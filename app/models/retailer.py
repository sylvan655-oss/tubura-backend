from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base


class Retailer(Base):
    """
    A fixed Tubura fulfillment point. Customers never browse retailers —
    the system assigns the nearest stocked retailer to each order item
    after the delivery address is confirmed.

    "Nearest" is decided by administrative closeness to the delivery
    address: same village > same cell > same sector > same district >
    same province. latitude/longitude are optional extras (useful for
    couriers and future true-distance ranking).
    """
    __tablename__ = "retailers"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=True)

    province = Column(String(60), nullable=True)
    district = Column(String(60), nullable=True)
    sector = Column(String(60), nullable=True)
    cell = Column(String(60), nullable=True)
    village = Column(String(60), nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)

    stocks = relationship("RetailerStock", back_populates="retailer",
                          cascade="all, delete-orphan")
