from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Retailer(Base):
    __tablename__ = "retailers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    district: Mapped[str] = mapped_column(String(60), nullable=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)

    stock_level: Mapped[str] = mapped_column(String(20), default="Medium")  # High | Medium | Low

    orders = relationship("Order", back_populates="retailer")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "district": self.district,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "stock": self.stock_level,
        }
