"""
IngestionService
================
Orchestrates the full live research ingestion pipeline:

  Source Connectors
      ↓
  Fetch New Records
      ↓
  Normalize (handled by each connector)
      ↓
  Deduplicate (source_type + source_id)
      ↓
  Entity Extraction (ai_service + query-context hints)
      ↓
  Drug/Disease Matching (against DB records, case-insensitive)
      ↓
  Evidence Matching → attach to existing signal
      ↓
  Score Update (ai_service.calculate_evidence_score)
      ↓
  Novel Signal Detection (flag if no existing signal found)
      ↓
  Rescore ALL signals after run completes
      ↓
  Research Monitor record creation
      ↓
  Alert creation

KEY FIXES IN THIS VERSION:
  1. Query-context matching: the ingestion query is parsed into drug/disease
     hint terms; records whose connector already populated extracted_drugs /
     extracted_diseases (UniProt, ClinicalTrials) use those directly, while
     text-only records (bioRxiv, medRxiv) are also matched against the query
     terms, not just free-text entity extraction.  This ensures bioRxiv,
     medRxiv, and UniProt records reach the Evidence table.

  2. Post-run rescore: after all sources finish, every signal is rescored
     from its current evidence so stored scores stay in sync with actual data.

  3. Config: max_records_per_source now taken from settings; callers can
     pass custom query_terms for on-demand (drug + disease) searches.

IMPORTANT:
  - All evidence is research metadata only — not clinical recommendations.
  - No findings are invented or exaggerated.
  - Demo data remains untouched throughout.
  - If all sources fail, the service returns gracefully with status "failed".
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import List, Optional, Dict, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.alert import Alert
from app.models.disease import Disease
from app.models.drug import Drug
from app.models.evidence import Evidence
from app.models.ingestion_run import IngestionRun
from app.models.research_source import ResearchSource
from app.models.signal import RepurposingSignal
from app.models.user import User
from app.services.ai_service import ai_service
from app.services.connectors import (
    BioRxivConnector,
    ClinicalTrialsConnector,
    ElsevierConnector,
    EuropePMCConnector,
    MedRxivConnector,
    NormalizedRecord,
    PubMedConnector,
    UniProtConnector,
)

logger = logging.getLogger(__name__)


# ── Confidence thresholds ─────────────────────────────────────────────────────
def _score_to_confidence(score: float) -> str:
    if score >= 75:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


class IngestionService:
    """
    Stateless service — call run() with a DB session to execute a full pipeline run.
    All external I/O is async; DB writes are synchronous (SQLite-safe).
    """

    def _build_connectors(self) -> dict:
        timeout = settings.INGESTION_REQUEST_TIMEOUT
        return {
            "pubmed":         PubMedConnector(timeout=timeout),
            "biorxiv":        BioRxivConnector(timeout=timeout),
            "medrxiv":        MedRxivConnector(timeout=timeout),
            "clinicaltrials": ClinicalTrialsConnector(timeout=timeout),
            "elsevier":       ElsevierConnector(timeout=timeout),
            "europepmc":      EuropePMCConnector(timeout=timeout),
            "uniprot":        UniProtConnector(timeout=timeout),
        }

    # ── Public entry point ────────────────────────────────────────────────────

    async def run(
        self,
        db: Session,
        query_terms: Optional[List[str]] = None,
    ) -> IngestionRun:
        """
        Execute a full ingestion run.

        query_terms: optional override — if provided, only these terms are
        searched (used for on-demand drug+disease queries from the UI).
        Falls back to settings.query_terms_list when None.

        Returns an IngestionRun with full results.
        Never raises — all errors are captured in the run record.
        """
        run = IngestionRun(status="running")
        db.add(run)
        db.commit()
        db.refresh(run)

        effective_queries = query_terms if query_terms is not None else settings.query_terms_list

        try:
            source_results = await self._run_all_sources(db, run.id, effective_queries)
            # Rescore ALL signals so stored scores reflect current evidence
            self._rescore_all_signals(db)
            self._finish_run(db, run, source_results)
        except Exception as e:
            logger.exception("[Ingestion] unexpected error in run %d: %s", run.id, e)
            run.status      = "failed"
            run.error       = str(e)
            run.summary     = "Ingestion run failed with an unexpected error."
            run.finished_at = datetime.now(timezone.utc)
            db.commit()

        return run

    # ── Source orchestration ──────────────────────────────────────────────────

    async def _run_all_sources(
        self,
        db: Session,
        run_id: int,
        queries: List[str],
    ) -> List[dict]:
        """Run all enabled sources concurrently (with per-source error isolation)."""
        enabled    = settings.enabled_sources_list
        max_recs   = settings.INGESTION_MAX_RECORDS_PER_SOURCE
        connectors = self._build_connectors()

        tasks = []
        for source_name in enabled:
            connector = connectors.get(source_name)
            if connector is None:
                continue
            for query in queries:
                tasks.append(
                    self._run_single_source(db, connector, source_name, query, max_recs)
                )

        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge per-source results across all queries
        merged: Dict[str, dict] = {}
        for res in raw_results:
            if isinstance(res, Exception):
                logger.warning("[Ingestion] source task raised: %s", res)
                continue
            sname = res["source"]
            if sname not in merged:
                merged[sname] = {
                    "source":             sname,
                    "status":             res["status"],
                    "records_fetched":    0,
                    "records_new":        0,
                    "records_duplicate":  0,
                    "records_matched":    0,
                    "records_novel":      0,
                    "errors":             [],
                    "elapsed_seconds":    0.0,
                }
            m = merged[sname]
            m["records_fetched"]   += res.get("records_fetched",   0)
            m["records_new"]       += res.get("records_new",       0)
            m["records_duplicate"] += res.get("records_duplicate", 0)
            m["records_matched"]   += res.get("records_matched",   0)
            m["records_novel"]     += res.get("records_novel",     0)
            m["elapsed_seconds"]   += res.get("elapsed_seconds",   0.0)
            if res.get("error"):
                m["errors"].append(res["error"])
            # Keep worst-case status ranking
            status_rank = {
                "connected": 3, "empty": 2, "error": 1,
                "timeout": 1, "rate_limited": 1, "disabled": 0,
            }
            if status_rank.get(res["status"], 0) > status_rank.get(m["status"], 0):
                m["status"] = res["status"]

        return list(merged.values())

    async def _run_single_source(
        self,
        db: Session,
        connector,
        source_name: str,
        query: str,
        max_recs: int,
    ) -> dict:
        t0 = time.monotonic()
        result = {
            "source":             source_name,
            "status":             "error",
            "records_fetched":    0,
            "records_new":        0,
            "records_duplicate":  0,
            "records_matched":    0,
            "records_novel":      0,
            "elapsed_seconds":    0.0,
            "error":              None,
        }

        if hasattr(connector, "_is_configured") and not connector._is_configured:
            result["status"] = "disabled"
            return result

        try:
            records = await connector.fetch(query=query, max_records=max_recs)
            result["records_fetched"] = len(records)

            if not records:
                result["status"] = "empty"
                return result

            result["status"] = "connected"
            # Parse query hints once for the whole batch
            drug_hints, disease_hints = _parse_query_for_hints(query)

            for rec in records:
                outcome = self._process_record(db, rec, drug_hints, disease_hints)
                if outcome == "duplicate":
                    result["records_duplicate"] += 1
                elif outcome == "new_matched":
                    result["records_new"]     += 1
                    result["records_matched"] += 1
                elif outcome == "new_novel":
                    result["records_new"]   += 1
                    result["records_novel"] += 1
                elif outcome == "new_unmatched":
                    result["records_new"] += 1

        except Exception as e:
            logger.warning("[Ingestion:%s] error for query %r: %s", source_name, query, e)
            result["status"] = "error"
            result["error"]  = str(e)
        finally:
            result["elapsed_seconds"] = round(time.monotonic() - t0, 2)

        return result

    # ── Per-record processing ─────────────────────────────────────────────────

    def _process_record(
        self,
        db: Session,
        rec: NormalizedRecord,
        drug_hints: Optional[List[str]] = None,
        disease_hints: Optional[List[str]] = None,
    ) -> str:
        """
        Process one normalised record through the full pipeline.
        Returns: "duplicate" | "new_matched" | "new_novel" | "new_unmatched"

        KEY FIX: entity matching now uses BOTH:
          a) AI/heuristic entity extraction from title+abstract text
          b) Query-context hints (drug_hints, disease_hints) from the
             ingestion query string
          c) Pre-populated extracted_drugs / extracted_diseases already on
             the record (from connectors like UniProt and ClinicalTrials)
        """
        # 1. Deduplication
        if self._is_duplicate(db, rec):
            return "duplicate"

        # 2. Entity extraction from text
        text     = f"{rec.title} {rec.abstract or ''}"
        entities = ai_service.extract_entities(text)

        # 3. Merge all entity sources: connector-provided + AI + query hints
        drugs = list(dict.fromkeys(
            rec.extracted_drugs
            + entities.get("drugs", [])
            + (drug_hints or [])
        ))
        diseases = list(dict.fromkeys(
            rec.extracted_diseases
            + entities.get("diseases", [])
            + (disease_hints or [])
        ))
        mechs = list(dict.fromkeys(
            rec.extracted_mechanisms
            + entities.get("mechanisms", [])
        ))

        # 4. DB-level entity matching (case-insensitive, partial)
        matched_drugs    = self._match_drugs(db, drugs)
        matched_diseases = self._match_diseases(db, diseases)

        # 5. Persist the research source record
        source_row = self._save_source(db, rec, matched_drugs, matched_diseases, mechs)

        # 6. Signal matching + score update
        if matched_drugs and matched_diseases:
            return self._handle_signal_match(db, rec, source_row, matched_drugs, matched_diseases)

        return "new_unmatched"

    # ── Deduplication ─────────────────────────────────────────────────────────

    def _is_duplicate(self, db: Session, rec: NormalizedRecord) -> bool:
        return db.query(ResearchSource).filter(
            ResearchSource.source_type == rec.source,
            ResearchSource.source_id   == rec.source_id,
        ).first() is not None

    # ── Entity matching ───────────────────────────────────────────────────────

    def _match_drugs(self, db: Session, names: List[str]) -> List[Drug]:
        matched: List[Drug] = []
        seen_ids = set()
        for name in names:
            if not name or len(name) < 3:
                continue
            drug = db.query(Drug).filter(Drug.name.ilike(f"%{name}%")).first()
            if drug and drug.id not in seen_ids:
                matched.append(drug)
                seen_ids.add(drug.id)
        return matched

    def _match_diseases(self, db: Session, names: List[str]) -> List[Disease]:
        matched: List[Disease] = []
        seen_ids = set()
        for name in names:
            if not name or len(name) < 3:
                continue
            disease = db.query(Disease).filter(Disease.name.ilike(f"%{name}%")).first()
            if disease and disease.id not in seen_ids:
                matched.append(disease)
                seen_ids.add(disease.id)
        return matched

    # ── Persist research source ───────────────────────────────────────────────

    def _save_source(
        self,
        db: Session,
        rec: NormalizedRecord,
        matched_drugs: List[Drug],
        matched_diseases: List[Disease],
        mechs: List[str],
    ) -> ResearchSource:
        row = ResearchSource(
            source_type=rec.source,
            source_id=rec.source_id,
            title=rec.title,
            abstract=rec.abstract,
            authors=rec.authors,
            publication_date=rec.publication_date,
            journal=rec.journal,
            doi=rec.doi,
            pmid=rec.pmid,
            nct_id=rec.nct_id,
            source_url=rec.source_url,
            extracted_drugs=[d.name for d in matched_drugs] or rec.extracted_drugs,
            extracted_diseases=[d.name for d in matched_diseases] or rec.extracted_diseases,
            extracted_mechanisms=mechs,
            is_processed=True,
            is_demo_data=False,
        )
        try:
            db.add(row)
            db.commit()
            db.refresh(row)
        except IntegrityError:
            db.rollback()
            row = db.query(ResearchSource).filter(
                ResearchSource.source_type == rec.source,
                ResearchSource.source_id   == rec.source_id,
            ).first()
        return row

    # ── Signal matching ───────────────────────────────────────────────────────

    def _handle_signal_match(
        self,
        db: Session,
        rec: NormalizedRecord,
        source_row: ResearchSource,
        drugs: List[Drug],
        diseases: List[Disease],
    ) -> str:
        for drug in drugs:
            for disease in diseases:
                signal = db.query(RepurposingSignal).filter(
                    RepurposingSignal.drug_id    == drug.id,
                    RepurposingSignal.disease_id == disease.id,
                ).first()

                if signal:
                    self._attach_evidence(db, rec, signal)
                    return "new_matched"
                else:
                    self._flag_novel_signal(db, rec, source_row, drug, disease)
                    return "new_novel"

        return "new_unmatched"

    def _attach_evidence(
        self,
        db: Session,
        rec: NormalizedRecord,
        signal: RepurposingSignal,
    ) -> None:
        """Attach new evidence to existing signal. Score update happens in _rescore_all_signals."""
        ev = Evidence(
            signal_id=signal.id,
            evidence_type=rec.evidence_type,
            title=rec.title,
            authors=rec.authors,
            abstract=rec.abstract,
            summary=None,
            publication_date=rec.publication_date,
            journal=rec.journal,
            source_name=rec.source,
            source_url=rec.source_url,
            doi=rec.doi,
            pmid=rec.pmid,
            pmcid=getattr(rec, "pmcid", None),
            nct_id=rec.nct_id,
            relevance_score=0.7,
            relevance_explanation=(
                f"Ingested from {rec.source} — matched to signal "
                f"'{signal.drug.name if signal.drug else '?'} → "
                f"{signal.disease.name if signal.disease else '?'}'."
            ),
            supports_mechanism=(rec.evidence_type in ("research_paper", "preprint", "protein_annotation")),
            is_demo_data=False,
            data_source=rec.source,
        )
        db.add(ev)
        # Mark signal as live if it was previously demo-only
        if signal.data_source == "demo":
            signal.data_source = "live"
        db.commit()

    # ── Post-run rescore ALL signals ──────────────────────────────────────────

    def _rescore_all_signals(self, db: Session) -> None:
        """
        Rescore every active signal from its current evidence set.
        This keeps stored scores in sync with actual ingested evidence
        and removes the staleness problem identified in the audit.
        """
        from sqlalchemy.orm import joinedload
        signals = (
            db.query(RepurposingSignal)
            .options(
                joinedload(RepurposingSignal.drug),
                joinedload(RepurposingSignal.disease),
                joinedload(RepurposingSignal.evidence_items),
            )
            .filter(RepurposingSignal.status == "active")
            .all()
        )

        for signal in signals:
            evidence_dicts = [
                {
                    "evidence_type":    e.evidence_type,
                    "publication_date": e.publication_date or "",
                    "data_source":      e.data_source or "unknown",
                    "doi":              e.doi,
                    "pmid":             e.pmid,
                    "is_demo_data":     e.is_demo_data,
                }
                for e in (signal.evidence_items or [])
            ]
            drug_targets    = signal.drug.molecular_targets    if signal.drug    else []
            disease_paths   = signal.disease.affected_pathways if signal.disease else []
            mechanism_overlap = self._compute_overlap(drug_targets, disease_paths)

            score_data = ai_service.calculate_evidence_score(
                drug_name=signal.drug.name    if signal.drug    else "",
                disease_name=signal.disease.name if signal.disease else "",
                evidence_items=evidence_dicts,
                mechanism_overlap=mechanism_overlap,
                drug_targets=drug_targets,
                disease_pathways=disease_paths,
            )
            new_score = min(float(score_data["total"]["score"]), 100.0)
            live_count = sum(1 for e in (signal.evidence_items or []) if not e.is_demo_data)

            signal.evidence_score   = new_score
            signal.source_count     = len(evidence_dicts)
            signal.confidence_level = _score_to_confidence(new_score)
            # Mark as live if there is any live evidence
            if live_count > 0:
                signal.data_source = "live"

        db.commit()
        logger.info("[Ingestion] Rescored %d signals after run.", len(signals))

    # ── Novel signal detection ────────────────────────────────────────────────

    def _flag_novel_signal(
        self,
        db: Session,
        rec: NormalizedRecord,
        source_row: ResearchSource,
        drug: Drug,
        disease: Disease,
    ) -> None:
        existing = db.query(RepurposingSignal).filter(
            RepurposingSignal.drug_id    == drug.id,
            RepurposingSignal.disease_id == disease.id,
        ).first()
        if existing:
            self._attach_evidence(db, rec, existing)
            return

        drug_targets  = drug.molecular_targets    or []
        disease_paths = disease.affected_pathways or []
        overlap       = self._compute_overlap(drug_targets, disease_paths)

        evidence_dicts = [{
            "evidence_type":    rec.evidence_type,
            "publication_date": rec.publication_date or "",
        }]
        score_data = ai_service.calculate_evidence_score(
            drug_name=drug.name,
            disease_name=disease.name,
            evidence_items=evidence_dicts,
            mechanism_overlap=overlap,
            drug_targets=drug_targets,
            disease_pathways=disease_paths,
        )
        initial_score = min(float(score_data["total"]["score"]), 100.0)

        signal = RepurposingSignal(
            drug_id=drug.id,
            disease_id=disease.id,
            title=(
                f"[Potential Novel Signal] {drug.name} — {disease.name}: "
                f"association detected via live research ingestion"
            ),
            summary=(
                f"[LIVE — Potential Novel Research Signal] "
                f"BioArbitrage detected a co-occurrence of {drug.name} and {disease.name} "
                f"in a newly ingested research record from {rec.source}. "
                f"This is a preliminary research signal flagged by automated entity matching. "
                f"Expert validation required. NOT a clinical recommendation."
            ),
            biological_mechanism=(
                f"Mechanistic basis not yet established from single record. "
                f"Drug targets: {', '.join(drug_targets[:3]) or 'see drug profile'}. "
                f"Disease pathways: {', '.join(disease_paths[:3]) or 'see disease profile'}."
            ),
            evidence_score=initial_score,
            confidence_level=_score_to_confidence(initial_score),
            source_count=1,
            score_breakdown=score_data,
            status="active",
            is_novel=True,
            data_source="live",
            explanation_factors=[{
                "factor": "Live Ingestion Detection",
                "detail": (
                    f"Co-occurrence of {drug.name} and {disease.name} detected "
                    f"in record ingested from {rec.source}."
                ),
                "strength": "weak",
            }],
        )
        db.add(signal)
        db.flush()

        ev = Evidence(
            signal_id=signal.id,
            evidence_type=rec.evidence_type,
            title=rec.title,
            authors=rec.authors,
            abstract=rec.abstract,
            publication_date=rec.publication_date,
            journal=rec.journal,
            source_name=rec.source,
            source_url=rec.source_url,
            doi=rec.doi,
            pmid=rec.pmid,
            pmcid=getattr(rec, "pmcid", None),
            nct_id=rec.nct_id,
            relevance_score=0.5,
            relevance_explanation=f"Triggering evidence for novel signal detection from {rec.source}.",
            is_demo_data=False,
            data_source=rec.source,
        )
        db.add(ev)
        db.commit()

        self._create_alerts(
            db=db,
            alert_type="new_signal",
            entity_type="drug",
            entity_id=drug.id,
            entity_name=drug.name,
            title=f"Potential novel signal detected: {drug.name} → {disease.name}",
            message=(
                f"[Potential Novel Research Signal — Requires Expert Validation] "
                f"Live ingestion from {rec.source} detected a research association between "
                f"{drug.name} and {disease.name}. Initial score: {initial_score:.0f}/100. "
                f"NOT a confirmed finding or clinical recommendation."
            ),
        )

    # ── Alert creation ────────────────────────────────────────────────────────

    def _create_alerts(
        self,
        db: Session,
        alert_type: str,
        entity_type: str,
        entity_id: int,
        entity_name: str,
        title: str,
        message: str,
    ) -> None:
        researchers = db.query(User).filter(User.is_active == True).all()
        for user in researchers:
            alert = Alert(
                user_id=user.id,
                alert_type=alert_type,
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=entity_name,
                title=title,
                message=message,
                is_read=False,
                is_dismissed=False,
            )
            db.add(alert)
        db.commit()

    # ── Score helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _compute_overlap(drug_targets: List[str], disease_pathways: List[str]) -> float:
        if not drug_targets or not disease_pathways:
            return 0.0
        t_words = set(" ".join(drug_targets).lower().split())
        p_words = set(" ".join(disease_pathways).lower().split())
        shared  = t_words & p_words
        return min(len(shared) / max(len(t_words), 1), 1.0)

    # ── Finalise run ──────────────────────────────────────────────────────────

    def _finish_run(
        self,
        db: Session,
        run: IngestionRun,
        source_results: List[dict],
    ) -> None:
        total_fetched    = sum(r["records_fetched"]   for r in source_results)
        total_new        = sum(r["records_new"]       for r in source_results)
        total_duplicates = sum(r["records_duplicate"] for r in source_results)
        total_matched    = sum(r["records_matched"]   for r in source_results)
        total_novel      = sum(r["records_novel"]     for r in source_results)
        any_error  = any(r["status"] == "error"   for r in source_results)
        all_error  = all(r["status"] in ("error", "disabled") for r in source_results)

        run.source_results   = source_results
        run.total_fetched    = total_fetched
        run.total_new        = total_new
        run.total_duplicates = total_duplicates
        run.total_errors     = sum(1 for r in source_results if r["status"] == "error")
        run.signals_updated  = total_matched
        run.signals_created  = total_novel
        run.finished_at      = datetime.now(timezone.utc)

        if all_error:
            run.status  = "failed"
            run.summary = (
                "All sources failed. Demo data is still available. "
                "Check network connectivity or source availability."
            )
        elif any_error:
            run.status  = "partial"
            run.summary = (
                f"Partial success: {total_new} new records from "
                f"{sum(1 for r in source_results if r['status'] == 'connected')} source(s). "
                f"{run.total_errors} source(s) failed."
            )
        elif total_new == 0:
            run.status  = "complete"
            run.summary = (
                f"Run complete. No new records found — {total_duplicates} duplicate(s) skipped. "
                "All sources responded successfully."
            )
        else:
            run.status  = "complete"
            run.summary = (
                f"Run complete: {total_new} new records ingested, "
                f"{total_duplicates} duplicate(s) skipped, "
                f"{total_matched} signal(s) updated, "
                f"{total_novel} novel signal(s) flagged."
            )

        db.commit()

    # ── Source connection check ───────────────────────────────────────────────

    async def check_sources(self) -> List[dict]:
        """Check connectivity for all configured sources. Used by Settings page."""
        connectors = self._build_connectors()
        results = []
        for name, connector in connectors.items():
            enabled = name in settings.enabled_sources_list
            if not enabled:
                results.append({"source": name, "status": "disabled", "enabled": False})
                continue

            if name == "elsevier":
                if not getattr(connector, "_is_configured", True):
                    results.append({
                        "source":  name,
                        "status":  "not_configured",
                        "enabled": False,
                        "error": (
                            "ELSEVIER_API_KEY not set in backend/.env. "
                            "Add your key and restart the backend."
                        ),
                    })
                else:
                    try:
                        detail = await asyncio.wait_for(
                            connector.check_connection_detail(),
                            timeout=settings.INGESTION_REQUEST_TIMEOUT,
                        )
                        reason = detail.get("reason", "error")
                        status_map = {
                            "connected":      "connected",
                            "invalid_key":    "invalid_key",
                            "rate_limited":   "rate_limited",
                            "timeout":        "timeout",
                            "not_configured": "not_configured",
                        }
                        ui_status = status_map.get(reason, "error")
                        error_msg = None
                        if reason == "invalid_key":
                            error_msg = (
                                f"API returned HTTP {detail.get('status_code')}. "
                                "Key may be invalid or missing entitlement."
                            )
                        elif reason == "rate_limited":
                            error_msg = "Rate limited (HTTP 429). Try again shortly."
                        elif reason not in ("connected", "not_configured"):
                            error_msg = f"API error: {reason}"
                        results.append({
                            "source":  name,
                            "status":  ui_status,
                            "enabled": detail.get("ok", False),
                            **({"error": error_msg} if error_msg else {}),
                        })
                    except asyncio.TimeoutError:
                        results.append({
                            "source": name, "status": "timeout", "enabled": False,
                            "error": "Connection timed out.",
                        })
                    except Exception as e:
                        results.append({
                            "source": name, "status": "error", "enabled": False,
                            "error": str(e),
                        })
                continue

            try:
                ok = await asyncio.wait_for(
                    connector.check_connection(),
                    timeout=settings.INGESTION_REQUEST_TIMEOUT,
                )
                results.append({
                    "source":  name,
                    "status":  "connected" if ok else "error",
                    "enabled": True,
                })
            except asyncio.TimeoutError:
                results.append({"source": name, "status": "timeout", "enabled": True})
            except Exception as e:
                results.append({
                    "source": name, "status": "error", "enabled": True, "error": str(e),
                })

        return results


# ── Query hint parsing ────────────────────────────────────────────────────────

def _parse_query_for_hints(query: str) -> Tuple[List[str], List[str]]:
    """
    Parse an ingestion query string into (drug_hints, disease_hints).

    Supports structured format: "drug:Metformin disease:Alzheimer's Disease"

    For unstructured queries like "metformin alzheimer" or "aspirin alzheimer":
    - Split into individual tokens (each word becomes its own hint).
    - Also include 2-word and 3-word combinations to catch multi-word drug/disease names.
    - The DB _match_drugs / _match_diseases use ilike('%hint%') so a single word
      like "metformin" will correctly match the Drug named "Metformin".

    Previously the whole string was used as a single hint, which caused ilike to
    look for a drug named "metformin alzheimer" — finding nothing.
    """
    drug_hints: List[str]    = []
    disease_hints: List[str] = []

    lower = query.lower()
    if "drug:" in lower or "disease:" in lower:
        tokens = query.split()
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.lower().startswith("drug:"):
                val = token[5:]
                while i + 1 < len(tokens) and not tokens[i + 1].lower().startswith(("drug:", "disease:")):
                    i += 1
                    val += " " + tokens[i]
                if val.strip():
                    drug_hints.append(val.strip())
            elif token.lower().startswith("disease:"):
                val = token[8:]
                while i + 1 < len(tokens) and not tokens[i + 1].lower().startswith(("drug:", "disease:")):
                    i += 1
                    val += " " + tokens[i]
                if val.strip():
                    disease_hints.append(val.strip())
            i += 1
        return drug_hints, disease_hints

    # Unstructured query: split into individual tokens.
    # Each token is tried as both a drug hint and a disease hint — the DB
    # ilike matcher handles the actual lookup. Short stop-words are excluded.
    stop_words = {
        "and", "or", "the", "of", "in", "for", "with", "a", "an",
        "drug", "disease", "therapy", "treatment", "mechanism",
        "pathway", "clinical", "trial", "repurposing", "aging",
        "research", "study", "evidence",
    }
    tokens = [t.strip().strip(".,;:'\"") for t in query.split() if len(t.strip()) >= 3]
    individual = [t for t in tokens if t.lower() not in stop_words]

    # Also include 2-word and 3-word combinations (for multi-word drug/disease names)
    combos: List[str] = list(individual)
    for length in (2, 3):
        for j in range(len(tokens) - length + 1):
            combo = " ".join(tokens[j: j + length])
            if combo not in combos:
                combos.append(combo)

    # Both lists get the same candidates — the matcher will only find
    # what actually exists in the Drug/Disease tables
    drug_hints    = list(dict.fromkeys(combos))  # dedup, preserve order
    disease_hints = list(dict.fromkeys(combos))

    return drug_hints, disease_hints


# Singleton
ingestion_service = IngestionService()
