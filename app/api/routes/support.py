from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.utils import normalize_phone
from app.db.session import get_db
from app.models.farmer import Farmer
from app.models.support import SupportRequest
from app.schemas.support import SupportRequestIn

router = APIRouter(tags=["support"])


@router.post("/api/support-requests")
def create_support_request(payload: SupportRequestIn, db: Session = Depends(get_db)):
    req = SupportRequest(
        phone=normalize_phone(payload.phone) if payload.phone else None,
        email=payload.email,
        message=payload.message,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return {"id": req.id, "received": True}


@router.delete("/api/users/{phone}")
def delete_user(phone: str, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.phone == normalize_phone(phone)).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    db.delete(farmer)
    db.commit()
    return {"deleted": True}
