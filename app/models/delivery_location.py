from sqlalchemy import Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DeliveryLocation(Base):
    __tablename__ = "delivery_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), nullable=True)

    name: Mapped[str] = mapped_column(String(80))
    icon: Mapped[str] = mapped_column(String(40), default="pin")

    province: Mapped[str] = mapped_column(String(60), nullable=True)
    district: Mapped[str] = mapped_column(String(60), nullable=True)
    sector: Mapped[str] = mapped_column(String(60), nullable=True)
    cell: Mapped[str] = mapped_column(String(60), nullable=True)
    village: Mapped[str] = mapped_column(String(60), nullable=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)

    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    farmer = relationship("Farmer", back_populates="delivery_locations")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "province": self.province,
            "district": self.district,
            "sector": self.sector,
            "cell": self.cell,
            "village": self.village,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "default": self.is_default,
        }
