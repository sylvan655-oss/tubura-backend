from sqlalchemy import Integer, String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name_en: Mapped[str] = mapped_column(String(200))
    name_rw: Mapped[str] = mapped_column(String(200))
    name_fr: Mapped[str] = mapped_column(String(200))

    category_key: Mapped[str] = mapped_column(String(40))  # Seeds | Inputs | Trees | CashCrops | Equipment
    category_en: Mapped[str] = mapped_column(String(60))
    category_rw: Mapped[str] = mapped_column(String(60))
    category_fr: Mapped[str] = mapped_column(String(60))

    unit_en: Mapped[str] = mapped_column(String(100))
    unit_rw: Mapped[str] = mapped_column(String(100))
    unit_fr: Mapped[str] = mapped_column(String(100))

    description_en: Mapped[str] = mapped_column(Text)
    description_rw: Mapped[str] = mapped_column(Text)
    description_fr: Mapped[str] = mapped_column(Text)

    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=4.5)
    sold: Mapped[int] = mapped_column(Integer, default=0)
    img: Mapped[str] = mapped_column(String(255), nullable=True)

    def to_dict(self, lang: str = "en") -> dict:
        lang = lang if lang in ("en", "rw", "fr") else "en"
        return {
            "id": self.id,
            "name": getattr(self, f"name_{lang}"),
            "category": getattr(self, f"category_{lang}"),
            "category_key": self.category_key,
            "unit": getattr(self, f"unit_{lang}"),
            "description": getattr(self, f"description_{lang}"),
            "price": self.price,
            "stock": self.stock,
            "rating": self.rating,
            "sold": self.sold,
            "img": self.img,
        }
