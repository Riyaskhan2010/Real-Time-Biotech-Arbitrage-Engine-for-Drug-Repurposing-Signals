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
from datetime import datetime, timezone, timedelta
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


# ── DB-backed ingestion lock ──────────────────────────────────────────────────
#
# The previous module-level `_run_in_progress = False` global was unsafe for
# multi-process or multi-worker deployments: each worker had its own copy of
# the flag, so concurrent ingestion jobs on different workers bypassed the guard.
#
# New approach: store the lock state in the `ingestion_runs` table itself.
# "Running" means there is a row with status="running" and started_at within
# the last LOCK_TIMEOUT_MINUTES minutes.  The timeout prevents a crash from
# leaving the system permanently locked.
#
# This is safe for any number of workers / replicas as long as they share the
# same database (which they must — SQLite or PostgreSQL).

LOCK_TIMEOUT_MINUTES = 30   # a run older than this is considered stale/dead


def _ingestion_is_running(db: Session) -> bool:
    """Return True if a non-stale ingestion run is currently in progress."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=LOCK_TIMEOUT_MINUTES)
    return db.query(IngestionRun).filter(
        IngestionRun.status == "running",
        IngestionRun.started_at >= cutoff,
    ).first() is not None


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

    Lock: uses the ingestion_runs table to prevent concurrent runs across
    all workers/processes sharing the same database.
    """
    if _ingestion_is_running(db):
        raise HTTPException(
            status_code=409,
            detail="An ingestion run is already in progress. Please wait for it to finish.",
        )

    query_terms = (body.query_terms if body and body.query_terms else None)
    run = await ingestion_service.run(db, query_terms=query_terms)
    return run


@router.post("/search", response_model=IngestionRunOut)
async def search_drug_disease(
    body: SearchRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    On-demand research search for a specific drug + disease combination.
    Uses DB-backed lock — safe across multiple workers/processes.
    """
    if _ingestion_is_running(db):
        raise HTTPException(
            status_code=409,
            detail="An ingestion run is already in progress. Please wait.",
        )

    drug    = body.drug.strip()
    disease = body.disease.strip()
    if not drug or not disease:
        raise HTTPException(status_code=422, detail="Both 'drug' and 'disease' are required.")

    query_terms = _build_search_queries(drug, disease, body.extra_terms or [])
    run = await ingestion_service.run(db, query_terms=query_terms)
    return run


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


@router.get("/latest", response_model=Optional[IngestionRunStatus])
def get_latest_run(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Return the most recent ingestion run summary.
    Returns null (HTTP 200) when no runs exist yet — not 404.
    This keeps Render logs clean while the frontend handles null gracefully.
    """
    run = (
        db.query(IngestionRun)
        .order_by(IngestionRun.started_at.desc())
        .first()
    )
    return run  # None serialises as JSON null with 200


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
def is_running(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Check whether an ingestion run is currently in progress (DB-backed, multi-worker safe)."""
    return {"running": _ingestion_is_running(db)}


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
