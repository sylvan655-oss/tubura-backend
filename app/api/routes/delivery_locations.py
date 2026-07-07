from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.utils import normalize_phone
from app.db.session import get_db
from app.models.delivery_location import DeliveryLocation
from app.models.farmer import Farmer
from app.schemas.delivery_location import DeliveryLocationIn, DeliveryLocationUpdate

router = APIRouter(prefix="/api/delivery-locations", tags=["delivery-locations"])


def _get_farmer(db: Session, phone: str | None) -> Farmer | None:
    if not phone:
        return None
    return db.query(Farmer).filter(Farmer.phone == normalize_phone(phone)).first()


@router.get("")
def list_locations(phone: str = Query(...), db: Session = Depends(get_db)):
    farmer = _get_farmer(db, phone)
    if not farmer:
        return []
    locs = (
        db.query(DeliveryLocation)
        .filter(DeliveryLocation.farmer_id == farmer.id)
        .order_by(DeliveryLocation.is_default.desc(), DeliveryLocation.id)
        .all()
    )
    return [l.to_dict() for l in locs]


@router.post("")
def create_location(payload: DeliveryLocationIn, db: Session = Depends(get_db)):
    farmer = _get_farmer(db, payload.user_phone)

    existing_count = 0
    if farmer:
        existing_count = (
            db.query(DeliveryLocation).filter(DeliveryLocation.farmer_id == farmer.id).count()
        )

    loc = DeliveryLocation(
        farmer_id=farmer.id if farmer else None,
        name=payload.name,
        icon=payload.icon or "pin",
        province=payload.province,
        district=payload.district,
        sector=payload.sector,
        cell=payload.cell,
        village=payload.village,
        latitude=payload.latitude,
        longitude=payload.longitude,
        is_default=(existing_count == 0),
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc.to_dict()


@router.put("/{location_id}")
def update_location(location_id: int, payload: DeliveryLocationUpdate, db: Session = Depends(get_db)):
    loc = db.query(DeliveryLocation).filter(DeliveryLocation.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Address not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(loc, field, value)
    db.commit()
    db.refresh(loc)
    return loc.to_dict()


@router.put("/{location_id}/default")
def set_default_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.query(DeliveryLocation).filter(DeliveryLocation.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Address not found")
    db.query(DeliveryLocation).filter(DeliveryLocation.farmer_id == loc.farmer_id).update(
        {"is_default": False}
    )
    loc.is_default = True
    db.commit()
    db.refresh(loc)
    return loc.to_dict()


@router.delete("/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.query(DeliveryLocation).filter(DeliveryLocation.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Address not found")
    was_default = loc.is_default
    farmer_id = loc.farmer_id
    db.delete(loc)
    db.commit()

    if was_default and farmer_id:
        remaining = (
            db.query(DeliveryLocation)
            .filter(DeliveryLocation.farmer_id == farmer_id)
            .order_by(DeliveryLocation.id)
            .first()
        )
        if remaining:
            remaining.is_default = True
            db.commit()

    return {"deleted": True, "id": location_id}
