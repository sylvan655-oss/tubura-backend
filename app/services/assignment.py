"""
Retailer assignment — the heart of Tubura fulfillment.

Given a delivery address and a wanted quantity of a product, pick the
nearest active retailer(s) that hold stock, by ADMINISTRATIVE closeness:

    same village (within same cell/sector/district/province)  -> score 5
    same cell                                                  -> score 4
    same sector                                                -> score 3
    same district                                              -> score 2
    same province                                              -> score 1
    different province                                         -> score 0

Village/cell names repeat all over Rwanda, so the comparison is
hierarchical: a village only matches if every level above it matches too.

If the order carries GPS coordinates AND retailers have coordinates,
haversine distance breaks ties inside the same score.

If no single retailer can cover the full quantity, the allocation is
SPLIT across retailers greedily (best score first, biggest stock first),
producing one OrderItem per retailer used.
"""
import math

from sqlalchemy.orm import Session

from app.models import Retailer, RetailerStock


def _norm(v: str | None) -> str:
    return (v or "").strip().lower()


def closeness_score(retailer: Retailer, addr: dict) -> int:
    if _norm(retailer.province) != _norm(addr.get("province")) or not _norm(addr.get("province")):
        return 0
    score = 1
    if _norm(retailer.district) == _norm(addr.get("district")) and _norm(addr.get("district")):
        score = 2
        if _norm(retailer.sector) == _norm(addr.get("sector")) and _norm(addr.get("sector")):
            score = 3
            if _norm(retailer.cell) == _norm(addr.get("cell")) and _norm(addr.get("cell")):
                score = 4
                if _norm(retailer.village) == _norm(addr.get("village")) and _norm(addr.get("village")):
                    score = 5
    return score


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = (math.sin(dp / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


def allocate(db: Session, product_id: int, qty: int,
             addr: dict) -> tuple[list[tuple[RetailerStock, int]], int]:
    """
    Returns ([(stock_row, take_qty), ...], shortfall).
    shortfall > 0 means not enough total stock; the caller turns the
    remainder into a PreOrder.
    Does NOT modify quantities — the caller decrements after committing
    to the allocation.
    """
    rows = (db.query(RetailerStock)
              .join(Retailer)
              .filter(RetailerStock.product_id == product_id,
                      RetailerStock.quantity > 0,
                      Retailer.is_active.is_(True))
              .all())

    lat, lng = addr.get("latitude"), addr.get("longitude")

    def sort_key(row: RetailerStock):
        r = row.retailer
        score = closeness_score(r, addr)
        dist = float("inf")
        if (lat is not None and lng is not None
                and r.latitude is not None and r.longitude is not None):
            dist = haversine_km(lat, lng, r.latitude, r.longitude)
        # higher score first, then nearer, then bigger stock
        return (-score, dist, -row.quantity)

    rows.sort(key=sort_key)

    allocation: list[tuple[RetailerStock, int]] = []
    remaining = qty
    for row in rows:
        if remaining <= 0:
            break
        take = min(row.quantity, remaining)
        allocation.append((row, take))
        remaining -= take

    return allocation, remaining
