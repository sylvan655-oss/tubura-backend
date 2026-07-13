from sqlalchemy import Column, Integer, String, Boolean
from app.db.session import Base


class Category(Base):
    """Product categories. Fully admin-managed: add / edit / delete / hide."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name_en = Column(String(80), nullable=False)
    name_rw = Column(String(80), nullable=False)
    name_fr = Column(String(80), nullable=False)

    is_hidden = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
