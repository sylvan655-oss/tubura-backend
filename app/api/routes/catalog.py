from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Category, Product, RetailerStock, Retailer

router = APIRouter(prefix="/api", tags=["catalog"])

LANGS = ("en", "rw", "fr")


def pick(obj, base: str, lang: str) -> str:
    lang = lang if lang in LANGS else "en"
    return getattr(obj, f"{base}_{lang}")


def stock_totals(db: Session, product_ids: list[int]) -> dict[int, int]:
    """Total quantity per product across ACTIVE retailers."""
    if not product_ids:
        return {}
    rows = (db.query(RetailerStock.product_id,
                     func.coalesce(func.sum(RetailerStock.quantity), 0))
              .join(Retailer)
              .filter(RetailerStock.product_id.in_(product_ids),
                      Retailer.is_active.is_(True))
              .group_by(RetailerStock.product_id).all())
    return {pid: int(total) for pid, total in rows}


def stock_label(total: int, threshold: int) -> str:
    if total <= 0:
        return "out_of_stock"
    if total <= threshold:
        return "limited"
    return "in_stock"


def product_json(p: Product, total: int, lang: str) -> dict:
    return {
        "id": p.id,
        "name": pick(p, "name", lang),
        "unit": pick(p, "unit", lang),
        "description": pick(p, "description", lang),
        "brand": p.brand,
        "specifications": p.specifications,
        "category_id": p.category_id,
        "category": pick(p.category, "name", lang) if p.category else None,
        "price": p.price,
        "img": p.img,
        "featured": p.featured,
        "stock": total,                                   # exact number
        "stock_label": stock_label(total, p.low_stock_threshold),
        "guide": pick(p, "guide", lang) if p.guide_en else None,
        "guide_video": p.guide_video,
    }


@router.get("/categories")
def list_categories(lang: str = Query("en"), db: Session = Depends(get_db)):
    cats = (db.query(Category).filter(Category.is_hidden.is_(False))
              .order_by(Category.sort_order, Category.id).all())
    return [{"id": c.id, "name": pick(c, "name", lang)} for c in cats]


@router.get("/products")
def list_products(lang: str = Query("en"),
                  category_id: int | None = None,
                  search: str | None = None,
                  featured: bool | None = None,
                  db: Session = Depends(get_db)):
    q = db.query(Product).filter(Product.status == "active")
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if featured is not None:
        q = q.filter(Product.featured.is_(featured))
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(or_(Product.name_en.ilike(like),
                         Product.name_rw.ilike(like),
                         Product.name_fr.ilike(like),
                         Product.brand.ilike(like)))
    products = q.order_by(Product.featured.desc(), Product.id.desc()).all()
    totals = stock_totals(db, [p.id for p in products])
    return [product_json(p, totals.get(p.id, 0), lang) for p in products]


@router.get("/products/{product_id}")
def get_product(product_id: int, lang: str = Query("en"),
                db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p or p.status != "active":
        raise HTTPException(404, "Product not found")
    totals = stock_totals(db, [p.id])
    return product_json(p, totals.get(p.id, 0), lang)
