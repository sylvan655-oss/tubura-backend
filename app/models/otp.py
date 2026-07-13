from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.db.session import Base


class OTP(Base):
    """One-time codes sent by SMS during signup."""
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True)
    phone = Column(String(20), index=True, nullable=False)
    code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
