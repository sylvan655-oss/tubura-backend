import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import (User, Product, Order, OrderItem, PreOrder,
                        Notification)
from app.core.config import settings
from app.services.assignment import allocate, closeness_score

def _delivery_fee(addr: dict, retailers: list, fulfillment: str) -> float:
    """Location-based flat fee: charged once per order, by the FARTHEST
    retailer that has to ship (same district < same province < other)."""
    if fulfillment == "pickup" or not retailers:
        return 0.0
    # tier per retailer: 1 = same district, 2 = same province, 3 = farther
    tiers = [(1 if closeness_score(r, addr) >= 2 else
              (2 if closeness_score(r, addr) == 1 else 3)) for r in retailers]
    worst = max(tiers)
    return float({1: settings.DELIVERY_FEE_SAME_DISTRICT,
                  2: settings.DELIVERY_FEE_SAME_PROVINCE,
                  3: settings.DELIVERY_FEE_OTHER}[worst])

from app.services.sms import send_sms
from app.api.routes.catalog import stock_totals

router = APIRouter(prefix="/api", tags=["orders"])


def new_ref(db: Session, addr: dict | None = None) -> str:
    """Ref prefix encodes the delivery location: first letters of
    District + Sector + Cell (e.g. Nyagatare/Karangazi/Kamate -> NKK)."""
    prefix = ""
    if addr:
        for part in (addr.get("district"), addr.get("sector"), addr.get("cell")):
            ch = (part or "").strip()[:1].upper()
            if ch.isalpha():
                prefix += ch
    if len(prefix) != 3:
        prefix = "TUB"
    while True:
        ref = prefix + "".join(random.choices("0123456789", k=6))
        if not db.query(Order).filter(Order.ref == ref).first():
            return ref


class ItemIn(BaseModel):
    product_id: int
    qty: int                 # buy now (must be available)
    preorder_qty: int = 0    # EXPLICITLY approved by the customer


class AddressIn(BaseModel):
    use_default: bool = True
    save_as_default: bool = False
    province: str | None = None
    district: str | None = None
    sector: str | None = None
    cell: str | None = None
    village: str | None = None
    street: str | None = None
    landmark: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class OrderIn(BaseModel):
    items: list[ItemIn]
    address: AddressIn
    fulfillment: str = "delivery"      # delivery | pickup


def order_json(o: Order) -> dict:
    return {
        "id": o.id, "ref": o.ref, "status": o.status,
        "fulfillment": o.fulfillment or "delivery",
        "subtotal": o.subtotal, "delivery_fee": o.delivery_fee,
        "tax": o.tax, "total": o.total,
        "address": {"province": o.province, "district": o.district,
                    "sector": o.sector, "cell": o.cell,
                    "village": o.village, "street": o.street,
                    "landmark": o.landmark},
        "created_at": o.created_at.isoformat(),
        "items": [{
            "id": i.id, "product_id": i.product_id, "name": i.name,
            "unit": i.unit, "price": i.price, "qty": i.qty, "img": i.img,
            "retailer": i.retailer.name if i.retailer else None,
            "retailer_district": i.retailer.district if i.retailer else None,
        } for i in o.items],
    }


