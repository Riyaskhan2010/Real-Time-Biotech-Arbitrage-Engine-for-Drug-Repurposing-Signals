"""
Public API — No authentication required.

These endpoints expose only aggregate, non-sensitive statistics suitable
for the public landing page. No user data, no evidence content, no signals
detail — only counts derived from the database.

All statistics are database-driven — no hard-coded values.
Demo records are clearly separated from live ingested records.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import exists as sq_exists
from app.database import get_db
from app.models.drug import Drug
from app.models.disease import Disease
from app.models.evidence import Evidence
from app.models.research_source import ResearchSource
from app.models.signal import RepurposingSignal
from app.config import settings

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/stats")
def get_public_stats(db: Session = Depends(get_db)):
    """
    Public landing-page statistics.
    No authentication required.
    Returns only aggregate counts — no sensitive research data.

    All signal/evidence counts reflect only LIVE (non-demo) data when
    live data is available. When no ingestion has run yet (startup state),
    the response includes has_live_data=False so the frontend can show
    an appropriate loading/pending state instead of misleading zeros.
    """
    # Live (non-demo) research source records indexed by ingestion
    sources_indexed = db.query(ResearchSource).filter(
        ResearchSource.is_demo_data == False
    ).count()

    # Live evidence records
    live_evidence = db.query(Evidence).filter(
        Evidence.is_demo_data == False
    ).count()

    # Has any real ingestion run happened yet?
    has_live_data = sources_indexed > 0 or live_evidence > 0

    if has_live_data:
        # Count only signals that have at least one live evidence record.
        # This matches the default behaviour of GET /api/signals?include_demo=false
        live_ev_exists = sq_exists().where(
            (Evidence.signal_id == RepurposingSignal.id) &
            (Evidence.is_demo_data == False)
        )
        total_signals = db.query(RepurposingSignal).filter(
            RepurposingSignal.status == "active",
            live_ev_exists,
        ).count()

        high_confidence = db.query(RepurposingSignal).filter(
            RepurposingSignal.status == "active",
            RepurposingSignal.confidence_level == "high",
            live_ev_exists,
        ).count()
    else:
        # No live data yet — return zeros so the UI shows a meaningful
        # "ingestion pending" state rather than inflated demo counts.
        total_signals   = 0
        high_confidence = 0

    # Number of configured biomedical databases (always real — from config)
    configured_databases = len(settings.enabled_sources_list)

    # Drugs and diseases are seeded and always present
    drugs_monitored  = db.query(Drug).count()
    diseases_tracked = db.query(Disease).count()

    return {
        "total_signals":        total_signals,
        "high_confidence":      high_confidence,
        "sources_indexed":      sources_indexed,
        "configured_databases": configured_databases,
        "drugs_monitored":      drugs_monitored,
        "diseases_tracked":     diseases_tracked,
        "live_evidence":        live_evidence,
        # Frontend can use this to show an ingestion-pending notice
        # instead of confusing zeros when the platform first starts up.
        "has_live_data":        has_live_data,
    }
