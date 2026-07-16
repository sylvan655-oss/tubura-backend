from datetime import datetime
from sqlalchemy import (Column, Integer, String, Text, DateTime, ForeignKey)
from sqlalchemy.orm import relationship
from app.db.session import Base


class PreOrder(Base):
    """
    A customer's request for something they couldn't buy right now.
    Created in three situations:
      1. Requested quantity exceeds available stock (product_id set,
         requested_qty = the shortfall).
      2. Product completely out of stock (product_id set).
      3. Product not found in the catalogue (product_id NULL,
         product_name holds what the customer typed).
    """
    __tablename__ = "preorders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)

    # What the customer asked for. For case 3 this is free text; for
    # cases 1-2 it snapshots the product name.
    product_name = Column(String(200), nullable=False)
    requested_qty = Column(Integer, nullable=False, default=1)

    # Total stock across retailers at the moment of the request
    # (shown in the admin table as "Current Stock")
    stock_at_request = Column(Integer, nullable=True)

    # received | under_review | approved | ordered | ready | cancelled
    status = Column(String(20), nullable=False, default="received")

    assigned_admin_id = Column(Integer, ForeignKey("administrators.id"),
                               nullable=True)

    # Set when the admin converts this pre-order into a real order
    converted_order_id = Column(Integer, ForeignKey("orders.id"),
                                nullable=True)

    # C1 reservation: set by HQ when readying the pre-order for the customer
    unit_price = Column(Integer, nullable=True)        # RWF per unit
    reserved_qty = Column(Integer, nullable=True)      # units held for this customer
    fulfiller_id = Column(Integer, ForeignKey("retailers.id"), nullable=True)  # supplying shop
    denied = Column(Integer, nullable=False, default=0)   # 0=not denied, 1=denied

    note = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    user = relationship("User")
    product = relationship("Product")
