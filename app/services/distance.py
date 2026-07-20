"""
Distance service — retailer -> customer village road distance in km.

Resolution ladder (never fails for any dropdown path):
  1. exact village centroid          (14,792 of 14,842 paths)
  2. same-named village in sector    (16 paths — cell reassignments)
  3. cell average                    (34 paths)
  4. sector average                  (safety net)

Distance ladder:
  1. cached value in delivery_distances table   (no internet, instant)
  2. OpenRouteService road distance             (real roads, cached forever)
  3. haversine x 1.4                            (offline fallback, cached as such)

Data: app/data/villages.json — built from WASAC boundary data (c) WASAC Ltd, CC-BY 4.0.
"""
import difflib
import json
import os
import re

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import DeliveryDistance
from app.services.assignment import haversine_km

VILLAGES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "villages.json")
HAVERSINE_ROAD_FACTOR = 1.4          # Rwanda's hills: roads ~40% longer than straight line
ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

_index = None                        # lazy-loaded nested dict


def _norm(s: str) -> str:
    """lowercase, strip punctuation/spaces, r/l interchange (Kinyarwanda)."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower()).replace("l", "r")


def _load_index():
    global _index
    if _index is not None:
        return _index
    with open(VILLAGES_PATH, encoding="utf-8") as f:
        villages = json.load(f)
    idx = {}
    for v in villages:
        (idx.setdefault(_norm(v["province"]), {})
            .setdefault(_norm(v["district"]), {})
            .setdefault(_norm(v["sector"]), {})
            .setdefault(_norm(v["cell"]), {}))[_norm(v["village"])] = (v["lat"], v["lng"])
    _index = idx
    return idx


def _fuzzy(key, keys):
    """Exact match, else closest name (handles 1-2 letter spelling drift)."""
    if key in keys:
        return key
    m = difflib.get_close_matches(key, list(keys), n=1, cutoff=0.75)
    return m[0] if m else None


def resolve_village(addr: dict):
    """addr with province/district/sector/cell/village -> (lat, lng) or None."""
    idx = _load_index()
    p = _fuzzy(_norm(addr.get("province")), idx.keys())
    if not p:
        return None
    d = _fuzzy(_norm(addr.get("district")), idx[p].keys())
    if not d:
        return None
    s = _fuzzy(_norm(addr.get("sector")), idx[p][d].keys())
    if not s:
        return None
    c = _fuzzy(_norm(addr.get("cell")), idx[p][d][s].keys())
    vnorm = _norm(addr.get("village"))
    if c:
        vkey = _fuzzy(vnorm, idx[p][d][s][c].keys())
        if vkey:
            return idx[p][d][s][c][vkey]
    for vs in idx[p][d][s].values():                      # village name anywhere in sector
        vkey = _fuzzy(vnorm, vs.keys())
        if vkey:
            return vs[vkey]
    if c:                                                 # cell average
        pts = list(idx[p][d][s][c].values())
        return (sum(x[0] for x in pts) / len(pts), sum(x[1] for x in pts) / len(pts))
    pts = [pt for vs in idx[p][d][s].values() for pt in vs.values()]   # sector average
    return (sum(x[0] for x in pts) / len(pts), sum(x[1] for x in pts) / len(pts))


def _village_key(addr: dict) -> str:
    return "|".join(_norm(addr.get(k)) for k in
                    ("province", "district", "sector", "cell", "village"))


def _ors_km(lat1, lng1, lat2, lng2):
    """Road distance via OpenRouteService. Returns km or None on any failure."""
    if not settings.ORS_API_KEY:
        return None
    try:
        r = httpx.get(ORS_URL, params={
            "api_key": settings.ORS_API_KEY,
            "start": f"{lng1},{lat1}",          # ORS wants lng,lat order!
            "end": f"{lng2},{lat2}",
        }, timeout=8.0)
        r.raise_for_status()
        meters = r.json()["features"][0]["properties"]["summary"]["distance"]
        return meters / 1000.0
    except Exception:
        return None


def road_km(db: Session, retailer, addr: dict):
    """
    Returns (km, method) or None when distance can't be computed
    (retailer has no coordinates yet). method is 'ors' or 'haversine'.
    """
    if retailer.latitude is None or retailer.longitude is None:
        return None
    point = resolve_village(addr)
    if point is None:
        return None
    vlat, vlng = point
    key = _village_key(addr)

    cached = (db.query(DeliveryDistance)
                .filter(DeliveryDistance.retailer_id == retailer.id,
                        DeliveryDistance.village_key == key)
                .first())
    if cached:
        return cached.km, cached.method

    km = _ors_km(retailer.latitude, retailer.longitude, vlat, vlng)
    method = "ors"
    if km is None:
        km = haversine_km(retailer.latitude, retailer.longitude,
                          vlat, vlng) * HAVERSINE_ROAD_FACTOR
        method = "haversine"

    db.add(DeliveryDistance(retailer_id=retailer.id, village_key=key,
                            km=round(km, 2), method=method))
    db.commit()
    return round(km, 2), method


def fee_for_km(km: float) -> int:
    """
    Map km to RWF using settings.DELIVERY_BANDS, e.g. "5:1000,15:2000,40:3500"
    means: up to 5km -> 1000, up to 15km -> 2000, up to 40km -> 3500.
    Beyond the last band -> settings.DELIVERY_FEE_BEYOND.
    """
    for part in settings.DELIVERY_BANDS.split(","):
        limit, fee = part.split(":")
        if km <= float(limit):
            return int(fee)
    return int(settings.DELIVERY_FEE_BEYOND)
