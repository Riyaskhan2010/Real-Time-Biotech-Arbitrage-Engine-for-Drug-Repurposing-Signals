from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Alert(Base):
    """
    Research alert — notifies a researcher when new evidence appears for a
    monitored drug or disease.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    alert_type = Column(String(50), nullable=False)    # new_signal, new_evidence, score_change
    entity_type = Column(String(20), nullable=False)   # drug, disease, signal
    entity_id = Column(Integer, nullable=False)
    entity_name = Column(String(255), nullable=False)  # denormalized for fast display

    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=True)

    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)

    extra_data = Column(JSON, default=dict)           # renamed from 'metadata' (reserved by SQLAlchemy)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="alerts")
