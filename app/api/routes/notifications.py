from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.utils import normalize_phone
from app.db.session import get_db
from app.models.farmer import Farmer
from app.models.notification import Notification
from app.schemas.notification import MarkAllReadIn, NotificationCreate

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _get_farmer(db: Session, phone: str | None) -> Farmer | None:
    if not phone:
        return None
    return db.query(Farmer).filter(Farmer.phone == normalize_phone(phone)).first()


@router.get("")
def list_notifications(phone: str = Query(...), db: Session = Depends(get_db)):
    farmer = _get_farmer(db, phone)
    if not farmer:
        return []
    notifs = (
        db.query(Notification)
        .filter(Notification.farmer_id == farmer.id)
        .order_by(Notification.created_at.desc())
        .limit(100)
        .all()
    )
    return [n.to_dict() for n in notifs]


@router.post("")
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)):
    farmer = _get_farmer(db, payload.user_phone)
    notif = Notification(
        farmer_id=farmer.id if farmer else None,
        category=payload.category,
        title=payload.title,
        body=payload.body,
        order_id=payload.order_id,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif.to_dict()


@router.put("/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.read = True
    db.commit()
    return {"id": notification_id, "read": True}


@router.post("/read-all")
def mark_all_read(payload: MarkAllReadIn, db: Session = Depends(get_db)):
    farmer = _get_farmer(db, payload.phone)
    if not farmer:
        return {"updated": 0}
    updated = (
        db.query(Notification)
        .filter(Notification.farmer_id == farmer.id, Notification.read == False)  # noqa: E712
        .update({"read": True})
    )
    db.commit()
    return {"updated": updated}
