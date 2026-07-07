import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def gen_ref() -> str:
    return "TUB" + uuid.uuid4().hex[:6].upper()


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ref: Mapped[str] = mapped_column(String(20), unique=True, index=True, default=gen_ref)

    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), nullable=True)
    retailer_id: Mapped[int] = mapped_column(ForeignKey("retailers.id"), nullable=True)

    delivery_method: Mapped[str] = mapped_column(String(20), default="pickup")  # pickup | delivery
    speed: Mapped[str] = mapped_column(String(20), nullable=True)  # standard | express
    payment_method: Mapped[str] = mapped_column(String(20), default="mtn_momo")

    subtotal: Mapped[float] = mapped_column(Float, default=0)
    delivery_fee: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float, default=0)

    status: Mapped[str] = mapped_column(
        String(20), default="confirmed"
    )  # confirmed | processing | shipped | delivered | cancelled
    payment_status: Mapped[str] = mapped_column(String(20), default="pending")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    farmer = relationship("Farmer", back_populates="orders")
    retailer = relationship("Retailer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.ref,
            "status": self.status,
            "payment_status": self.payment_status,
            "delivery_method": self.delivery_method,
            "speed": self.speed,
            "payment_method": self.payment_method,
            "subtotal": self.subtotal,
            "delivery_fee": self.delivery_fee,
            "total": self.total,
            "retailer": self.retailer.to_dict() if self.retailer else None,
            "items": [i.to_dict() for i in self.items],
            "date": self.created_at.strftime("%d %b %Y"),
            "time": self.created_at.strftime("%H:%M"),
        }


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    price: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(100), nullable=True)
    img: Mapped[str] = mapped_column(String(255), nullable=True)
    qty: Mapped[int] = mapped_column(Integer, default=1)

    order = relationship("Order", back_populates="items")

    def to_dict(self) -> dict:
        return {
            "id": self.product_id,
            "name": self.name,
            "price": self.price,
            "unit": self.unit,
            "img": self.img,
            "qty": self.qty,
        }
