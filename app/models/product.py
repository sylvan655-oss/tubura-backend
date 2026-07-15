from datetime import datetime
from sqlalchemy import (Column, Integer, String, Text, Float, Boolean,
                        DateTime, ForeignKey)
from sqlalchemy.orm import relationship
from app.db.session import Base


class Product(Base):
    """
    A Tubura product sold at a fixed, admin-managed price.

    IMPORTANT: there is NO stock/quantity column here. Stock is held per
    retailer in the retailer_stock table. The quantity shown to a customer
    is the SUM of quantity across all active retailers, and the label
    (In Stock / Limited / Out of Stock) is derived from that sum using
    low_stock_threshold, which the admin sets per product:

        total == 0                  -> Out of Stock
        total <= low_stock_threshold -> Limited
        otherwise                   -> In Stock
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    brand = Column(String(100), nullable=True)

    name_en = Column(String(200), nullable=False)
    name_rw = Column(String(200), nullable=False)
    name_fr = Column(String(200), nullable=False)

    unit_en = Column(String(100), nullable=False)   # e.g. "per 50kg bag"
    unit_rw = Column(String(100), nullable=False)
    unit_fr = Column(String(100), nullable=False)

    description_en = Column(Text, nullable=False)
    description_rw = Column(Text, nullable=False)
    description_fr = Column(Text, nullable=False)

    # Free-text specifications shown on the product page (optional)
    specifications = Column(Text, nullable=True)

    # One-page usage guide shown to customers after purchase (optional)
    guide_en = Column(Text, nullable=True)
    guide_rw = Column(Text, nullable=True)
    guide_fr = Column(Text, nullable=True)
    guide_video = Column(String(300), nullable=True)   # optional video link

    price = Column(Float, nullable=False)           # RWF, fixed nationally

    # Admin sets this once in a while, per product. 50 for seed packs,
    # 3 for sprayers — the admin decides what "low" means for each item.
    low_stock_threshold = Column(Integer, nullable=False, default=10)

    featured = Column(Boolean, nullable=False, default=False)
    # active | hidden   (hidden = not shown in the customer app)
    status = Column(String(20), nullable=False, default="active")

    img = Column(String(255), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    category = relationship("Category")
    stocks = relationship("RetailerStock", back_populates="product",
                          cascade="all, delete-orphan")
