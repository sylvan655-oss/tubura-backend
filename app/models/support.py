from datetime import datetime
from sqlalchemy import (Column, Integer, String, Text, DateTime, ForeignKey)
from sqlalchemy.orm import relationship
from app.db.session import Base


class SupportTicket(Base):
    """Every customer inquiry lands here as a ticket."""
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True)
    ticket_no = Column(String(20), unique=True, index=True, nullable=False)  # e.g. TKT000042
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    phone = Column(String(20), nullable=True)
    email = Column(String(150), nullable=True)
    subject = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)

    # open | in_progress | resolved | closed
    status = Column(String(20), nullable=False, default="open")

    assigned_admin_id = Column(Integer, ForeignKey("administrators.id"),
                               nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    user = relationship("User")
