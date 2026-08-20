from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.models.disease import Disease
from app.models.signal import RepurposingSignal
from app.schemas.schemas import DiseaseOut, SignalListItem
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api/diseases", tags=["diseases"])


@router.get("", response_model=List[DiseaseOut])
def list_diseases(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    q = db.query(Disease)
    if search:
        q = q.filter(Disease.name.ilike(f"%{search}%"))
    if category:
        q = q.filter(Disease.category.ilike(f"%{category}%"))
    diseases = q.order_by(Disease.name).all()

    result = []
    for d in diseases:
        sig_count = db.query(RepurposingSignal).filter(
            RepurposingSignal.disease_id == d.id,
            RepurposingSignal.status == "active",
        ).count()
        out = DiseaseOut.model_validate(d)
        out.signal_count = sig_count
        result.append(out)
    return result


@router.get("/{disease_id}", response_model=DiseaseOut)
def get_disease(
    disease_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    disease = db.query(Disease).filter(Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found")
    sig_count = db.query(RepurposingSignal).filter(
        RepurposingSignal.disease_id == disease_id,
        RepurposingSignal.status == "active",
    ).count()
    out = DiseaseOut.model_validate(disease)
    out.signal_count = sig_count
    return out


@router.get("/{disease_id}/signals", response_model=List[SignalListItem])
def get_disease_signals(
    disease_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    disease = db.query(Disease).filter(Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found")

    signals = (
        db.query(RepurposingSignal)
        .options(joinedload(RepurposingSignal.drug), joinedload(RepurposingSignal.disease))
        .filter(RepurposingSignal.disease_id == disease_id, RepurposingSignal.status == "active")
        .order_by(RepurposingSignal.evidence_score.desc())
        .all()
    )
    return [
        SignalListItem(
            id=s.id, title=s.title, drug_id=s.drug_id, disease_id=s.disease_id,
            evidence_score=s.evidence_score, confidence_level=s.confidence_level,
            source_count=s.source_count, status=s.status, is_novel=s.is_novel,
            detected_at=s.detected_at,
            drug_name=s.drug.name if s.drug else None,
            disease_name=s.disease.name if s.disease else None,
            biological_mechanism=s.biological_mechanism,
        )
        for s in signals
    ]
