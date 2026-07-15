from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models import User, Administrator


def _bearer(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(authorization.removeprefix("Bearer ").strip())
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    return payload


def get_current_user(authorization: str | None = Header(None),
                     db: Session = Depends(get_db)) -> User:
    payload = _bearer(authorization)
    if payload.get("role") != "user":
        raise HTTPException(403, "User token required")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(401, "Account not found or disabled")
    return user


def get_current_user_optional(authorization: str | None = Header(None),
                              db: Session = Depends(get_db)) -> User | None:
    if not authorization:
        return None
    try:
        return get_current_user(authorization, db)
    except HTTPException:
        return None


def get_current_admin(authorization: str | None = Header(None),
                      db: Session = Depends(get_db)) -> Administrator:
    payload = _bearer(authorization)
    if payload.get("role") != "admin":
        raise HTTPException(403, "Admin token required")
    admin = db.get(Administrator, int(payload["sub"]))
    if not admin or not admin.is_active:
        raise HTTPException(401, "Admin not found or disabled")
    return admin


def require_superadmin(admin: Administrator = Depends(get_current_admin)) -> Administrator:
    if admin.role != "superadmin":
        raise HTTPException(403, "Superadmin only")
    return admin


def require_perm(perm: str):
    """Route guard: superadmins pass; regular admins need `perm` in their list."""
    def dep(admin: Administrator = Depends(get_current_admin)) -> Administrator:
        if admin.retailer_id and perm != "orders":
            raise HTTPException(403, "Retailer accounts can only access orders")
        if admin.role == "superadmin":
            return admin
        if perm not in (admin.permissions or []):
            raise HTTPException(403, f"You don't have the '{perm}' permission")
        return admin
    return dep


def require_hq(admin: Administrator = Depends(get_current_admin)) -> Administrator:
    """Blocks retailer-linked accounts from HQ-only endpoints."""
    if admin.retailer_id:
        raise HTTPException(403, "Retailer accounts can only access orders")
    return admin
