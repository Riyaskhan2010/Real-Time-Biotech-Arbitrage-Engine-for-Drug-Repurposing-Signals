from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.schemas import AlertOut
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertOut])
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alerts = (
        db.query(Alert)
        .filter(Alert.user_id == current_user.id, Alert.is_dismissed == False)
        .order_by(Alert.created_at.desc())
        .all()
    )
    return alerts


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    count = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.is_read == False,
        Alert.is_dismissed == False,
    ).count()
    return {"unread_count": count}


@router.patch("/{alert_id}/read")
def mark_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id,
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    return {"status": "ok"}


@router.patch("/{alert_id}/dismiss")
def dismiss_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id,
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_dismissed = True
    db.commit()
    return {"status": "ok"}


@router.patch("/mark-all-read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"status": "ok"}
