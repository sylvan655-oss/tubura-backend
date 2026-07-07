from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.utils import normalize_phone
from app.db.session import get_db
from app.models.farmer import Farmer
from app.models.training import Training, TrainingBooking
from app.schemas.training import TrainingRequestIn

router = APIRouter(tags=["trainings"])


@router.get("/api/trainings")
def list_trainings(lang: str = Query(default="en"), db: Session = Depends(get_db)):
    trainings = db.query(Training).order_by(Training.id).all()
    return [t.to_dict(lang) for t in trainings]


@router.post("/api/training-requests")
def book_training(payload: TrainingRequestIn, db: Session = Depends(get_db)):
    training = db.query(Training).filter(Training.id == payload.training_id).first()
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    if not training.available:
        raise HTTPException(status_code=400, detail="This training session is full")

    farmer = None
    if payload.user_phone:
        farmer = db.query(Farmer).filter(Farmer.phone == normalize_phone(payload.user_phone)).first()

    booking = TrainingBooking(
        farmer_id=farmer.id if farmer else None,
        training_id=training.id,
        user_phone=normalize_phone(payload.user_phone) if payload.user_phone else None,
        preferred_date=payload.preferred_date,
        status="pending",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return {
        "id": booking.id,
        "training_id": training.id,
        "status": booking.status,
        "preferred_date": booking.preferred_date,
    }
