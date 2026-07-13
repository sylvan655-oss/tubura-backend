from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date
from app.db.session import Base


class User(Base):
    """A Tubura customer: farmer, homeowner, NGO, school, cooperative, etc."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    customer_code = Column(String(20), unique=True, index=True, nullable=True)  # e.g. NYA-48291
    phone = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    email = Column(String(150), nullable=True)
    password_hash = Column(String(255), nullable=True)

    # What kind of customer this is: farmer, homeowner, ngo, school,
    # cooperative, business, government, individual
    customer_type = Column(String(40), nullable=True)
    gender = Column(String(20), nullable=True)          # male | female | other
    dob = Column(Date, nullable=True)                   # date of birth
    language = Column(String(5), nullable=True)         # en | rw | fr

    # ── Default delivery address (collected at registration) ─────────────
    province = Column(String(60), nullable=True)
    district = Column(String(60), nullable=True)
    sector = Column(String(60), nullable=True)
    cell = Column(String(60), nullable=True)
    village = Column(String(60), nullable=True)
    street = Column(String(120), nullable=True)     # street / house no. (optional)
    landmark = Column(String(200), nullable=True)   # optional, for the courier

    # ── Customer care status (admin-managed) ─────────────────────────────
    # normal | needs_followup | frequent_issues
    care_status = Column(String(30), nullable=False, default="normal")

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
