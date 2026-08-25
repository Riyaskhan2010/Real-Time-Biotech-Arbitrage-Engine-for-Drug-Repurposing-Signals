"""
Public API — No authentication required.

These endpoints expose only aggregate, non-sensitive statistics suitable
for the public landing page. No user data, no evidence content, no signals
detail — only counts derived from the database.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
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
    """
    # Active signal count
    total_signals = db.query(RepurposingSignal).filter(
        RepurposingSignal.status == "active"
    ).count()

    # High-confidence signals
    high_confidence = db.query(RepurposingSignal).filter(
        RepurposingSignal.status == "active",
        RepurposingSignal.confidence_level == "high",
    ).count()

    # Live (non-demo) research source records indexed
    sources_indexed = db.query(ResearchSource).filter(
        ResearchSource.is_demo_data == False
    ).count()

    # Number of configured biomedical databases
    # Derived from the enabled sources list in config rather than hard-coded
    configured_databases = len(settings.enabled_sources_list)

    # Drugs and diseases being monitored
    drugs_monitored   = db.query(Drug).count()
    diseases_tracked  = db.query(Disease).count()

    # Live evidence records
    live_evidence = db.query(Evidence).filter(
        Evidence.is_demo_data == False
    ).count()

    return {
        "total_signals":       total_signals,
        "high_confidence":     high_confidence,
        "sources_indexed":     sources_indexed,
        "configured_databases": configured_databases,
        "drugs_monitored":     drugs_monitored,
        "diseases_tracked":    diseases_tracked,
        "live_evidence":       live_evidence,
    }
