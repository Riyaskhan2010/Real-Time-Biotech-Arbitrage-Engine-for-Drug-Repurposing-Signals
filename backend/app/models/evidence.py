from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Evidence(Base):
    """
    A single piece of traceable evidence supporting a repurposing signal.
    Each item has a source reference for full traceability.
    """
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("repurposing_signals.id"), nullable=False)

    # Evidence classification
    evidence_type = Column(String(50), nullable=False)
    # Types: research_paper, preprint, clinical_trial, review_article,
    #        case_report, meta_analysis, database_entry

    title = Column(String(500), nullable=False)
    authors = Column(JSON, default=list)               # list of author strings
    abstract = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)              # AI-generated or manual summary

    # Publication metadata
    publication_date = Column(String(20), nullable=True)  # YYYY-MM-DD
    journal = Column(String(255), nullable=True)
    source_name = Column(String(100), nullable=True)   # PubMed, bioRxiv, ClinicalTrials, etc.

    # Traceable source links — always required
    source_url = Column(Text, nullable=True)
    doi = Column(String(255), nullable=True)
    pmid = Column(String(50), nullable=True)
    pmcid = Column(String(50), nullable=True)        # PubMed Central ID (e.g. PMC1234567)
    nct_id = Column(String(50), nullable=True)         # ClinicalTrials NCT number

    # Relevance to the signal
    relevance_score = Column(Float, default=0.0)       # 0–1
    relevance_explanation = Column(Text, nullable=True)
    supports_mechanism = Column(Boolean, default=False)

    # Demo data flag — clearly label simulated records
    is_demo_data = Column(Boolean, default=True)
    data_source = Column(String(50), default="demo")   # demo, pubmed, biorxiv, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    signal = relationship("RepurposingSignal", back_populates="evidence_items")
