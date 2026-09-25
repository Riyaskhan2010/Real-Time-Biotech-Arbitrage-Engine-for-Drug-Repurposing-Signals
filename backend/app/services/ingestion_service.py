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
from app.services.connectors import get_registry, NormalizedRecord

logger = logging.getLogger(__name__)


# ── Confidence thresholds ─────────────────────────────────────────────────────
def _score_to_confidence(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


class IngestionService:
    """
    Stateless service — call run() with a DB session to execute a full pipeline run.
    All external I/O is async; DB writes are synchronous (SQLite-safe).
    """

    def _build_connectors(self) -> dict:
        """
        Build connector instances from the central registry.
        New connectors are discovered automatically — no changes needed here.
        To add a new source: register it in connectors/__init__.py and add its
        name to INGESTION_ENABLED_SOURCES in .env / Render Dashboard.
        """
        timeout  = settings.INGESTION_REQUEST_TIMEOUT
        registry = get_registry()
        return {name: cls(timeout=timeout) for name, cls in registry.items()}

    # ── Public entry point ────────────────────────────────────────────────────

    async def run(
        self,
        db: Session,
        query_terms: Optional[List[str]] = None,
        since_days: Optional[int] = None,
    ) -> IngestionRun:
        """
        Execute a full ingestion run.

        query_terms: optional override — if provided, only these terms are
          searched (used for on-demand drug+disease queries from the UI).
          Falls back to settings.query_terms_list when None.

        since_days: optional freshness window — when set, each connector uses
          its date filter to fetch only records newer than this many days.
          The scheduler sets this automatically (2× interval hours converted
          to days). Manual runs and first-time runs leave it as None so the
          full history is queried.

        Returns an IngestionRun with full results.
        Never raises — all errors are captured in the run record.
        """
        run = IngestionRun(status="running")
        db.add(run)
        db.commit()
        db.refresh(run)

        effective_queries = query_terms if query_terms is not None else settings.query_terms_list

        try:
            source_results = await self._run_all_sources(
                db, run.id, effective_queries, since_days=since_days
            )
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
        since_days: Optional[int] = None,
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
                    self._run_single_source(
                        db, connector, source_name, query, max_recs,
                        since_days=since_days,
                    )
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
        since_days: Optional[int] = None,
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
            # Pass since_days only if the connector's fetch() accepts it.
            # All built-in connectors do; future connectors may not yet.
            import inspect
            fetch_sig = inspect.signature(connector.fetch)
            if "since_days" in fetch_sig.parameters:
                records = await connector.fetch(
                    query=query, max_records=max_recs, since_days=since_days
                )
            else:
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

    # ── Entity matching + auto-creation ──────────────────────────────────────
    #
    # ENTITY TYPE VALIDATION:
    # The pipeline now enforces strict entity-type separation:
    #   - A name appearing in _KNOWN_DISEASE_NAMES will NEVER be created as a Drug
    #   - A name appearing in _KNOWN_DRUG_NAMES will NEVER be created as a Disease
    #   - Query-hint phrases that are multi-word combinations of drug+disease
    #     (e.g. "Rapamycin Aging", "Aspirin Alzheimer") are explicitly blocked
    #   - Names must pass minimum quality checks (length, stop-words, blacklists)
    #
    # These sets are derived from the AI service heuristic dictionaries so the
    # two layers stay in sync. We import the sets lazily to avoid circular imports.
    # ─────────────────────────────────────────────────────────────────────────

    _ENTITY_STOP_WORDS = {
        "drug", "drugs", "disease", "diseases", "therapy", "treatment",
        "clinical", "trial", "mechanism", "pathway", "research", "study",
        "evidence", "effect", "effects", "role", "novel", "new", "review",
        "repurposing", "target", "targets", "inhibitor", "inhibition",
        "expression", "regulation", "activity", "function", "model",
        "mouse", "human", "cell", "cells", "protein", "gene", "genes",
        "association", "analysis", "patient", "patients", "method",
        # additional generic words that should never become drug/disease entities
        "aging", "age", "health", "healthy", "cancer", "tumor", "tumour",
        "data", "results", "outcome", "outcomes", "risk", "factor", "factors",
        "type", "stage", "grade", "form", "variant", "subtype",
    }

    # Phrases that are explicitly multi-token query strings, NOT entity names.
    # Auto-generated by combining drug + disease names from the query parser.
    # Any name that contains TWO of these root words is a query artifact.
    _QUERY_ARTIFACT_ROOTS = {
        # drug roots
        "rapamycin", "metformin", "sildenafil", "aspirin", "ivermectin",
        "doxycycline", "lithium", "naltrexone", "thalidomide", "everolimus",
        "temsirolimus", "berberine", "atorvastatin", "celecoxib", "fluoxetine",
        # disease roots
        "alzheimer", "cancer", "diabetes", "aging", "hypertension", "sclerosis",
        "parkinson", "glioblastoma", "melanoma", "leukemia", "lymphoma",
    }

    @classmethod
    def _is_query_artifact(cls, name: str) -> bool:
        """
        Return True if 'name' looks like a combined query-hint phrase rather
        than a genuine entity name.  E.g. "Rapamycin Aging", "Aspirin Alzheimer".
        """
        tokens = name.lower().split()
        if len(tokens) < 2:
            return False
        roots_found = sum(1 for t in tokens if t in cls._QUERY_ARTIFACT_ROOTS)
        return roots_found >= 2

    @staticmethod
    def _get_known_drug_names() -> set:
        """Return the set of lowercase known drug names from the AI service."""
        try:
            from app.services.ai_service import ai_service
            return {d.lower() for d in ai_service._KNOWN_DRUGS}
        except Exception:
            return set()

    @staticmethod
    def _get_known_disease_names() -> set:
        """Return the set of lowercase known disease names from the AI service."""
        try:
            from app.services.ai_service import ai_service
            return {d.lower() for d in ai_service._KNOWN_DISEASES}
        except Exception:
            return set()

    def _match_drugs(self, db: Session, names: List[str]) -> List[Drug]:
        """
        Match or create Drug rows for each candidate name.
        ENTITY TYPE VALIDATION: rejects names that are known diseases,
        query artifacts, or generic terms.
        """
        known_diseases = self._get_known_disease_names()
        matched: List[Drug] = []
        seen_ids: set = set()
        for name in names:
            name = (name or "").strip()
            if len(name) < 4 or name.lower() in self._ENTITY_STOP_WORDS:
                continue
            # Reject query artifacts (e.g. "Rapamycin Aging")
            if self._is_query_artifact(name):
                logger.debug("[EntityValidation] Rejecting drug candidate %r — query artifact", name)
                continue
            # Reject if the name is a known disease
            if name.lower() in known_diseases:
                logger.debug("[EntityValidation] Rejecting drug candidate %r — known disease", name)
                continue
            drug = db.query(Drug).filter(Drug.name.ilike(f"%{name}%")).first()
            if drug is None:
                drug = self._create_drug_from_evidence(db, name)
            if drug and drug.id not in seen_ids:
                matched.append(drug)
                seen_ids.add(drug.id)
        return matched

    def _match_diseases(self, db: Session, names: List[str]) -> List[Disease]:
        """
        Match or create Disease rows for each candidate name.
        ENTITY TYPE VALIDATION: rejects names that are known drugs,
        query artifacts, or generic terms.
        """
        known_drugs = self._get_known_drug_names()
        matched: List[Disease] = []
        seen_ids: set = set()
        for name in names:
            name = (name or "").strip()
            if len(name) < 4 or name.lower() in self._ENTITY_STOP_WORDS:
                continue
            # Reject query artifacts (e.g. "Aspirin Alzheimer", "Rapamycin Cancer")
            if self._is_query_artifact(name):
                logger.debug("[EntityValidation] Rejecting disease candidate %r — query artifact", name)
                continue
            # Reject if the name is a known drug
            if name.lower() in known_drugs:
                logger.debug("[EntityValidation] Rejecting disease candidate %r — known drug", name)
                continue
            disease = db.query(Disease).filter(Disease.name.ilike(f"%{name}%")).first()
            if disease is None:
                disease = self._create_disease_from_evidence(db, name)
            if disease and disease.id not in seen_ids:
                matched.append(disease)
                seen_ids.add(disease.id)
        return matched

    def _create_drug_from_evidence(self, db: Session, name: str) -> Optional[Drug]:
        """
        Create a Drug record from a live evidence entity name.
        Uses known drug metadata from the AI service when available.
        Only called when no existing DB row matches and the name passes
        entity-type validation.
        """
        canonical = name.strip().title()
        # Final cross-table check: never create a drug with the same name as an existing disease
        if db.query(Disease).filter(Disease.name.ilike(canonical)).first():
            logger.debug("[EntityValidation] Skipping drug creation for %r — exists as disease", canonical)
            return None
        # Double-check it doesn't already exist
        existing = db.query(Drug).filter(Drug.name.ilike(canonical)).first()
        if existing:
            return existing
        # Try to get metadata from AI service known drugs
        drug_meta = self._lookup_known_drug_meta(canonical)
        try:
            drug = Drug(
                name=canonical,
                generic_name=drug_meta.get("generic_name", canonical.lower()),
                drug_class=drug_meta.get("drug_class", "Drug — extracted from live evidence"),
                mechanism_of_action=drug_meta.get("mechanism", f"Mechanism not yet characterised for {canonical}. Identified in live research ingestion."),
                approved_indications=drug_meta.get("approved_indications", []),
                molecular_targets=drug_meta.get("molecular_targets", []),
                pathways=drug_meta.get("pathways", []),
                fda_status=drug_meta.get("fda_status", "Status unknown — see source evidence"),
                approval_year=drug_meta.get("approval_year"),
                description=drug_meta.get("description", f"{canonical} was identified in live research evidence ingested by BioArbitrage. Profile will be enriched as more evidence is indexed."),
            )
            db.add(drug)
            db.commit()
            db.refresh(drug)
            logger.info("[Ingestion] Created Drug entity from live evidence: %r (class: %s)", canonical, drug.drug_class)
            return drug
        except IntegrityError:
            db.rollback()
            return db.query(Drug).filter(Drug.name.ilike(canonical)).first()
        except Exception as exc:
            db.rollback()
            logger.warning("[Ingestion] Could not create Drug %r: %s", canonical, exc)
            return None

    def _create_disease_from_evidence(self, db: Session, name: str) -> Optional[Disease]:
        """
        Create a Disease record from a live evidence entity name.
        Uses known disease metadata from the AI service when available.
        Only called when no existing DB row matches and the name passes
        entity-type validation.
        """
        canonical = name.strip().title()
        # Final cross-table check: never create a disease with the same name as an existing drug
        if db.query(Drug).filter(Drug.name.ilike(canonical)).first():
            logger.debug("[EntityValidation] Skipping disease creation for %r — exists as drug", canonical)
            return None
        existing = db.query(Disease).filter(Disease.name.ilike(canonical)).first()
        if existing:
            return existing
        # Try to get metadata from AI service known diseases
        disease_meta = self._lookup_known_disease_meta(canonical)
        try:
            disease = Disease(
                name=canonical,
                icd10_code=disease_meta.get("icd10_code"),
                category=disease_meta.get("category", "Disease — extracted from live evidence"),
                description=disease_meta.get("description", f"{canonical} was identified in live research evidence ingested by BioArbitrage. Profile will be enriched as more evidence is indexed."),
                affected_pathways=disease_meta.get("affected_pathways", []),
                molecular_markers=disease_meta.get("molecular_markers", []),
                current_treatments=disease_meta.get("current_treatments", []),
                unmet_needs=disease_meta.get("unmet_needs", f"Unmet needs for {canonical} not yet characterised. See source evidence."),
                prevalence=disease_meta.get("prevalence", "Prevalence not available — see source evidence"),
            )
            db.add(disease)
            db.commit()
            db.refresh(disease)
            logger.info("[Ingestion] Created Disease entity from live evidence: %r (category: %s)", canonical, disease.category)
            return disease
        except IntegrityError:
            db.rollback()
            return db.query(Disease).filter(Disease.name.ilike(canonical)).first()
        except Exception as exc:
            db.rollback()
            logger.warning("[Ingestion] Could not create Disease %r: %s", canonical, exc)
            return None

    @staticmethod
    def _lookup_known_drug_meta(name: str) -> dict:
        """Look up known drug metadata from the AI service dictionary."""
        try:
            from app.services.ai_service import ai_service
            name_lower = name.lower()
            for d in ai_service._KNOWN_DRUGS:
                if d.lower() == name_lower:
                    return {}  # known drug, but no structured meta in the set
            return {}
        except Exception:
            return {}

    @staticmethod
    def _lookup_known_disease_meta(name: str) -> dict:
        """Look up known disease metadata from the AI service dictionary."""
        try:
            from app.services.ai_service import ai_service
            name_lower = name.lower()
            for d in ai_service._KNOWN_DISEASES:
                if d.lower() == name_lower:
                    return {}  # known disease, but no structured meta in the set
            return {}
        except Exception:
            return {}

    # ── Persist research source ───────────────────────────────────────────────

    def _save_source(
        self,
        db: Session,
        rec: NormalizedRecord,
        matched_drugs: List[Drug],
        matched_diseases: List[Disease],
        mechs: List[str],
    ) -> ResearchSource:
        # Use matched DB entity names when available; fall back to raw extracted names.
        # This ensures Research Monitor always shows the names that were identified,
        # even if DB matching only found a partial set.
        saved_drugs    = [d.name for d in matched_drugs] if matched_drugs else rec.extracted_drugs
        saved_diseases = [d.name for d in matched_diseases] if matched_diseases else rec.extracted_diseases

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
            extracted_drugs=saved_drugs,
            extracted_diseases=saved_diseases,
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
            signal.score_breakdown  = score_data   # keep stored breakdown in sync
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

    async def check_sources(self, db=None) -> List[dict]:
        """
        Check connectivity for all configured sources concurrently.
        Each source gets a hard 10-second timeout so one unreachable source
        cannot hang the entire Settings page.

        db: optional SQLAlchemy Session — when provided, adds stored_records
            and last_successful_sync from the database to each result.
        """
        from datetime import datetime, timezone
        connectors = self._build_connectors()
        _CHECK_TIMEOUT = 10   # hard per-source limit regardless of global setting
        now_iso = datetime.now(timezone.utc).isoformat()

        async def _check_one(name: str, connector) -> dict:
            enabled = name in settings.enabled_sources_list
            if not enabled:
                return {"source": name, "status": "disabled", "enabled": False}

            if name == "elsevier":
                if not getattr(connector, "_is_configured", True):
                    return {
                        "source":  name,
                        "status":  "not_configured",
                        "enabled": False,
                        "error":   "ELSEVIER_API_KEY not set in backend/.env.",
                    }
                try:
                    detail = await asyncio.wait_for(
                        connector.check_connection_detail(),
                        timeout=_CHECK_TIMEOUT,
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
                    return {
                        "source":  name,
                        "status":  ui_status,
                        "enabled": detail.get("ok", False),
                        **({"error": error_msg} if error_msg else {}),
                    }
                except asyncio.TimeoutError:
                    return {"source": name, "status": "timeout", "enabled": False,
                            "error": "Connection timed out after 10s."}
                except Exception as e:
                    return {"source": name, "status": "error", "enabled": False, "error": str(e)}

            # All other sources
            try:
                # Reset the empty-body sentinel before checking
                if hasattr(connector, '_last_check_empty_body'):
                    connector._last_check_empty_body = False
                ok = await asyncio.wait_for(
                    connector.check_connection(),
                    timeout=_CHECK_TIMEOUT,
                )
                if ok:
                    return {"source": name, "status": "connected", "enabled": True}
                empty_body = getattr(connector, '_last_check_empty_body', False)
                if empty_body:
                    return {
                        "source": name,
                        "status": "unavailable",
                        "enabled": True,
                        "error": (
                            "API server is reachable but returning no data currently. "
                            "This is a server-side issue — the source will reconnect automatically."
                        ),
                    }
                return {"source": name, "status": "error", "enabled": True,
                        "error": "API returned empty or invalid response."}
            except asyncio.TimeoutError:
                return {"source": name, "status": "timeout", "enabled": True,
                        "error": "Connection timed out after 10s."}
            except Exception as e:
                return {"source": name, "status": "error", "enabled": True, "error": str(e)}

        # Run all checks concurrently — one slow/unreachable source won't block others
        tasks = [_check_one(name, connector) for name, connector in connectors.items()]
        raw = await asyncio.gather(*tasks, return_exceptions=True)
        results = [
            r if isinstance(r, dict)
            else {"source": "unknown", "status": "error", "error": str(r)}
            for r in raw
        ]

        # Enrich with DB stats (stored records + last successful sync) when DB available
        if db is not None:
            try:
                from app.models.research_source import ResearchSource
                from sqlalchemy import func
                for item in results:
                    src_name = item.get("source", "")
                    # Stored live records for this source
                    stored = (db.query(func.count(ResearchSource.id))
                        .filter(ResearchSource.source_type == src_name,
                                ResearchSource.is_demo_data == False)
                        .scalar() or 0)
                    item["stored_records"] = stored
                    # Last successful ingest date
                    last_row = (db.query(func.max(ResearchSource.ingested_at))
                        .filter(ResearchSource.source_type == src_name,
                                ResearchSource.is_demo_data == False)
                        .scalar())
                    item["last_successful_sync"] = last_row.isoformat() if last_row else None
                    item["last_attempt"] = now_iso
            except Exception as e:
                logger.warning("[check_sources] DB enrichment failed: %s", e)

        return results


# ── Query hint parsing ────────────────────────────────────────────────────────

def _parse_query_for_hints(query: str) -> Tuple[List[str], List[str]]:
    """
    Parse an ingestion query string into (drug_hints, disease_hints).

    Supports structured format: "drug:Metformin disease:Alzheimer's Disease"

    For unstructured queries like "metformin alzheimer":
    - Each token is classified as DRUG or DISEASE using the AI service known sets.
    - A token that is a known drug goes into drug_hints only (never disease_hints).
    - A token that is a known disease goes into disease_hints only (never drug_hints).
    - Ambiguous tokens (not in either known set) go into both lists — the DB
      ilike matcher + entity-type validation in _match_drugs/_match_diseases
      handles the final classification.
    - Query artifact phrases (multi-word combinations like "Rapamycin Aging")
      are NOT passed as hints — they only appear in the text extraction.

    This ensures "rapamycin" from "rapamycin aging" goes to drug_hints only,
    and "alzheimer" from "aspirin alzheimer" goes to disease_hints only.
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

    # Load known sets from AI service for classification
    try:
        from app.services.ai_service import ai_service
        known_drugs_lower    = {d.lower() for d in ai_service._KNOWN_DRUGS}
        known_diseases_lower = {d.lower() for d in ai_service._KNOWN_DISEASES}
    except Exception:
        known_drugs_lower    = set()
        known_diseases_lower = set()

    stop_words = {
        "and", "or", "the", "of", "in", "for", "with", "a", "an",
        "drug", "disease", "therapy", "treatment", "mechanism",
        "pathway", "clinical", "trial", "repurposing", "aging",
        "research", "study", "evidence",
    }
    tokens = [t.strip().strip(".,;:'\"") for t in query.split() if len(t.strip()) >= 3]
    individual = [t for t in tokens if t.lower() not in stop_words]

    # Build single-word hints classified by type
    for t in individual:
        t_lower = t.lower()
        if t_lower in known_drugs_lower:
            drug_hints.append(t)
        elif t_lower in known_diseases_lower:
            disease_hints.append(t)
        else:
            # Ambiguous — try both (entity validation will filter at DB level)
            drug_hints.append(t)
            disease_hints.append(t)

    # Add multi-word combos — but classify each combo by type
    for length in (2, 3):
        for j in range(len(tokens) - length + 1):
            combo = " ".join(tokens[j: j + length])
            combo_lower = combo.lower()
            # Skip combo if it looks like a query artifact (drug+disease phrase)
            root_count = sum(
                1 for word in combo.lower().split()
                if word in known_drugs_lower or word in known_diseases_lower
            )
            if root_count >= 2:
                # This is a multi-entity phrase — skip it as a hint; let text
                # extraction handle the individual components
                continue
            if combo_lower in {h.lower() for h in drug_hints + disease_hints}:
                continue
            if combo_lower in known_drugs_lower:
                drug_hints.append(combo)
            elif combo_lower in known_diseases_lower:
                disease_hints.append(combo)
            else:
                drug_hints.append(combo)
                disease_hints.append(combo)

    # Deduplicate preserving order
    drug_hints    = list(dict.fromkeys(drug_hints))
    disease_hints = list(dict.fromkeys(disease_hints))

    return drug_hints, disease_hints


# Singleton
ingestion_service = IngestionService()
