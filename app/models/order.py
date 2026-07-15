from datetime import datetime
from sqlalchemy import (Column, Integer, String, Text, Float, DateTime,
                        ForeignKey)
from sqlalchemy.orm import relationship
from app.db.session import Base


class Order(Base):
    """
    A customer order. The delivery address is SNAPSHOTTED onto the order at
    checkout (copied from the user's default or the one-time address they
    typed), so editing the profile later never changes past orders.
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    ref = Column(String(20), unique=True, index=True, nullable=False)  # e.g. TUB240391
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # pending | confirmed | preparing | ready | delivered | cancelled
    status = Column(String(20), nullable=False, default="pending")
    fulfillment = Column(String(12), nullable=False, default="delivery")  # delivery | pickup

    subtotal = Column(Float, nullable=False, default=0)
    delivery_fee = Column(Float, nullable=False, default=0)
    tax = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False, default=0)

    # ── Delivery address snapshot ─────────────────────────────────────────
    province = Column(String(60), nullable=True)
    district = Column(String(60), nullable=True)
    sector = Column(String(60), nullable=True)
    cell = Column(String(60), nullable=True)
    village = Column(String(60), nullable=True)
    street = Column(String(120), nullable=True)
    landmark = Column(String(200), nullable=True)   # for the courier
    latitude = Column(Float, nullable=True)          # only if "Use Current Location"
    longitude = Column(Float, nullable=True)

    assigned_admin_id = Column(Integer, ForeignKey("administrators.id"),
                               nullable=True)
    note = Column(Text, nullable=True)               # internal admin notes

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    user = relationship("User")
    items = relationship("OrderItem", back_populates="order",
                         cascade="all, delete-orphan")


class OrderItem(Base):
    """
    One product line inside an order. Name, unit and price are snapshots of
    the product AT PURCHASE TIME (prices may change later; old orders must
    still show what was actually paid).

    retailer_id is the supplier the system assigned for this line — the
    nearest active retailer that had enough quantity. Admins can reassign
    it from the dashboard.
    """
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    retailer_id = Column(Integer, ForeignKey("retailers.id"), nullable=True)

    name = Column(String(200), nullable=False)   # snapshot
    unit = Column(String(100), nullable=True)    # snapshot
    price = Column(Float, nullable=False)        # snapshot (RWF, at purchase)
    qty = Column(Integer, nullable=False)
    img = Column(String(255), nullable=True)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    retailer = relationship("Retailer")
