from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float
from sqlalchemy.sql import func
from app.database import Base


class IngestionRun(Base):
    """
    Records every ingestion run for audit, status display, and rate-limiting.
    Each call to POST /api/ingestion/run creates one IngestionRun row.
    """
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True, index=True)

    # Run lifecycle
    status = Column(String(30), default="pending")
    # pending | running | complete | partial | failed

    started_at  = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

    # Per-source results (JSON list of SourceResult dicts)
    source_results = Column(JSON, default=list)

    # Aggregate counters
    total_fetched    = Column(Integer, default=0)
    total_new        = Column(Integer, default=0)
    total_duplicates = Column(Integer, default=0)
    total_errors     = Column(Integer, default=0)

    # Signal activity
    signals_updated = Column(Integer, default=0)
    signals_created = Column(Integer, default=0)
    alerts_created  = Column(Integer, default=0)

    # Human-readable summary
    summary = Column(Text, nullable=True)
    error   = Column(Text, nullable=True)
