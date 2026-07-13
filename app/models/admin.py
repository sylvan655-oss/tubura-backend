from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from app.db.session import Base


class Administrator(Base):
    """Staff who manage Tubura through the admin dashboard."""
    __tablename__ = "administrators"

    id = Column(Integer, primary_key=True)
    username = Column(String(60), unique=True, index=True, nullable=False)
    email = Column(String(150), nullable=True)
    password_hash = Column(String(255), nullable=False)

    # superadmin | admin | staff  (superadmin can manage other admins)
    role = Column(String(30), nullable=False, default="admin")

    # Fine-grained permissions, e.g. ["products", "orders", "preorders",
    # "customers", "notifications", "support", "admins"]
    permissions = Column(JSON, nullable=False, default=list)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
