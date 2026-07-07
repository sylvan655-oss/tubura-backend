from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def list_products(
    lang: str = Query(default="en"),
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(Product)
    if category:
        q = q.filter(Product.category_key == category)
    products = q.order_by(Product.id).all()
    return [p.to_dict(lang) for p in products]


@router.get("/{product_id}")
def get_product(product_id: int, lang: str = Query(default="en"), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.to_dict(lang)
