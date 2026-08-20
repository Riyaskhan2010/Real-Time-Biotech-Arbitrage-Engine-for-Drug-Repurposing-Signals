from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RepurposingSignal(Base):
    """
    A detected drug-repurposing signal linking a drug to a potential new disease indication.
    This is a research prioritization signal, NOT a clinical recommendation.
    """
    __tablename__ = "repurposing_signals"

    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=False)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=False)

    # Core signal metadata
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    biological_mechanism = Column(Text, nullable=True)

    # Scoring — all experimental research-prioritization scores, not clinical probabilities
    evidence_score = Column(Float, default=0.0)       # 0–100 composite score
    confidence_level = Column(String(20), default="low")  # low, medium, high
    source_count = Column(Integer, default=0)

    # Score breakdown factors (stored as JSON for transparency)
    score_breakdown = Column(JSON, default=dict)

    # Signal status
    status = Column(String(50), default="active")     # active, archived, under_review
    is_novel = Column(Boolean, default=True)          # novel vs. known

    # AI explanation fields
    ai_explanation = Column(Text, nullable=True)
    explanation_factors = Column(JSON, default=list)  # list of factor objects

    # Detection metadata
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    data_source = Column(String(100), default="demo")  # demo, live, imported

    # Extension point fields for future integrations
    clinicaltrials_nct = Column(String(50), nullable=True)
    pubmed_pmids = Column(JSON, default=list)

    drug = relationship("Drug", back_populates="signals")
    disease = relationship("Disease", back_populates="signals")
    evidence_items = relationship("Evidence", back_populates="signal")
