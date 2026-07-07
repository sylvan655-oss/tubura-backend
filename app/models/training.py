from datetime import datetime

from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Training(Base):
    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    title_en: Mapped[str] = mapped_column(String(150))
    title_rw: Mapped[str] = mapped_column(String(150))
    title_fr: Mapped[str] = mapped_column(String(150))

    desc_en: Mapped[str] = mapped_column(Text)
    desc_rw: Mapped[str] = mapped_column(Text)
    desc_fr: Mapped[str] = mapped_column(Text)

    duration_en: Mapped[str] = mapped_column(String(60))
    duration_rw: Mapped[str] = mapped_column(String(60))
    duration_fr: Mapped[str] = mapped_column(String(60))

    icon: Mapped[str] = mapped_column(String(40), default="sprout")
    available: Mapped[bool] = mapped_column(Boolean, default=True)

    bookings = relationship("TrainingBooking", back_populates="training")

    def to_dict(self, lang: str = "en") -> dict:
        lang = lang if lang in ("en", "rw", "fr") else "en"
        return {
            "id": self.id,
            "title": getattr(self, f"title_{lang}"),
            "desc": getattr(self, f"desc_{lang}"),
            "duration": getattr(self, f"duration_{lang}"),
            "icon": self.icon,
            "available": self.available,
        }


class TrainingBooking(Base):
    __tablename__ = "training_bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), nullable=True)
    training_id: Mapped[int] = mapped_column(ForeignKey("trainings.id"))
    user_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    preferred_date: Mapped[str] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | confirmed | done
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    farmer = relationship("Farmer", back_populates="training_bookings")
    training = relationship("Training", back_populates="bookings")
