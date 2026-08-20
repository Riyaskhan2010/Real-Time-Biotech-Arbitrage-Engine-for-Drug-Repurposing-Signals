"""
Ingestion API
=============
POST /api/ingestion/run          — trigger a full ingestion run (async)
POST /api/ingestion/search       — on-demand search for specific drug + disease
GET  /api/ingestion/status/{id}  — poll run status
GET  /api/ingestion/latest       — last run summary
GET  /api/ingestion/source-status — connectivity probe for all sources
GET  /api/ingestion/running      — quick in-progress check
GET  /api/ingestion/query-terms  — list currently configured query terms

All endpoints require authentication.
No API keys are ever exposed to the frontend.
"""
import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.ingestion_run import IngestionRun
from app.schemas.schemas import IngestionRunOut, IngestionRunStatus, SourceStatusItem
from app.services.ingestion_service import ingestion_service
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])
logger = logging.getLogger(__name__)

# Guard: only one run at a time
_run_in_progress = False


# ── Request bodies ────────────────────────────────────────────────────────────

class RunIngestionRequest(BaseModel):
    """Optional body for POST /run — allows caller to override query terms."""
    query_terms: Optional[List[str]] = None


class SearchRequest(BaseModel):
    """
    Body for POST /search — on-demand drug+disease research query.
    The system builds source-appropriate queries and searches ALL connected
    sources for the researcher's specific drug+disease combination.
    """
    drug: str
    disease: str
    extra_terms: Optional[List[str]] = None   # optional: targets, mechanisms, etc.


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/run", response_model=IngestionRunOut)
async def run_ingestion(
    body: Optional[RunIngestionRequest] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Trigger a full research ingestion run.

    Optional body:
      { "query_terms": ["metformin cancer", "aspirin alzheimer"] }

    When query_terms is omitted the configured INGESTION_QUERY_TERMS are used.
    Each query term is sent to all enabled sources; results are deduplicated,
    entity-extracted, matched to signals, and stored.
    """
    global _run_in_progress
    if _run_in_progress:
        raise HTTPException(
            status_code=409,
            detail="An ingestion run is already in progress. Please wait for it to finish.",
        )

    query_terms = (body.query_terms if body and body.query_terms else None)

    _run_in_progress = True
    try:
        run = await ingestion_service.run(db, query_terms=query_terms)
        return run
    finally:
        _run_in_progress = False


@router.post("/search", response_model=IngestionRunOut)
async def search_drug_disease(
    body: SearchRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    On-demand research search for a specific drug + disease combination.

    The system constructs optimised queries for each source:
      - General:         "{drug} {disease}"
      - Structured:      "drug:{drug} disease:{disease}"  (used by UniProt connector)
      - Mechanism:       "{drug} mechanism {disease}"
      - Clinical:        "{drug} clinical trial {disease}"
      - Target/pathway:  "{drug} pathway"

    All enabled sources are queried. Results enter the full evidence pipeline
    (dedup → entity match → signal update → rescore).

    This endpoint allows researchers to search for ANY drug + disease without
    modifying configuration.
    """
    global _run_in_progress
    if _run_in_progress:
        raise HTTPException(
            status_code=409,
            detail="An ingestion run is already in progress. Please wait.",
        )

    drug    = body.drug.strip()
    disease = body.disease.strip()
    if not drug or not disease:
        raise HTTPException(status_code=422, detail="Both 'drug' and 'disease' are required.")

    # Build source-appropriate query variants
    query_terms = _build_search_queries(drug, disease, body.extra_terms or [])

    _run_in_progress = True
    try:
        run = await ingestion_service.run(db, query_terms=query_terms)
        return run
    finally:
        _run_in_progress = False


@router.get("/query-terms")
def get_query_terms(current_user=Depends(get_current_active_user)):
    """
    Return the currently configured background ingestion query terms.
    These are read from INGESTION_QUERY_TERMS in backend/.env (or config.py default).
    """
    return {
        "query_terms": settings.query_terms_list,
        "source": "INGESTION_QUERY_TERMS env var / config.py",
        "note": (
            "These terms drive the background/scheduled ingestion. "
            "Use POST /api/ingestion/search to run an on-demand search "
            "for any drug + disease without modifying this list."
        ),
    }


@router.get("/status/{run_id}", response_model=IngestionRunStatus)
def get_run_status(
    run_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Poll the status of an ingestion run by ID."""
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Ingestion run not found")
    return run


@router.get("/latest", response_model=IngestionRunStatus)
def get_latest_run(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Return the most recent ingestion run summary, or 404 if none exist."""
    run = (
        db.query(IngestionRun)
        .order_by(IngestionRun.started_at.desc())
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="No ingestion runs found")
    return run


@router.get("/source-status", response_model=List[SourceStatusItem])
async def get_source_status(
    current_user=Depends(get_current_active_user),
):
    """
    Probe connectivity for all configured research sources.
    Returns status: connected | error | timeout | disabled for each.
    Never exposes API keys or credentials.
    """
    results = await ingestion_service.check_sources()
    return results


@router.get("/running")
def is_running(current_user=Depends(get_current_active_user)):
    """Quick check whether an ingestion run is currently in progress."""
    return {"running": _run_in_progress}


# ── Query builder ─────────────────────────────────────────────────────────────

def _build_search_queries(drug: str, disease: str, extra: List[str]) -> List[str]:
    """
    Build a set of search queries optimised for different source types.

    Returns a deduplicated list so each query runs once per source.
    """
    queries = [
        # Primary: drug + disease combined (works for PubMed, EuropePMC, Elsevier, bioRxiv, medRxiv)
        f"{drug} {disease}",
        # Structured: used by UniProt connector hint parser
        f"drug:{drug} disease:{disease}",
        # Mechanism / target context
        f"{drug} mechanism pathway",
        # Clinical evidence
        f"{drug} clinical trial {disease}",
    ]

    # Additional user-supplied terms (e.g. target name, pathway)
    for term in extra:
        t = term.strip()
        if t:
            queries.append(f"{drug} {t}")

    # Deduplicate while preserving order
    seen = set()
    result = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            result.append(q)
    return result
