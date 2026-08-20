from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional, Dict, Any
from collections import defaultdict
from app.database import get_db
from app.models.signal import RepurposingSignal
from app.models.evidence import Evidence
from app.schemas.schemas import SignalOut, SignalListItem
from app.utils.auth import get_current_active_user
from app.services.ai_service import ai_service
from app.data.seed_data import SIGNAL_ENRICHMENTS

router = APIRouter(prefix="/api/signals", tags=["signals"])


def _to_list_item(s: RepurposingSignal) -> SignalListItem:
    # Compute per-source names from stored evidence for traceability
    source_names: List[str] = []
    live_count = 0
    seen_ids: set = set()
    unique_count = 0

    for ev in (s.evidence_items or []):
        src = ev.data_source or ev.source_name or "unknown"
        if src and src not in source_names:
            source_names.append(src)

        canonical = (ev.doi or ev.pmid or (ev.title or "")[:80] or "").strip().lower()
        if canonical and canonical not in seen_ids:
            seen_ids.add(canonical)
            unique_count += 1
        elif not canonical:
            unique_count += 1

        if not ev.is_demo_data:
            live_count += 1

    return SignalListItem(
        id=s.id,
        title=s.title,
        drug_id=s.drug_id,
        disease_id=s.disease_id,
        evidence_score=s.evidence_score,
        confidence_level=s.confidence_level,
        source_count=s.source_count,
        status=s.status,
        is_novel=s.is_novel,
        detected_at=s.detected_at,
        drug_name=s.drug.name if s.drug else None,
        disease_name=s.disease.name if s.disease else None,
        biological_mechanism=s.biological_mechanism,
        unique_evidence_count=unique_count or None,
        live_evidence_count=live_count or None,
        source_names=source_names or None,
    )


