from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.models.evidence import Evidence
from app.models.signal import RepurposingSignal
from app.schemas.schemas import EvidenceOut, EvidenceExplorerItem
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api/evidence", tags=["evidence"])


@router.get("", response_model=List[EvidenceExplorerItem])
def list_evidence(
    evidence_type: Optional[str] = Query(None),
    data_source: Optional[str] = Query(None, description="Filter by source: pubmed, europepmc, uniprot, etc."),
    is_demo: Optional[bool] = Query(None, description="Filter by demo/live: true=demo only, false=live only"),
    search: Optional[str] = Query(None),
    signal_id: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    q = (
        db.query(Evidence)
        .options(
            joinedload(Evidence.signal).joinedload(RepurposingSignal.drug),
            joinedload(Evidence.signal).joinedload(RepurposingSignal.disease),
        )
    )

    if evidence_type:
        q = q.filter(Evidence.evidence_type == evidence_type)
    if signal_id:
        q = q.filter(Evidence.signal_id == signal_id)
    if search:
        q = q.filter(Evidence.title.ilike(f"%{search}%"))
    if data_source:
        q = q.filter(Evidence.data_source == data_source)
    if is_demo is not None:
        q = q.filter(Evidence.is_demo_data == is_demo)

    items = q.order_by(Evidence.publication_date.desc()).offset(offset).limit(limit).all()

    result = []
    for e in items:
        item = EvidenceExplorerItem.model_validate(e)
        if e.signal:
            item.drug_name = e.signal.drug.name if e.signal.drug else None
            item.disease_name = e.signal.disease.name if e.signal.disease else None
            item.signal_title = e.signal.title
        result.append(item)
    return result


@router.get("/sources")
def list_evidence_sources(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Returns distinct data sources that have evidence records in the database.
    Used to populate the source filter in the Evidence Explorer.
    """
    from sqlalchemy import distinct, func
    rows = db.query(
        Evidence.data_source,
        func.count(Evidence.id).label("count"),
    ).group_by(Evidence.data_source).all()

    return [
        {"source": r.data_source or "unknown", "count": r.count}
        for r in rows
        if r.data_source
    ]


@router.get("/{evidence_id}", response_model=EvidenceExplorerItem)
def get_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    e = (
        db.query(Evidence)
        .options(
            joinedload(Evidence.signal).joinedload(RepurposingSignal.drug),
            joinedload(Evidence.signal).joinedload(RepurposingSignal.disease),
        )
        .filter(Evidence.id == evidence_id)
        .first()
    )
    if not e:
        raise HTTPException(status_code=404, detail="Evidence item not found")

    item = EvidenceExplorerItem.model_validate(e)
    if e.signal:
        item.drug_name = e.signal.drug.name if e.signal.drug else None
        item.disease_name = e.signal.disease.name if e.signal.disease else None
        item.signal_title = e.signal.title
    return item
