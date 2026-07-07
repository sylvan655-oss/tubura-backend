from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    generate_farmer_id,
    generate_otp,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.core.utils import district_code, normalize_phone
from app.db.session import get_db
from app.models.farmer import Farmer
from app.models.otp import OTP
from app.schemas.auth import FarmerOut, LoginIn, RequestOTP, SignupIn, TokenOut, VerifyOTP
from app.services.sms import send_otp_sms
from app.api.deps import get_current_farmer

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/request-otp")
def request_otp(payload: RequestOTP, db: Session = Depends(get_db)):
    phone = normalize_phone(payload.phone)
    code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    otp = OTP(phone=phone, code=code, expires_at=expires_at)
    db.add(otp)
    db.commit()

    send_otp_sms(phone, code)
    response = {"message": "OTP sent", "phone": phone}
    if settings.APP_ENV != "production":
        response["debug_code"] = code  # convenient for local testing only
    return response


@router.post("/verify-otp")
def verify_otp(payload: VerifyOTP, db: Session = Depends(get_db)):
    phone = normalize_phone(payload.phone)
    otp = (
        db.query(OTP)
        .filter(OTP.phone == phone, OTP.code == payload.code, OTP.verified == False)  # noqa: E712
        .order_by(OTP.id.desc())
        .first()
    )
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    if otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification code expired")

    otp.verified = True
    db.commit()
    return {"message": "OTP verified", "phone": phone}


@router.post("/signup", response_model=FarmerOut)
def signup(payload: SignupIn, db: Session = Depends(get_db)):
    phone = normalize_phone(payload.phone)
    farmer = db.query(Farmer).filter(Farmer.phone == phone).first()

    if farmer is None:
        farmer = Farmer(phone=phone, name=payload.name)
        db.add(farmer)

    farmer.name = payload.name or farmer.name
    farmer.dob = payload.dob
    farmer.age = payload.age
    farmer.gender = payload.gender
    farmer.province = payload.province
    farmer.district = payload.district
    farmer.sector = payload.sector
    farmer.cell = payload.cell
    farmer.village = payload.village
    farmer.customer_type = payload.customer_type
    farmer.interests = payload.interests
    farmer.crops = payload.crops or payload.interests

    if payload.password:
        farmer.password_hash = hash_password(payload.password)

    if not farmer.farmer_id:
        farmer.farmer_id = generate_farmer_id(district_code(payload.district))

    db.commit()
    db.refresh(farmer)
    return farmer


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    phone = normalize_phone(payload.phone)
    farmer = db.query(Farmer).filter(Farmer.phone == phone).first()
    if not farmer or not verify_password(payload.password, farmer.password_hash or ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect phone or password")

    token = create_access_token(subject=farmer.phone)
    return {"access_token": token, "token_type": "bearer", "farmer": farmer}


@router.get("/me", response_model=FarmerOut)
def me(current_farmer: Farmer = Depends(get_current_farmer)):
    return current_farmer
