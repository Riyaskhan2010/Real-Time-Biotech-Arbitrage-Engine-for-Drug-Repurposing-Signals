from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class ResearchSource(Base):
    """
    Represents an ingested research data source (paper, trial record, preprint).
    source_type + source_id forms a unique key for deduplication.
    """
    __tablename__ = "research_sources"
    __table_args__ = (
        UniqueConstraint("source_type", "source_id", name="uq_source_type_source_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    source_type = Column(String(50), nullable=False)
    # Types: pubmed, biorxiv, medrxiv, clinicaltrials, manual, demo

    # Unique identifier within the source — used for deduplication
    # e.g. PMID for PubMed, DOI for bioRxiv, NCT number for ClinicalTrials
    source_id = Column(String(255), nullable=True, index=True)

    abstract = Column(Text, nullable=True)
    authors = Column(JSON, default=list)
    publication_date = Column(String(20), nullable=True)
    journal = Column(String(255), nullable=True)

    # Identifiers
    doi = Column(String(255), nullable=True)
    pmid = Column(String(50), nullable=True)
    nct_id = Column(String(50), nullable=True)
    source_url = Column(Text, nullable=True)

    # Extracted entities (populated by entity extraction layer)
    extracted_drugs = Column(JSON, default=list)
    extracted_diseases = Column(JSON, default=list)
    extracted_mechanisms = Column(JSON, default=list)
    extracted_targets = Column(JSON, default=list)

    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_notes = Column(Text, nullable=True)

    # Data provenance flag
    is_demo_data = Column(Boolean, default=False)   # False = live ingested, True = seeded demo

    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
