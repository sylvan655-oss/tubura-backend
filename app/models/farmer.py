from datetime import datetime

from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Farmer(Base):
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=True)

    dob: Mapped[str] = mapped_column(String(20), nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    gender: Mapped[str] = mapped_column(String(20), nullable=True)

    province: Mapped[str] = mapped_column(String(60), nullable=True)
    district: Mapped[str] = mapped_column(String(60), nullable=True)
    sector: Mapped[str] = mapped_column(String(60), nullable=True)
    cell: Mapped[str] = mapped_column(String(60), nullable=True)
    village: Mapped[str] = mapped_column(String(60), nullable=True)

    customer_type: Mapped[str] = mapped_column(String(40), nullable=True)
    interests: Mapped[list] = mapped_column(JSON, default=list)
    crops: Mapped[list] = mapped_column(JSON, default=list)

    farmer_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="farmer", cascade="all, delete-orphan")
    delivery_locations = relationship(
        "DeliveryLocation", back_populates="farmer", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification", back_populates="farmer", cascade="all, delete-orphan"
    )
    training_bookings = relationship(
        "TrainingBooking", back_populates="farmer", cascade="all, delete-orphan"
    )
