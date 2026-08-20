"""
Research Monitor API
====================
Returns a combined view of LIVE ingested records + DEMO seed records.

Each record is clearly labelled:
  data_mode: "live"  — from a real ingestion run
  data_mode: "demo"  — from seed data

GET /api/research-monitor
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.data.seed_data import DEMO_RESEARCH_MONITOR
from app.database import get_db
from app.models.research_source import ResearchSource
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api/research-monitor", tags=["research-monitor"])
logger = logging.getLogger(__name__)

PIPELINE_STAGES = [
    {"stage": "ingestion",               "label": "Research Ingestion",      "description": "New research record detected from source feed"},
    {"stage": "entity_extraction",       "label": "Entity Extraction",        "description": "Drug, disease, and mechanism entities extracted from text"},
    {"stage": "mechanism_identification","label": "Mechanism Identification", "description": "Biological pathway overlap analysis performed"},
    {"stage": "evidence_matching",       "label": "Evidence Matching",        "description": "Cross-referenced against existing signal database"},
    {"stage": "signal_evaluation",       "label": "Signal Evaluation",        "description": "Evidence score updated, signal status reviewed"},
]


def _rs_to_monitor_record(rs: ResearchSource) -> dict:
    """Convert a live ResearchSource DB row to the monitor record format."""
    # Build matched_signals list from extracted entities
    drugs    = rs.extracted_drugs    or []
    diseases = rs.extracted_diseases or []
    matched: list[dict] = []
    for drug in drugs[:2]:
        for disease in diseases[:2]:
            matched.append({"drug": drug, "disease": disease, "score_delta": 0})

    return {
        "id": f"RS-{rs.id}",
        "title": rs.title,
        "source": rs.source_type.capitalize(),
        "source_type": rs.source_type,
        "ingested_at": rs.ingested_at.isoformat() if rs.ingested_at else datetime.now(timezone.utc).isoformat(),
        "pipeline_stage": "signal_evaluation" if rs.is_processed else "entity_extraction",
        "pipeline_status": "complete" if rs.is_processed else "pending",
        "extracted_entities": {
            "drugs":      rs.extracted_drugs      or [],
            "diseases":   rs.extracted_diseases   or [],
            "mechanisms": rs.extracted_mechanisms or [],
            "targets":    rs.extracted_targets    or [],
        },
        "matched_signals": matched,
        "evaluation_result": (
            f"Processed: {len(drugs)} drug(s) and {len(diseases)} disease(s) identified."
            if rs.is_processed else "Pending processing."
        ),
        "is_demo_data": False,
        "data_mode": "live",
    }


@router.get("")
def get_research_monitor(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Returns live-ingested records (if any) merged with DEMO seed records.
    Live records always appear first; each record carries a data_mode field.
    """
    # Fetch live records (non-demo, most recent first, capped at 20)
    live_rows = (
        db.query(ResearchSource)
        .filter(ResearchSource.is_demo_data == False)
        .order_by(ResearchSource.ingested_at.desc())
        .limit(20)
        .all()
    )
    live_records = [_rs_to_monitor_record(rs) for rs in live_rows]

    # Add data_mode to demo records
    demo_records = [
        {**r, "data_mode": "demo", "is_demo_data": True}
        for r in DEMO_RESEARCH_MONITOR
    ]

    all_records  = live_records + demo_records
    total        = len(all_records)
    live_count   = len(live_records)
    has_live     = live_count > 0

    return {
        "pipeline_stages": PIPELINE_STAGES,
        "recent_records":  all_records,
        "total_records":   total,
        "live_records":    live_count,
        "demo_records":    len(demo_records),
        "has_live_data":   has_live,
        "disclaimer": (
            "Live records are ingested from public research APIs and contain only official "
            "metadata. Demo records are clearly labelled simulated data. "
            "All records are research evidence only — not clinical recommendations."
            if has_live else
            "No live records yet. Displaying demo seed data only. "
            "Run ingestion to fetch real research records from PubMed, bioRxiv, medRxiv, "
            "ClinicalTrials.gov, Elsevier (Scopus), and Europe PMC."
        ),
        "integration_points": [
            {"source": "PubMed",             "status": "active", "api": "https://eutils.ncbi.nlm.nih.gov/"},
            {"source": "bioRxiv",            "status": "active", "api": "https://api.biorxiv.org/"},
            {"source": "medRxiv",            "status": "active", "api": "https://api.biorxiv.org/"},
            {"source": "ClinicalTrials.gov", "status": "active", "api": "https://clinicaltrials.gov/api/"},
            {"source": "Elsevier (Scopus)",  "status": "active", "api": "https://api.elsevier.com/content/search/scopus"},
            {"source": "Europe PMC",         "status": "active", "api": "https://www.ebi.ac.uk/europepmc/webservices/rest/search"},
            {"source": "UniProt",            "status": "active", "api": "https://rest.uniprot.org/uniprotkb/search"},
        ],
    }
