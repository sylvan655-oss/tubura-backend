from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.utils import normalize_phone
from app.db.session import get_db
from app.models.farmer import Farmer
from app.models.notification import Notification
from app.models.order import Order, OrderItem
from app.models.retailer import Retailer
from app.schemas.order import OrderCreate
from app.services.payment import request_payment
from app.services.sms import send_order_update_sms
from app.api.deps import get_optional_farmer

router = APIRouter(prefix="/api/orders", tags=["orders"])

DELIVERY_FEES = {"standard": 1500, "express": 3000}


@router.post("")
async def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    farmer = None
    if payload.user_phone:
        phone = normalize_phone(payload.user_phone)
        farmer = db.query(Farmer).filter(Farmer.phone == phone).first()

    retailer = None
    if payload.retailer_id:
        retailer = db.query(Retailer).filter(Retailer.id == payload.retailer_id).first()

    subtotal = sum(item.price * item.qty for item in payload.items)
    fee = 0 if payload.delivery_method == "pickup" else DELIVERY_FEES.get(payload.speed or "standard", 1500)
    total = subtotal + fee

    order = Order(
        farmer_id=farmer.id if farmer else None,
        retailer_id=retailer.id if retailer else None,
        delivery_method=payload.delivery_method,
        speed=payload.speed,
        payment_method=payload.payment_method,
        subtotal=subtotal,
        delivery_fee=fee,
        total=total,
        status="confirmed",
        payment_status="pending",
    )
    db.add(order)
    db.flush()  # get order.id before adding items

    for item in payload.items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.id,
                name=item.name,
                price=item.price,
                unit=item.unit,
                img=item.img,
                qty=item.qty,
            )
        )

    if farmer:
        db.add(
            Notification(
                farmer_id=farmer.id,
                category="order",
                title="Order confirmed",
                body=f"Order #{order.ref} has been placed — {int(total):,} RWF".replace(",", ","),
                order_id=order.ref,
            )
        )

    db.commit()
    db.refresh(order)

    # Fire the mobile-money push payment request (non-blocking best-effort)
    if farmer and payload.payment_method in ("mtn_momo", "airtel"):
        payment_result = await request_payment(payload.payment_method, farmer.phone, total, order.ref)
        if payment_result and payment_result.get("status") == "pending":
            pass  # webhook will update payment_status when it lands
        send_order_update_sms(farmer.phone, order.ref, "confirmed, awaiting payment confirmation")

    return order.to_dict()


@router.get("")
def list_orders(
    phone: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_farmer: Farmer | None = Depends(get_optional_farmer),
):
    farmer = current_farmer
    if farmer is None and phone:
        farmer = db.query(Farmer).filter(Farmer.phone == normalize_phone(phone)).first()
    if farmer is None:
        return []
    orders = (
        db.query(Order)
        .filter(Order.farmer_id == farmer.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return [o.to_dict() for o in orders]


@router.get("/{ref}")
def get_order(ref: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.ref == ref).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order.to_dict()


@router.post("/{ref}/cancel")
def cancel_order(ref: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.ref == ref).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status in ("delivered", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel an order that is {order.status}")

    order.status = "cancelled"
    order.payment_status = "refunded" if order.payment_status == "paid" else "cancelled"
    if order.farmer:
        db.add(
            Notification(
                farmer_id=order.farmer_id,
                category="order",
                title="Order cancelled",
                body=f"Order #{order.ref} was cancelled and any payment will be refunded.",
                order_id=order.ref,
            )
        )
        send_order_update_sms(order.farmer.phone, order.ref, "cancelled — refund initiated")
    db.commit()
    return order.to_dict()


def _mark_paid(db: Session, order: Order):
    order.payment_status = "paid"
    order.status = "processing" if order.status == "confirmed" else order.status
    if order.farmer:
        db.add(
            Notification(
                farmer_id=order.farmer_id,
                category="order",
                title="Payment received",
                body=f"Payment for order #{order.ref} was received. Your order is now being processed.",
                order_id=order.ref,
            )
        )
        send_order_update_sms(order.farmer.phone, order.ref, "payment received, processing")
    db.commit()


@router.post("/payments/mtn/callback")
async def mtn_momo_callback(request: Request, db: Session = Depends(get_db)):
    """MTN MoMo Collections webhook. Payload shape varies by integration;
    we look for an externalId matching our order ref and a success status."""
    data = await request.json()
    order_ref = data.get("externalId") or data.get("reference")
    status_val = (data.get("status") or "").upper()
    order = db.query(Order).filter(Order.ref == order_ref).first()
    if order and status_val == "SUCCESSFUL":
        _mark_paid(db, order)
    return {"received": True}


@router.post("/payments/airtel/callback")
async def airtel_callback(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    transaction = data.get("transaction", {})
    order_ref = transaction.get("id") or data.get("reference")
    status_val = (transaction.get("status") or data.get("status") or "").upper()
    order = db.query(Order).filter(Order.ref == order_ref).first()
    if order and status_val in ("SUCCESS", "TS"):
        _mark_paid(db, order)
    return {"received": True}
