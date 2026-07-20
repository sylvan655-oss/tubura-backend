from datetime import datetime

from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String,
                        UniqueConstraint)

from app.db.session import Base


class DeliveryDistance(Base):
    """
    Cache of retailer -> village road distances. Villages and roads don't
    move, so a row here is valid forever. method records how it was measured:
    'ors' (real road routing) or 'haversine' (straight-line x 1.4 fallback).
    Deleting a 'haversine' row causes it to be re-measured on next use.
    """
    __tablename__ = "delivery_distances"
    __table_args__ = (
        UniqueConstraint("retailer_id", "village_key",
                         name="uq_delivery_distance_pair"),
    )

    id = Column(Integer, primary_key=True)
    retailer_id = Column(Integer,
                         ForeignKey("retailers.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    village_key = Column(String(200), nullable=False, index=True)
    km = Column(Float, nullable=False)
    method = Column(String(12), nullable=False)   # 'ors' | 'haversine'
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
