from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    icd10_code = Column(String(20), nullable=True)       # ICD-10 code
    category = Column(String(100), nullable=True)        # oncology, neurology, etc.
    description = Column(Text, nullable=True)
    affected_pathways = Column(JSON, default=list)       # relevant biological pathways
    molecular_markers = Column(JSON, default=list)       # key biomarkers
    current_treatments = Column(JSON, default=list)      # list of approved drugs
    unmet_needs = Column(Text, nullable=True)            # known gaps in treatment
    prevalence = Column(String(100), nullable=True)      # estimated prevalence
    mondo_id = Column(String(50), nullable=True)         # extension point: MONDO ontology
    mesh_id = Column(String(50), nullable=True)          # extension point: MeSH ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    signals = relationship("RepurposingSignal", back_populates="disease")
