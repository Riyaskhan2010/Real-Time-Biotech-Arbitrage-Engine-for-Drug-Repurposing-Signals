from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.models.drug import Drug
from app.models.signal import RepurposingSignal
from app.schemas.schemas import DrugOut, SignalListItem
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api/drugs", tags=["drugs"])


@router.get("", response_model=List[DrugOut])
def list_drugs(
    search: Optional[str] = Query(None),
    drug_class: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    q = db.query(Drug)
    if search:
        q = q.filter(Drug.name.ilike(f"%{search}%"))
    if drug_class:
        q = q.filter(Drug.drug_class.ilike(f"%{drug_class}%"))
    drugs = q.order_by(Drug.name).all()

    result = []
    for d in drugs:
        sig_count = db.query(RepurposingSignal).filter(
            RepurposingSignal.drug_id == d.id,
            RepurposingSignal.status == "active",
        ).count()
        out = DrugOut.model_validate(d)
        out.signal_count = sig_count
        result.append(out)
    return result


@router.get("/{drug_id}", response_model=DrugOut)
def get_drug(
    drug_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    drug = db.query(Drug).filter(Drug.id == drug_id).first()
    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")
    sig_count = db.query(RepurposingSignal).filter(
        RepurposingSignal.drug_id == drug_id,
        RepurposingSignal.status == "active",
    ).count()
    out = DrugOut.model_validate(drug)
    out.signal_count = sig_count
    return out


@router.get("/{drug_id}/signals", response_model=List[SignalListItem])
def get_drug_signals(
    drug_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    drug = db.query(Drug).filter(Drug.id == drug_id).first()
    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")

    signals = (
        db.query(RepurposingSignal)
        .options(joinedload(RepurposingSignal.drug), joinedload(RepurposingSignal.disease))
        .filter(RepurposingSignal.drug_id == drug_id, RepurposingSignal.status == "active")
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