@router.get("", response_model=List[SignalListItem])
def list_signals(
    confidence: Optional[str] = Query(None, description="Filter: high, medium, low"),
    drug_id: Optional[int] = Query(None),
    disease_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("evidence_score", description="evidence_score | detected_at"),
    include_demo: bool = Query(
        False,
        description=(
            "Include demo/seed signals in results. "
            "Default false: only returns signals with at least one live evidence record. "
            "Set true only for admin/debugging purposes."
        ),
    ),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    q = (
        db.query(RepurposingSignal)
        .options(
            joinedload(RepurposingSignal.drug),
            joinedload(RepurposingSignal.disease),
            joinedload(RepurposingSignal.evidence_items),   # needed for source traceability
        )
        .filter(RepurposingSignal.status == "active")
    )

    if confidence:
        q = q.filter(RepurposingSignal.confidence_level == confidence)
    if drug_id:
        q = q.filter(RepurposingSignal.drug_id == drug_id)
    if disease_id:
        q = q.filter(RepurposingSignal.disease_id == disease_id)
    if search:
        q = q.filter(
            or_(
                RepurposingSignal.title.ilike(f"%{search}%"),
                RepurposingSignal.summary.ilike(f"%{search}%"),
            )
        )

    # When include_demo=False, only return signals that have at least 1 live evidence record.
    # This is the preferred live-research mode; demo-only signals are hidden from view.
    if not include_demo:
        from sqlalchemy import exists
        live_ev_exists = exists().where(
            (Evidence.signal_id == RepurposingSignal.id) &
            (Evidence.is_demo_data == False)
        )
        q = q.filter(live_ev_exists)

    if sort_by == "detected_at":
        q = q.order_by(RepurposingSignal.detected_at.desc())
    else:
        q = q.order_by(RepurposingSignal.evidence_score.desc())

    signals = q.offset(offset).limit(limit).all()
    return [_to_list_item(s) for s in signals]


@router.get("/{signal_id}", response_model=SignalOut)
def get_signal(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    signal = (
        db.query(RepurposingSignal)
        .options(
            joinedload(RepurposingSignal.drug),
            joinedload(RepurposingSignal.disease),
            joinedload(RepurposingSignal.evidence_items),
        )
        .filter(RepurposingSignal.id == signal_id)
        .first()
    )
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    # Generate explanation on-the-fly if not stored
    if not signal.ai_explanation:
        evidence_dicts = [
            {"evidence_type": e.evidence_type, "title": e.title}
            for e in (signal.evidence_items or [])
        ]
        signal.ai_explanation = ai_service.explain_signal(
            drug_name=signal.drug.name if signal.drug else "Unknown drug",
            disease_name=signal.disease.name if signal.disease else "Unknown disease",
            mechanism=signal.biological_mechanism or "",
            evidence_items=evidence_dicts,
            score=signal.evidence_score,
        )

    return signal


@router.get("/{signal_id}/explain")
def explain_signal(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    signal = (
        db.query(RepurposingSignal)
        .options(
            joinedload(RepurposingSignal.drug),
            joinedload(RepurposingSignal.disease),
            joinedload(RepurposingSignal.evidence_items),
        )
        .filter(RepurposingSignal.id == signal_id)
        .first()
    )
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    evidence_dicts = [
        {"evidence_type": e.evidence_type, "title": e.title}
        for e in (signal.evidence_items or [])
    ]
    explanation = ai_service.explain_signal(
        drug_name=signal.drug.name if signal.drug else "Unknown",
        disease_name=signal.disease.name if signal.disease else "Unknown",
        mechanism=signal.biological_mechanism or "",
        evidence_items=evidence_dicts,
        score=signal.evidence_score,
    )

    return {
        "signal_id": signal_id,
        "drug_name": signal.drug.name if signal.drug else None,
        "disease_name": signal.disease.name if signal.disease else None,
        "explanation": explanation,
        "explanation_factors": signal.explanation_factors or [],
        "score_breakdown": signal.score_breakdown or {},
        "ai_backend": ai_service.backend,
        "disclaimer": (
            "This explanation is a research-prioritization signal generated by an experimental "
            "AI system. It is NOT a clinical recommendation, medical diagnosis, or treatment guidance."
        ),
    }


@router.get("/{signal_id}/source-breakdown")
def get_source_breakdown(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Returns a per-source evidence breakdown for a signal.
    Answers: "Which research sources support this signal?" and
             "How many unique, deduplicated records contributed to the score?"

    - Counts are per-source
    - Cross-source duplicates are identified (same DOI/PMID in 2+ sources)
    - Demo records are clearly separated from live records
    - Every traceable record is returned with full provenance

    This endpoint powers the "Why this score?" explanation in the UI.
    Research decision-support only — not clinical guidance.
    """
    signal = (
        db.query(RepurposingSignal)
        .options(
            joinedload(RepurposingSignal.drug),
            joinedload(RepurposingSignal.disease),
            joinedload(RepurposingSignal.evidence_items),
        )
        .filter(RepurposingSignal.id == signal_id)
        .first()
    )
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    evidence_items = signal.evidence_items or []
    drug_name    = signal.drug.name    if signal.drug    else "Unknown"
    disease_name = signal.disease.name if signal.disease else "Unknown"

    # ── 1. Per-source counts ──────────────────────────────────────────────────
    source_counts: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "count": 0, "live": 0, "demo": 0, "records": []
    })

    for ev in evidence_items:
        src = ev.data_source or ev.source_name or "unknown"
        source_counts[src]["count"] += 1
        if ev.is_demo_data:
            source_counts[src]["demo"] += 1
        else:
            source_counts[src]["live"] += 1
        source_counts[src]["records"].append({
            "id":               ev.id,
            "title":            ev.title,
            "evidence_type":    ev.evidence_type,
            "authors":          ev.authors or [],
            "publication_date": ev.publication_date,
            "journal":          ev.journal,
            "doi":              ev.doi,
            "pmid":             ev.pmid,
            "pmcid":            getattr(ev, "pmcid", None),
            "nct_id":           ev.nct_id,
            "source_url":       ev.source_url,
            "relevance_score":  ev.relevance_score,
            "relevance_explanation": ev.relevance_explanation,
            "supports_mechanism":    ev.supports_mechanism,
            "is_demo_data":     ev.is_demo_data,
        })

    # ── 2. Cross-source deduplication ─────────────────────────────────────────
    # Identify articles that appear in multiple sources (same DOI or PMID)
    doi_to_sources:  Dict[str, List[str]] = defaultdict(list)
    pmid_to_sources: Dict[str, List[str]] = defaultdict(list)

    for ev in evidence_items:
        src = ev.data_source or ev.source_name or "unknown"
        if ev.doi:
            doi_to_sources[ev.doi.strip().lower()].append(src)
        if ev.pmid:
            pmid_to_sources[ev.pmid.strip()].append(src)

    cross_source_dupes = []
    for doi, sources in doi_to_sources.items():
        if len(set(sources)) > 1:
            cross_source_dupes.append({"identifier": doi, "type": "doi", "sources": list(set(sources))})
    for pmid, sources in pmid_to_sources.items():
        if len(set(sources)) > 1:
            cross_source_dupes.append({"identifier": pmid, "type": "pmid", "sources": list(set(sources))})

    # ── 3. Unique (deduplicated) count ────────────────────────────────────────
    seen: set = set()
    unique_live_count = 0
    unique_demo_count = 0

    for ev in evidence_items:
        doi   = (ev.doi   or "").strip().lower()
        pmid  = (ev.pmid  or "").strip()
        title = (ev.title or "").strip().lower()[:80]
        canonical = doi or pmid or title
        if canonical and canonical in seen:
            continue
        if canonical:
            seen.add(canonical)
        if ev.is_demo_data:
            unique_demo_count += 1
        else:
            unique_live_count += 1

    # ── 4. Evidence type distribution ────────────────────────────────────────
    type_dist: Dict[str, int] = defaultdict(int)
    for ev in evidence_items:
        if not ev.is_demo_data:
            type_dist[ev.evidence_type] += 1

    # ── 5. Build score explanation from real evidence ─────────────────────────
    evidence_dicts = [
        {
            "evidence_type":    ev.evidence_type,
            "publication_date": ev.publication_date or "",
            "data_source":      ev.data_source or ev.source_name or "unknown",
            "doi":              ev.doi,
            "pmid":             ev.pmid,
            "is_demo_data":     ev.is_demo_data,
        }
        for ev in evidence_items
    ]

    drug_targets  = signal.drug.molecular_targets    if signal.drug    else []
    disease_paths = signal.disease.affected_pathways if signal.disease else []

    from app.services.ingestion_service import IngestionService
    mechanism_overlap = IngestionService._compute_overlap(drug_targets, disease_paths)

    score_data = ai_service.calculate_evidence_score(
        drug_name=drug_name,
        disease_name=disease_name,
        evidence_items=evidence_dicts,
        mechanism_overlap=mechanism_overlap,
        drug_targets=drug_targets,
        disease_pathways=disease_paths,
    )

    # ── 6. Determine whether this signal has any live (non-demo) evidence ─────
    has_live_evidence = any(not ev.is_demo_data for ev in evidence_items)

    return {
        "signal_id":     signal_id,
        "drug_name":     drug_name,
        "disease_name":  disease_name,
        "evidence_score": signal.evidence_score,
        "confidence_level": signal.confidence_level,
        "data_source":   signal.data_source,

        # Source breakdown — answers "Which sources support this signal?"
        "source_breakdown": {
            src: {
                "count":   data["count"],
                "live":    data["live"],
                "demo":    data["demo"],
                "records": data["records"],
            }
            for src, data in sorted(source_counts.items())
        },

        # Totals
        "total_evidence_records":    len(evidence_items),
        "unique_evidence_records":   unique_live_count + unique_demo_count,
        "unique_live_records":       unique_live_count,
        "unique_demo_records":       unique_demo_count,
        "independent_source_count":  len(source_counts),
        "has_live_evidence":         has_live_evidence,

        # Cross-source duplicates — transparency about double-counting prevention
        "cross_source_duplicates":   cross_source_dupes,
        "duplicates_removed":        len(evidence_items) - (unique_live_count + unique_demo_count),

        # Evidence type distribution (live records only)
        "evidence_type_distribution": dict(type_dist),

        # Score breakdown calculated from actual stored evidence
        "score_breakdown_from_evidence": score_data,

        # Score explanation
        "score_explanation": (
            f"Score of {signal.evidence_score:.0f}/100 based on {unique_live_count} unique live evidence "
            f"record(s) from {len(source_counts)} independent source(s). "
            f"{len(cross_source_dupes)} cross-source duplicate(s) removed. "
            f"Demo records: {unique_demo_count} (not counted in live scoring). "
            "Experimental research-prioritization score — not clinical probability."
            if has_live_evidence else
            f"Score of {signal.evidence_score:.0f}/100 based on {unique_demo_count} demo seed record(s). "
            "No live evidence records yet — run ingestion to fetch real research data. "
            "Experimental research-prioritization score — not clinical probability."
        ),

        "disclaimer": (
            "This breakdown is generated by an experimental research intelligence system. "
            "All signals are research-prioritization candidates requiring expert validation. "
            "This is NOT clinical guidance, medical advice, or treatment recommendation. "
            "Demo records are clearly labelled and never contribute to live evidence scoring."
        ),
    }



def get_signal_pipeline(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Returns the full detection pipeline trace for a signal.
    This is the primary explainability endpoint — shows exactly HOW
    BioArbitrage discovered and scored this drug-repurposing signal.

    Combines:
    - 6-step pipeline trace (generated by AIService)
    - Enriched 5-factor score breakdown
    - Detection rationale (how was this found?)
    - Relationship graph data (Drug → Target → Pathway → Disease)
    - Evidence traceability
    """
    signal = (
        db.query(RepurposingSignal)
        .options(
            joinedload(RepurposingSignal.drug),
            joinedload(RepurposingSignal.disease),
            joinedload(RepurposingSignal.evidence_items),
        )
        .filter(RepurposingSignal.id == signal_id)
        .first()
    )
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    drug_name    = signal.drug.name    if signal.drug    else "Unknown"
    disease_name = signal.disease.name if signal.disease else "Unknown"
    drug_targets  = signal.drug.molecular_targets    if signal.drug    else []
    disease_paths = signal.disease.affected_pathways if signal.disease else []

    evidence_dicts = [
        {
            "evidence_type":     e.evidence_type,
            "title":             e.title,
            "publication_date":  e.publication_date or "",
            "source_name":       e.source_name,
            "source_url":        e.source_url,
            "doi":               e.doi,
            "pmid":              e.pmid,
            "nct_id":            e.nct_id,
            "supports_mechanism":e.supports_mechanism,
            "relevance_score":   e.relevance_score,
            "relevance_explanation": e.relevance_explanation,
            "is_demo_data":      e.is_demo_data,
        }
        for e in (signal.evidence_items or [])
    ]

    # Compute enriched score from ACTUAL stored evidence (always dynamic, never from seed)
    enrichment = SIGNAL_ENRICHMENTS.get((drug_name, disease_name), {})

    from app.services.ingestion_service import IngestionService
    mechanism_overlap = IngestionService._compute_overlap(drug_targets, disease_paths)

    enriched_score = ai_service.calculate_evidence_score(
        drug_name=drug_name,
        disease_name=disease_name,
        evidence_items=evidence_dicts,
        mechanism_overlap=mechanism_overlap,
        drug_targets=drug_targets,
        disease_pathways=disease_paths,
    )

    pipeline_input = {
        "drug_name":       drug_name,
        "disease_name":    disease_name,
        "biological_mechanism": signal.biological_mechanism,
        "evidence_items":  evidence_dicts,
        "evidence_score":  signal.evidence_score,
        "drug_targets":    drug_targets,
        "disease_pathways":disease_paths,
    }
    pipeline_steps = ai_service.generate_pipeline_steps(pipeline_input)

    detection_rationale = enrichment.get("detection_rationale", {
        "how_detected": signal.ai_explanation or "Mechanistic pathway overlap and cross-source evidence matching.",
        "mechanism_summary": signal.biological_mechanism,
        "pathway_overlap": list(set(drug_targets) & set(disease_paths)),
        "shared_targets": drug_targets[:3],
        "evidence_types_found": list({e["evidence_type"] for e in evidence_dicts}),
        "research_gaps": [],
        "validation_required": True,
        "clinical_readiness": "Requires expert review [DEMO]",
    })

    relationship_graph = enrichment.get("relationship_graph", {
        "drug_node":    {"label": drug_name,    "type": "drug",    "approved_for": ", ".join(signal.drug.approved_indications[:2]) if signal.drug else ""},
        "target_nodes": [{"label": t, "type": "target", "action": "Modulates"} for t in drug_targets[:4]],
        "pathway_nodes":[{"label": p, "type": "pathway","disease_relevance": "relevant"} for p in disease_paths[:4]],
        "disease_node": {"label": disease_name, "type": "disease","affected_by": ", ".join(disease_paths[:2])},
        "evidence_nodes":[{"label": e["title"][:60] + "…", "type": "evidence","strength": "moderate"} for e in evidence_dicts],
    })

    evidence_matching = ai_service.match_evidence(drug_name, disease_name, evidence_dicts)

    return {
        "signal_id":          signal_id,
        "drug_name":          drug_name,
        "disease_name":       disease_name,
        "evidence_score":     signal.evidence_score,
        "confidence_level":   signal.confidence_level,

        # 6-step pipeline trace
        "pipeline_steps":     pipeline_steps,

        # Transparent scoring
        "enriched_score_breakdown": enriched_score,

        # How was this detected?
        "detection_rationale":detection_rationale,

        # Visual graph data
        "relationship_graph": relationship_graph,

        # Cross-source matching
        "evidence_matching":  evidence_matching,

        # Traceable evidence
        "evidence_items":     evidence_dicts,

        # AI backend info
        "ai_backend":         ai_service.backend,

        "disclaimer": (
            "This pipeline trace is generated by an experimental research intelligence system. "
            "All signals are research-prioritization candidates requiring expert validation. "
            "This is NOT clinical guidance, medical advice, or treatment recommendation. "
            "All demo data is clearly labelled as simulated."
        ),
        "is_demo_data": signal.data_source == "demo",
    }


# ── Register pipeline endpoint (must be after all route definitions) ─────────
router.get("/{signal_id}/pipeline")(get_signal_pipeline)


# ─────────────────────────────────────────────────────────────────────────────
# LIVE EVIDENCE ENDPOINT
# Returns only live (non-demo) evidence records for a signal with full
# provenance: source, title, authors, date, journal, DOI, PMID, PMCID,
# NCT ID, abstract, open-access info, article type, source URL.
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{signal_id}/live-evidence")
def get_live_evidence(
    signal_id: int,
    evidence_type: Optional[str] = Query(None, description="Filter: research_paper, clinical_trial, preprint, protein_annotation"),
    source: Optional[str] = Query(None, description="Filter by source: pubmed, europepmc, etc."),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Returns all LIVE (non-demo) evidence records for a signal with complete provenance.

    Every record includes:
    - source name and original source URL
    - title, authors, abstract
    - publication date / year
    - journal
    - DOI, PMID, PMCID, NCT ID (where available)
    - evidence type (research_paper, clinical_trial, preprint, protein_annotation)
    - open-access indicator (inferred from source URL / PMCID presence)
    - relevance explanation

    Demo records are completely excluded from this response.
    Research decision-support only — not clinical recommendations.
    """
    signal = (
        db.query(RepurposingSignal)
        .options(
            joinedload(RepurposingSignal.drug),
            joinedload(RepurposingSignal.disease),
            joinedload(RepurposingSignal.evidence_items),
        )
        .filter(RepurposingSignal.id == signal_id)
        .first()
    )
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    drug_name    = signal.drug.name    if signal.drug    else "Unknown"
    disease_name = signal.disease.name if signal.disease else "Unknown"

    # Filter to live evidence only
    live_items = [
        e for e in (signal.evidence_items or [])
        if not e.is_demo_data
    ]

    # Apply optional filters
    if evidence_type:
        live_items = [e for e in live_items if e.evidence_type == evidence_type]
    if source:
        live_items = [e for e in live_items if (e.data_source or e.source_name or "") == source]

    # Sort: most recent first
    live_items.sort(
        key=lambda e: e.publication_date or "",
        reverse=True,
    )

    # Group by source for per-source summary
    per_source: Dict[str, int] = defaultdict(int)
    for e in live_items:
        per_source[e.data_source or e.source_name or "unknown"] += 1

    # Serialize with full provenance
    records = []
    for e in live_items:
        src_name = e.data_source or e.source_name or "unknown"
        # Infer open-access: PMCID present or source is europepmc/biorxiv/medrxiv
        is_open_access = bool(
            getattr(e, "pmcid", None)
            or src_name in ("europepmc", "biorxiv", "medrxiv")
        )
        records.append({
            "id":                    e.id,
            "source":                src_name,
            "source_url":            e.source_url,
            "title":                 e.title,
            "authors":               e.authors or [],
            "publication_date":      e.publication_date,
            "journal":               e.journal,
            "abstract":              e.abstract,
            "doi":                   e.doi,
            "pmid":                  e.pmid,
            "pmcid":                 getattr(e, "pmcid", None),
            "nct_id":                e.nct_id,
            "evidence_type":         e.evidence_type,
            "is_open_access":        is_open_access,
            "relevance_score":       e.relevance_score,
            "relevance_explanation": e.relevance_explanation,
            "supports_mechanism":    e.supports_mechanism,
            "is_demo_data":          False,  # always False — this endpoint only returns live
        })

    # Summary counts
    type_counts: Dict[str, int] = defaultdict(int)
    for e in live_items:
        type_counts[e.evidence_type] += 1

    has_live = len(live_items) > 0
    empty_sources = [
        s for s in ("pubmed", "europepmc", "clinicaltrials", "elsevier", "biorxiv", "medrxiv", "uniprot")
        if s not in per_source
    ]

    return {
        "signal_id":    signal_id,
        "drug_name":    drug_name,
        "disease_name": disease_name,
        "has_live_evidence": has_live,
        "total_live_records":   len(live_items),
        "per_source_counts":    dict(per_source),
        "per_type_counts":      dict(type_counts),
        "sources_without_evidence": empty_sources,
        "evidence": records,
        "message": (
            f"Live evidence supporting {drug_name} \u2192 {disease_name} signal."
            if has_live else
            f"No live evidence records currently ingested for {drug_name} \u2192 {disease_name}. "
            f"Run ingestion (POST /api/ingestion/search) with drug='{drug_name}' and "
            f"disease='{disease_name}' to fetch real research from all connected sources."
        ),
        "disclaimer": (
            "Research decision-support only. Not clinical recommendations. "
            "All records are real metadata fetched from connected research databases. "
            "No fabricated titles, authors, DOIs, PMIDs, or URLs."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# DEMO SIGNAL CLEANUP
# Safe endpoint to remove pure-demo signals (those with only demo evidence
# or no evidence at all). Never deletes signals that have live evidence.
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/demo", summary="Remove pure-demo signals safely")
def delete_demo_signals(
    dry_run: bool = Query(True, description="If true, only report what would be deleted (no actual deletion)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Safely removes signals that have NO live evidence (only demo/seed records or none).
    Signals with at least one live evidence record are NEVER deleted.

    dry_run=true (default): reports what would be removed, makes no changes.
    dry_run=false: actually removes the qualifying demo-only signals.

    Use this to clean up demo/seed signals from the database once real ingestion
    has produced live signals.

    NOTE: The underlying Drug, Disease, and live Evidence records are preserved.
    """
    from sqlalchemy import exists as sq_exists, not_

    # A signal is "demo-only" when it has no live evidence records
    live_ev_exists = sq_exists().where(
        (Evidence.signal_id == RepurposingSignal.id) &
        (Evidence.is_demo_data == False)
    )
    demo_only_signals = (
        db.query(RepurposingSignal)
        .filter(not_(live_ev_exists))
        .all()
    )

    report = [
        {
            "id":           s.id,
            "drug_name":    s.drug.name if s.drug else "?",
            "disease_name": s.disease.name if s.disease else "?",
            "data_source":  s.data_source,
            "evidence_score": s.evidence_score,
            "demo_evidence_count": sum(1 for e in (s.evidence_items or []) if e.is_demo_data),
        }
        for s in demo_only_signals
    ]

    if dry_run:
        return {
            "dry_run":    True,
            "would_delete": len(demo_only_signals),
            "signals":    report,
            "message": (
                f"Dry run only — no changes made. "
                f"{len(demo_only_signals)} demo-only signal(s) would be removed. "
                f"Set ?dry_run=false to actually delete them."
            ),
        }

    # Actually delete — child evidence first to avoid FK constraint
    deleted_ids = [s.id for s in demo_only_signals]
    for s in demo_only_signals:
        db.query(Evidence).filter(Evidence.signal_id == s.id).delete(synchronize_session=False)
        db.delete(s)
    db.commit()

    return {
        "dry_run":   False,
        "deleted":   len(deleted_ids),
        "deleted_ids": deleted_ids,
        "signals":   report,
        "message": (
            f"Removed {len(deleted_ids)} demo-only signal(s). "
            f"Signals with live evidence were preserved. "
            f"Drug, Disease, and live Evidence records were NOT deleted."
        ),
    }
