from math import asin, cos, radians, sin, sqrt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.retailer import Retailer

router = APIRouter(prefix="/api/retailers", tags=["retailers"])


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


@router.get("")
def list_retailers(district: str | None = Query(default=None), db: Session = Depends(get_db)):
    q = db.query(Retailer)
    if district:
        q = q.filter(Retailer.district == district)
    return [r.to_dict() for r in q.order_by(Retailer.id).all()]


@router.get("/nearby")
def nearby_retailers(
    lat: float = Query(...),
    lng: float = Query(...),
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db),
):
    retailers = db.query(Retailer).filter(Retailer.latitude.isnot(None), Retailer.longitude.isnot(None)).all()
    ranked = sorted(
        retailers,
        key=lambda r: _haversine_km(lat, lng, r.latitude, r.longitude),
    )
    out = []
    for r in ranked[:limit]:
        d = r.to_dict()
        d["dist_km"] = round(_haversine_km(lat, lng, r.latitude, r.longitude), 2)
        out.append(d)
    return out
