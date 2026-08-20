from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    generic_name = Column(String(255), nullable=True)
    drug_class = Column(String(255), nullable=True)
    mechanism_of_action = Column(Text, nullable=True)
    approved_indications = Column(JSON, default=list)   # list of disease strings
    molecular_targets = Column(JSON, default=list)      # list of target strings
    pathways = Column(JSON, default=list)               # list of pathway strings
    fda_status = Column(String(100), nullable=True)     # approved, investigational, etc.
    approval_year = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    pubchem_cid = Column(String(50), nullable=True)     # extension point: PubChem ID
    chembl_id = Column(String(50), nullable=True)       # extension point: ChEMBL ID
    atc_code = Column(String(50), nullable=True)        # ATC classification code
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    signals = relationship("RepurposingSignal", back_populates="drug")
