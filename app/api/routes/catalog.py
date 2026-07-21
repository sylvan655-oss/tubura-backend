from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import (Category, Product, RetailerStock, Retailer,
                        PreOrder, Order)

router = APIRouter(prefix="/api", tags=["catalog"])

LANGS = ("en", "rw", "fr")


def pick(obj, base: str, lang: str) -> str:
    lang = lang if lang in LANGS else "en"
    return getattr(obj, f"{base}_{lang}")


# Order statuses that still owe goods to a pre-order customer. Once an
# order is delivered/received/cancelled the goods have physically left
# (or were released), so they stop being counted as committed.
OPEN_ORDER_STATUSES = ("confirmed", "preparing", "ready")


def committed_totals(db: Session, product_ids: list[int]) -> dict[int, int]:
    """
    Units already promised to pre-order customers, per product.

    Counted when a pre-order is approved & ready to buy but not yet bought,
    AND while the resulting order is still open. Approval does NOT require
    the shop to hold the stock yet — Tubura commits the customer first and
    sources the goods afterwards — so these units are simply subtracted
    from what everyone else can see and buy.
    """
    if not product_ids:
        return {}
    rows = (db.query(PreOrder.product_id, PreOrder.reserved_qty,
                     PreOrder.status, PreOrder.converted_order_id)
              .filter(PreOrder.product_id.in_(product_ids),
                      PreOrder.reserved_qty.isnot(None)).all())
    open_order_ids = set()
    order_ids = [r[3] for r in rows if r[3]]
    if order_ids:
        open_order_ids = {o.id for o in db.query(Order)
                          .filter(Order.id.in_(order_ids),
                                  Order.status.in_(OPEN_ORDER_STATUSES)).all()}
    out: dict[int, int] = {}
    for pid, qty, status, order_id in rows:
        if order_id:
            counts = order_id in open_order_ids
        else:
            counts = status == "ready"
        if counts:
            out[pid] = out.get(pid, 0) + int(qty or 0)
    return out


def shop_totals(db: Session, product_ids: list[int]) -> dict[int, int]:
    """Raw quantity sitting in ACTIVE retailers' shops, per product."""
    if not product_ids:
        return {}
    rows = (db.query(RetailerStock.product_id,
                     func.coalesce(func.sum(RetailerStock.quantity), 0))
              .join(Retailer)
              .filter(RetailerStock.product_id.in_(product_ids),
                      Retailer.is_active.is_(True))
              .group_by(RetailerStock.product_id).all())
    return {pid: int(total) for pid, total in rows}


def stock_totals(db: Session, product_ids: list[int]) -> dict[int, int]:
    """
    What is actually available to buy: shop stock minus units already
    committed to pre-order customers. Never negative.
    """
    shop = shop_totals(db, product_ids)
    held = committed_totals(db, product_ids)
    return {pid: max(0, qty - held.get(pid, 0)) for pid, qty in shop.items()}


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
