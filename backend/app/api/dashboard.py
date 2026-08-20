"""
Dashboard API
=============
GET /api/dashboard

Returns live statistics, real signal trend (from ingestion runs), recent
signals with full source traceability fields, and high-confidence signals.

FIX: removed DEMO_SIGNAL_TREND — signal trend is now computed from real
IngestionRun records. Falls back to an empty list when no runs exist yet.

FIX: _to_list_item now joins evidence_items so live_evidence_count,
unique_evidence_count, and source_names are populated on dashboard cards.

FIX: total_research_sources and recent_updates now count only LIVE records.
"""
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.models.drug import Drug
from app.models.disease import Disease
from app.models.evidence import Evidence
from app.models.ingestion_run import IngestionRun
from app.models.research_source import ResearchSource
from app.models.signal import RepurposingSignal
from app.schemas.schemas import (
    DashboardResponse, DashboardStats, SignalTrendPoint, SignalListItem,
)
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # ── Counts — live sources only ────────────────────────────────────────────
    live_sources = (
        db.query(ResearchSource)
        .filter(ResearchSource.is_demo_data == False)
        .count()
    )
    drugs_monitored  = db.query(Drug).count()
    diseases_tracked = db.query(Disease).count()
    total_signals    = db.query(RepurposingSignal).filter(
        RepurposingSignal.status == "active"
    ).count()
    high_conf = db.query(RepurposingSignal).filter(
        RepurposingSignal.confidence_level == "high",
        RepurposingSignal.status == "active",
    ).count()

    # Recent updates = live records ingested in last 7 days
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_live = (
        db.query(ResearchSource)
        .filter(
            ResearchSource.is_demo_data == False,
            ResearchSource.ingested_at  >= seven_days_ago,
        )
        .count()
    )

    stats = DashboardStats(
        total_research_sources=live_sources,
        drugs_monitored=drugs_monitored,
        diseases_tracked=diseases_tracked,
        total_signals=total_signals,
        high_confidence_signals=high_conf,
        recent_updates=recent_live,
    )

    # ── Signal trend — built from real IngestionRun records ───────────────────
    trend = _build_real_signal_trend(db)

    # ── Recent and high-confidence signals (with evidence traceability) ───────
    eager = [
        joinedload(RepurposingSignal.drug),
        joinedload(RepurposingSignal.disease),
        joinedload(RepurposingSignal.evidence_items),
    ]

    recent_raw = (
        db.query(RepurposingSignal)
        .options(*eager)
        .filter(RepurposingSignal.status == "active")
        .order_by(RepurposingSignal.evidence_score.desc())
        .limit(5)
        .all()
    )
    recent_signals = [_to_list_item(s) for s in recent_raw]

    high_conf_raw = (
        db.query(RepurposingSignal)
        .options(*eager)
        .filter(
            RepurposingSignal.confidence_level == "high",
            RepurposingSignal.status == "active",
        )
        .order_by(RepurposingSignal.evidence_score.desc())
        .limit(4)
        .all()
    )
    high_conf_signals = [_to_list_item(s) for s in high_conf_raw]

    return DashboardResponse(
        stats=stats,
        signal_trend=trend,
        recent_signals=recent_signals,
        high_confidence_signals=high_conf_signals,
    )


# ── Real signal trend ─────────────────────────────────────────────────────────

def _build_real_signal_trend(db: Session):
    """
    Build a 30-point signal trend from real IngestionRun history.

    Approach:
      - Take up to 30 completed ingestion runs ordered by date.
      - For each run date, query the signal table for totals at that point.
      - Falls back to current snapshot if fewer than 2 runs exist.
    """
    runs = (
        db.query(IngestionRun)
        .filter(IngestionRun.status.in_(["complete", "partial"]))
        .order_by(IngestionRun.finished_at.asc())
        .limit(30)
        .all()
    )

    if len(runs) < 2:
        # Not enough history — return a single current snapshot
        total = db.query(RepurposingSignal).filter(RepurposingSignal.status == "active").count()
        high  = db.query(RepurposingSignal).filter(
            RepurposingSignal.status == "active",
            RepurposingSignal.confidence_level == "high",
        ).count()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if total == 0:
            return []
        return [SignalTrendPoint(date=today, total=total, high_confidence=high)]

    # Build cumulative trend: for each run, count signals active at that date
    trend = []
    seen_dates = set()
    for run in runs:
        if not run.finished_at:
            continue
        date_str = run.finished_at.strftime("%Y-%m-%d")
        if date_str in seen_dates:
            continue
        seen_dates.add(date_str)

        # Count signals created on or before this run date
        run_ts = run.finished_at
        total = db.query(RepurposingSignal).filter(
            RepurposingSignal.status == "active",
            RepurposingSignal.detected_at <= run_ts,
        ).count()
        high = db.query(RepurposingSignal).filter(
            RepurposingSignal.status == "active",
            RepurposingSignal.confidence_level == "high",
            RepurposingSignal.detected_at <= run_ts,
        ).count()
        trend.append(SignalTrendPoint(date=date_str, total=total, high_confidence=high))

    return trend


# ── Signal list item with full traceability ───────────────────────────────────

def _to_list_item(s: RepurposingSignal) -> SignalListItem:
    """
    Build a SignalListItem with live_evidence_count, unique_evidence_count,
    and source_names populated from the loaded evidence_items.

    FIX: this function now loads evidence_items (via joinedload in the query)
    and computes source traceability fields, matching what signals.py does.
    """
    source_names = []
    live_count   = 0
    seen_ids: set = set()
    unique_count  = 0

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
