import random
from datetime import datetime, timedelta, date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import (hash_password, verify_password, create_token,
                               generate_otp)
from app.db.session import get_db
from app.models import User, OTP
from app.services.sms import send_sms

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _gen_customer_code(db: Session, district: str | None) -> str:
    """District prefix + random number, guaranteed unique (e.g. NYA-48291)."""
    prefix = ''.join(ch for ch in (district or '')[:3] if ch.isalpha()).upper() or 'TBR'
    for _ in range(25):
        code = f"{prefix}-{random.randint(10000, 99999)}"
        if not db.query(User).filter(User.customer_code == code).first():
            return code
    return f"{prefix}-{random.randint(100000, 999999)}"


def _ensure_code(db: Session, u: User) -> None:
    """Older accounts (created before codes existed) get one on next contact."""
    if not u.customer_code:
        u.customer_code = _gen_customer_code(db, u.district)
        db.commit()


def _profile(u: User) -> dict:
    return {
        "id": u.id, "customer_code": u.customer_code,
        "phone": u.phone, "name": u.name, "email": u.email,
        "customer_type": u.customer_type,
        "province": u.province, "district": u.district, "sector": u.sector,
        "cell": u.cell, "village": u.village,
        "street": u.street, "landmark": u.landmark,
        "gender": u.gender, "dob": u.dob.isoformat() if u.dob else None,
        "language": u.language,
    }


class PhoneIn(BaseModel):
    phone: str


@router.post("/request-otp")
def request_otp(body: PhoneIn, db: Session = Depends(get_db)):
    code = generate_otp()
    db.add(OTP(phone=body.phone, code=code,
               expires_at=datetime.utcnow() + timedelta(minutes=10)))
    db.commit()
    send_sms(body.phone, f"Your Tubura verification code is {code}. "
                         f"It expires in 10 minutes.")
    return {"ok": True}


class VerifyIn(BaseModel):
    phone: str
    code: str


@router.post("/verify-otp")
def verify_otp(body: VerifyIn, db: Session = Depends(get_db)):
    otp = (db.query(OTP)
             .filter(OTP.phone == body.phone, OTP.code == body.code,
                     OTP.expires_at > datetime.utcnow())
             .order_by(OTP.id.desc()).first())
    if not otp:
        raise HTTPException(400, "Invalid or expired code")
    otp.verified = True
    db.commit()
    return {"ok": True, "phone": body.phone}


class SignupIn(BaseModel):
    phone: str
    name: str
    password: str
    customer_type: str | None = None
    gender: str | None = None
    dob: str | None = None            # "YYYY-MM-DD"
    language: str | None = None
    email: str | None = None
    province: str | None = None
    district: str | None = None
    sector: str | None = None
    cell: str | None = None
    village: str | None = None
    street: str | None = None
    landmark: str | None = None


@router.post("/signup")
def signup(body: SignupIn, db: Session = Depends(get_db)):
    verified = (db.query(OTP)
                  .filter(OTP.phone == body.phone, OTP.verified.is_(True),
                          OTP.created_at > datetime.utcnow() - timedelta(hours=1))
                  .first())
    if not verified:
        raise HTTPException(400, "Phone not verified. Request an OTP first.")
    if db.query(User).filter(User.phone == body.phone).first():
        raise HTTPException(400, "An account with this phone already exists")
    if len(body.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    dob_val = None
    if body.dob:
        try:
            dob_val = date.fromisoformat(body.dob)
        except ValueError:
            dob_val = None
    user = User(phone=body.phone, name=body.name,
                password_hash=hash_password(body.password),
                customer_type=body.customer_type, email=body.email,
                gender=body.gender, dob=dob_val, language=body.language,
                province=body.province, district=body.district,
                sector=body.sector, cell=body.cell, village=body.village,
                street=body.street, landmark=body.landmark)
    user.customer_code = _gen_customer_code(db, body.district)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": create_token(user.id, "user"), **_profile(user)}


class LoginIn(BaseModel):
    phone: str
    password: str


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == body.phone).first()
    if not user or not verify_password(body.password, user.password_hash or ""):
        raise HTTPException(401, "Wrong phone number or password")
    if not user.is_active:
        raise HTTPException(403, "This account has been disabled")
    _ensure_code(db, user)
    return {"token": create_token(user.id, "user"), **_profile(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _profile(user)


class ProfileUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    province: str | None = None
    district: str | None = None
    sector: str | None = None
    cell: str | None = None
    village: str | None = None
    street: str | None = None
    landmark: str | None = None


@router.put("/me")
def update_me(body: ProfileUpdate, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    return _profile(user)


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


@router.post("/change-password")
def change_password(body: ChangePasswordIn, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(body.old_password, user.password_hash or ""):
        raise HTTPException(400, "Current password is wrong")
    if len(body.new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"ok": True}


@router.post("/forgot-otp")
def forgot_otp(body: PhoneIn, db: Session = Depends(get_db)):
    """Send a reset code — only for phones that actually have an account."""
    user = db.query(User).filter(User.phone == body.phone).first()
    if not user:
        raise HTTPException(404, "No account found with this phone number")
    code = generate_otp()
    db.add(OTP(phone=body.phone, code=code,
               expires_at=datetime.utcnow() + timedelta(minutes=10)))
    db.commit()
    send_sms(body.phone, f"Your Tubura password reset code is {code}. "
                         f"It expires in 10 minutes.")
    return {"ok": True}


class ResetPasswordIn(BaseModel):
    phone: str
    code: str
    new_password: str


@router.post("/reset-password")
def reset_password(body: ResetPasswordIn, db: Session = Depends(get_db)):
    otp = (db.query(OTP)
             .filter(OTP.phone == body.phone, OTP.code == body.code,
                     OTP.expires_at > datetime.utcnow())
             .order_by(OTP.id.desc()).first())
    if not otp:
        raise HTTPException(400, "Invalid or expired code")
    user = db.query(User).filter(User.phone == body.phone).first()
    if not user:
        raise HTTPException(404, "No account found with this phone number")
    if len(body.new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    user.password_hash = hash_password(body.new_password)
    db.delete(otp)          # single-use
    db.commit()
    return {"ok": True}
