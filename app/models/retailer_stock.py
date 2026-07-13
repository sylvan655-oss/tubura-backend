from datetime import datetime
from sqlalchemy import (Column, Integer, DateTime, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relationship
from app.db.session import Base


class RetailerStock(Base):
    """
    How many units of one product one retailer currently holds.
    This is the table admins update daily from the dashboard.
    Confirmed orders decrement quantity here.
    """
    __tablename__ = "retailer_stock"
    __table_args__ = (
        UniqueConstraint("retailer_id", "product_id",
                         name="uq_retailer_product"),
    )

    id = Column(Integer, primary_key=True)
    retailer_id = Column(Integer, ForeignKey("retailers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    quantity = Column(Integer, nullable=False, default=0)

    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    retailer = relationship("Retailer", back_populates="stocks")
    product = relationship("Product", back_populates="stocks")
