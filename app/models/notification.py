from datetime import datetime
from sqlalchemy import (Column, Integer, String, Text, Boolean, DateTime,
                        ForeignKey, JSON)
from app.db.session import Base


class Notification(Base):
    """
    One table, two uses (kept simple for V1):

    1. PERSONAL notification (user_id set): order updates, replies —
       shows in that customer's inbox with a read flag.
    2. CAMPAIGN (user_id NULL): admin-created announcement banner, push
       notification, promo graphic, seasonal/service announcement —
       targeted via `audience`.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # order | banner | push | promo | seasonal | service
    type = Column(String(20), nullable=False, default="service")

    title = Column(String(150), nullable=False)
    body = Column(Text, nullable=False)
    image = Column(String(255), nullable=True)        # banner image
    button_text = Column(String(60), nullable=True)   # optional button
    button_link = Column(String(255), nullable=True)  # optional link

    # For campaigns: all | selected | individual
    audience = Column(String(20), nullable=False, default="all")
    audience_user_ids = Column(JSON, nullable=True)   # for "selected"

    # draft | scheduled | sent
    send_status = Column(String(20), nullable=False, default="sent")
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    order_ref = Column(String(20), nullable=True)     # link to an order
    read = Column(Boolean, nullable=False, default=False)  # personal only

    created_by_admin_id = Column(Integer, ForeignKey("administrators.id"),
                                 nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