@router.post("/orders")
def create_order(body: OrderIn, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    if not body.items:
        raise HTTPException(400, "Cart is empty")

    # ── Resolve the delivery address ──────────────────────────────────────
    a = body.address
    if a.use_default:
        addr = dict(province=user.province, district=user.district,
                    sector=user.sector, cell=user.cell, village=user.village,
                    street=a.street or user.street,
                    landmark=a.landmark or user.landmark,
                    latitude=a.latitude, longitude=a.longitude)
    else:
        if not (a.province and a.district and a.sector):
            raise HTTPException(400, "Delivery address is incomplete")
        addr = dict(province=a.province, district=a.district,
                    sector=a.sector, cell=a.cell, village=a.village,
                    street=a.street, landmark=a.landmark,
                    latitude=a.latitude, longitude=a.longitude)
        if a.save_as_default:
            for f in ("province", "district", "sector", "cell", "village",
                      "street", "landmark"):
                setattr(user, f, addr[f])

    # ── PASS 1: validate availability. NEVER decide for the customer. ─────
    # If any "buy now" quantity exceeds current stock, refuse the whole
    # order and report exactly what IS available, so the frontend can ask
    # the customer whether they want to pre-order the remainder.
    products: dict[int, Product] = {}
    shortages = []
    for item in body.items:
        if item.qty < 0 or item.preorder_qty < 0:
            raise HTTPException(400, "Quantities cannot be negative")
        if item.qty == 0 and item.preorder_qty == 0:
            continue
        product = db.get(Product, item.product_id)
        if not product or product.status != "active":
            raise HTTPException(400, f"Product {item.product_id} unavailable")
        products[item.product_id] = product
        available = stock_totals(db, [product.id]).get(product.id, 0)
        if item.qty > available:
            shortages.append({"product_id": product.id,
                              "product": product.name_en,
                              "requested": item.qty,
                              "available": available})
    if shortages:
        # 409 Conflict: nothing was created; customer must decide.
        raise HTTPException(
            status_code=409,
            detail={"error": "insufficient_stock", "items": shortages})

    # ── PASS 2: create the order + customer-approved pre-orders ───────────
    fulfillment = body.fulfillment if body.fulfillment in ("delivery", "pickup") else "delivery"
    order = Order(ref=new_ref(db, addr), user_id=user.id, status="confirmed",
                  fulfillment=fulfillment, **addr)
    db.add(order)
    db.flush()

    subtotal = 0.0
    preorders_created = []
    used_retailers = {}

    for item in body.items:
        product = products.get(item.product_id)
        if not product:
            continue

        if item.qty > 0:
            allocation, shortfall = allocate(db, product.id, item.qty, addr)
            if shortfall > 0:
                # stock changed between pass 1 and now (very rare race)
                db.rollback()
                raise HTTPException(
                    status_code=409,
                    detail={"error": "insufficient_stock",
                            "items": [{"product_id": product.id,
                                       "product": product.name_en,
                                       "requested": item.qty,
                                       "available": item.qty - shortfall}]})
            for stock_row, take in allocation:
                used_retailers[stock_row.retailer_id] = stock_row.retailer
                db.add(OrderItem(order_id=order.id, product_id=product.id,
                                 retailer_id=stock_row.retailer_id,
                                 name=product.name_en, unit=product.unit_en,
                                 price=product.price, qty=take,
                                 img=product.img))
                stock_row.quantity -= take        # decrement stock now
                subtotal += product.price * take

        if item.preorder_qty > 0:
            # Only because the customer explicitly chose it.
            totals = stock_totals(db, [product.id])
            db.add(PreOrder(user_id=user.id, product_id=product.id,
                            product_name=product.name_en,
                            requested_qty=item.preorder_qty,
                            stock_at_request=totals.get(product.id, 0),
                            status="received"))
            preorders_created.append({"product": product.name_en,
                                      "qty": item.preorder_qty})

    if subtotal == 0 and not preorders_created:
        raise HTTPException(400, "Nothing could be ordered")

    if subtotal == 0:
        # Pre-orders only, no purchasable items: don't keep an empty order
        db.delete(order)
        db.commit()
        return {"order": None, "preorders_created": preorders_created}

    fee = _delivery_fee(addr, [r for r in used_retailers.values() if r], fulfillment)
    tax = round(subtotal * settings.TAX_RATE)
    order.subtotal = subtotal
    order.delivery_fee = fee
    order.tax = tax
    order.total = subtotal + tax + fee

    db.add(Notification(user_id=user.id, type="order",
                        title="Order received",
                        body=f"Order #{order.ref} received — "
                             f"{int(order.total):,} RWF. We will confirm it shortly.",
                        order_ref=order.ref))
    db.commit()
    db.refresh(order)

    send_sms(user.phone, f"Tubura: order #{order.ref} received. "
                         f"Total {int(order.total):,} RWF.")

    result = order_json(order)
    result["preorders_created"] = preorders_created
    return result


@router.get("/orders")
def my_orders(user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    orders = (db.query(Order).filter(Order.user_id == user.id)
                .order_by(Order.id.desc()).all())
    return [order_json(o) for o in orders]


@router.get("/orders/{ref}")
def get_order(ref: str, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.ref == ref,
                               Order.user_id == user.id).first()
    if not o:
        raise HTTPException(404, "Order not found")
    return order_json(o)


@router.post("/orders/{ref}/cancel")
def cancel_order(ref: str, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.ref == ref,
                               Order.user_id == user.id).first()
    if not o:
        raise HTTPException(404, "Order not found")
    if o.status not in ("pending", "confirmed"):
        raise HTTPException(400, f"Cannot cancel an order that is {o.status}")

    # Restore stock to the retailers it was taken from
    from app.models import RetailerStock
    for item in o.items:
        if item.retailer_id and item.product_id:
            row = (db.query(RetailerStock)
                     .filter_by(retailer_id=item.retailer_id,
                                product_id=item.product_id).first())
            if row:
                row.quantity += item.qty
    o.status = "cancelled"
    o.updated_at = datetime.utcnow()
    db.add(Notification(user_id=user.id, type="order",
                        title="Order cancelled",
                        body=f"Order #{o.ref} has been cancelled.",
                        order_ref=o.ref))
    db.commit()
    return {"ok": True, "status": o.status}


@router.post("/orders/quote")
def quote_order(body: OrderIn, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """Dry-run: closest retailer(s), delivery fee, tax and total — creates NOTHING."""
    if not body.items:
        raise HTTPException(400, "Cart is empty")
    a = body.address
    if a.use_default:
        addr = dict(province=user.province, district=user.district,
                    sector=user.sector, cell=user.cell, village=user.village)
    else:
        if not (a.province and a.district and a.sector):
            raise HTTPException(400, "Address is incomplete")
        addr = dict(province=a.province, district=a.district,
                    sector=a.sector, cell=a.cell, village=a.village)
    fulfillment = body.fulfillment if body.fulfillment in ("delivery", "pickup") else "delivery"

    shortages, lines, retailers = [], [], {}
    subtotal = 0.0
    for item in body.items:
        if item.qty <= 0:
            continue
        product = db.get(Product, item.product_id)
        if not product or product.status != "active":
            raise HTTPException(400, f"Product {item.product_id} unavailable")
        allocation, shortfall = allocate(db, product.id, item.qty, addr)
        if shortfall > 0:
            shortages.append({"product_id": product.id, "product": product.name_en,
                              "requested": item.qty,
                              "available": item.qty - shortfall})
            continue
        for stock_row, take in allocation:
            r = stock_row.retailer
            retailers[r.id] = r
            lines.append({"product_id": product.id, "product": product.name_en,
                          "qty": take, "retailer_id": r.id, "retailer": r.name})
            subtotal += product.price * take
    if shortages:
        raise HTTPException(status_code=409,
                            detail={"error": "insufficient_stock", "items": shortages})
    if subtotal == 0:
        raise HTTPException(400, "Nothing to quote")

    fee = _delivery_fee(addr, list(retailers.values()), fulfillment)
    tax = round(subtotal * settings.TAX_RATE)
    return {
        "fulfillment": fulfillment,
        "retailers": [{
            "id": r.id, "name": r.name, "phone": r.phone,
            "province": r.province, "district": r.district,
            "sector": r.sector, "cell": r.cell, "village": r.village,
            "latitude": r.latitude, "longitude": r.longitude,
        } for r in retailers.values()],
        "lines": lines,
        "subtotal": subtotal, "delivery_fee": fee, "tax": tax,
        "total": subtotal + tax + fee,
    }
