from typing import Optional

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.farmer import Farmer


def get_current_farmer(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Farmer:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    phone = decode_access_token(token)
    if not phone:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    farmer = db.query(Farmer).filter(Farmer.phone == phone).first()
    if not farmer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Farmer not found")
    return farmer


def get_optional_farmer(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[Farmer]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    phone = decode_access_token(token)
    if not phone:
        return None
    return db.query(Farmer).filter(Farmer.phone == phone).first()
