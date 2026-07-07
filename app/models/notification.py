from datetime import datetime

from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), nullable=True)

    category: Mapped[str] = mapped_column(String(20), default="order")  # order | delivery | promo | feedback
    title: Mapped[str] = mapped_column(String(150))
    body: Mapped[str] = mapped_column(Text)
    order_id: Mapped[str] = mapped_column(String(20), nullable=True)

    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    farmer = relationship("Farmer", back_populates="notifications")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "body": self.body,
            "order_id": self.order_id,
            "read": self.read,
            "createdAt": self.created_at.isoformat(),
        }
