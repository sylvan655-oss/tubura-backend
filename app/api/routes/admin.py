"""
Admin API — everything the dashboard UI (Phase 3) will call.
All endpoints require an admin JWT except /login.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, require_superadmin, require_perm
from app.core.security import verify_password, hash_password, create_token
from app.db.session import get_db
from app.models import (Administrator, Category, Product, Retailer,
                        RetailerStock, Order, OrderItem, PreOrder, User,
                        Notification, SupportTicket)
from app.api.routes.catalog import stock_totals, stock_label
from app.services.sms import send_sms

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── AUTH ───────────────────────────────────────────────────────────────────

class AdminLoginIn(BaseModel):
    username: str
    password: str


@router.post("/login")
def admin_login(body: AdminLoginIn, db: Session = Depends(get_db)):
    admin = (db.query(Administrator)
               .filter(Administrator.username == body.username).first())
    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(401, "Wrong username or password")
    if not admin.is_active:
        raise HTTPException(403, "This admin account is disabled")
    return {"token": create_token(admin.id, "admin"),
            "username": admin.username, "role": admin.role,
            "permissions": admin.permissions}


# ── DASHBOARD SUMMARY ──────────────────────────────────────────────────────

@router.get("/summary")
def summary(admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.status == "active").all()
    totals = stock_totals(db, [p.id for p in products])
    out_of_stock = sum(1 for p in products if totals.get(p.id, 0) <= 0)
    low_stock = sum(1 for p in products
                    if 0 < totals.get(p.id, 0) <= p.low_stock_threshold)
    return {
        "orders_waiting": db.query(Order)
            .filter(Order.status == "pending").count(),
        "preorders_waiting": db.query(PreOrder)
            .filter(PreOrder.status.in_(["received", "under_review"])).count(),
        "out_of_stock_products": out_of_stock,
        "low_stock_products": low_stock,
        "active_products": len(products),
        "notifications_sent": db.query(Notification)
            .filter(Notification.user_id.is_(None),
                    Notification.send_status == "sent").count(),
        "open_tickets": db.query(SupportTicket)
            .filter(SupportTicket.status.in_(["open", "in_progress"])).count(),
    }


# ── CATEGORIES ─────────────────────────────────────────────────────────────

class CategoryIn(BaseModel):
    name_en: str
    name_rw: str
    name_fr: str
    is_hidden: bool = False
    sort_order: int = 0


@router.get("/categories")
def admin_categories(admin=Depends(require_perm('categories')),
                     db: Session = Depends(get_db)):
    cats = db.query(Category).order_by(Category.sort_order, Category.id).all()
    return [{"id": c.id, "name_en": c.name_en, "name_rw": c.name_rw,
             "name_fr": c.name_fr, "is_hidden": c.is_hidden,
             "sort_order": c.sort_order} for c in cats]


@router.post("/categories")
def add_category(body: CategoryIn, admin=Depends(require_perm('categories')),
                 db: Session = Depends(get_db)):
    c = Category(**body.model_dump())
    db.add(c); db.commit(); db.refresh(c)
    return {"id": c.id}


@router.put("/categories/{cat_id}")
def edit_category(cat_id: int, body: CategoryIn,
                  admin=Depends(require_perm('categories')),
                  db: Session = Depends(get_db)):
    c = db.get(Category, cat_id)
    if not c:
        raise HTTPException(404, "Category not found")
    for k, v in body.model_dump().items():
        setattr(c, k, v)
    db.commit()
    return {"ok": True}


@router.delete("/categories/{cat_id}")
def delete_category(cat_id: int, admin=Depends(require_perm('categories')),
                    db: Session = Depends(get_db)):
    c = db.get(Category, cat_id)
    if not c:
        raise HTTPException(404, "Category not found")
    in_use = db.query(Product).filter(Product.category_id == cat_id).count()
    if in_use:
        raise HTTPException(400, f"{in_use} products use this category. "
                                 f"Move them first or hide the category.")
    db.delete(c); db.commit()
    return {"ok": True}


# ── PRODUCTS ───────────────────────────────────────────────────────────────

class ProductIn(BaseModel):
    category_id: int | None = None
    brand: str | None = None
    name_en: str; name_rw: str; name_fr: str
    unit_en: str; unit_rw: str; unit_fr: str
    description_en: str; description_rw: str; description_fr: str
    specifications: str | None = None
    price: float
    low_stock_threshold: int = 10
    featured: bool = False
    status: str = "active"          # active | hidden
    img: str | None = None


@router.get("/products")
def admin_products(admin=Depends(require_perm('products')),
                   db: Session = Depends(get_db),
                   category_id: int | None = None,
                   status: str | None = None,
                   stock: str | None = Query(None, description="in_stock|limited|out_of_stock"),
                   featured: bool | None = None,
                   search: str | None = None):
    q = db.query(Product)
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if status:
        q = q.filter(Product.status == status)
    if featured is not None:
        q = q.filter(Product.featured.is_(featured))
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(or_(Product.name_en.ilike(like),
                         Product.name_rw.ilike(like),
                         Product.name_fr.ilike(like),
                         Product.brand.ilike(like)))
    products = q.order_by(Product.id.desc()).all()
    totals = stock_totals(db, [p.id for p in products])

    out = []
    for p in products:
        total = totals.get(p.id, 0)
        label = stock_label(total, p.low_stock_threshold)
        if stock and label != stock:
            continue
        out.append({
            "id": p.id, "name_en": p.name_en, "name_rw": p.name_rw,
            "name_fr": p.name_fr, "brand": p.brand,
            "category_id": p.category_id,
            "category": p.category.name_en if p.category else None,
            "price": p.price, "stock_total": total, "stock_label": label,
            "low_stock_threshold": p.low_stock_threshold,
            "featured": p.featured, "status": p.status, "img": p.img,
            "unit_en": p.unit_en, "unit_rw": p.unit_rw, "unit_fr": p.unit_fr,
            "description_en": p.description_en,
            "description_rw": p.description_rw,
            "description_fr": p.description_fr,
            "specifications": p.specifications,
            "updated_at": p.updated_at.isoformat(),
        })
    return out


@router.post("/products")
def add_product(body: ProductIn, admin=Depends(require_perm('products')),
                db: Session = Depends(get_db)):
    p = Product(**body.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return {"id": p.id}


@router.put("/products/{product_id}")
def edit_product(product_id: int, body: ProductIn,
                 admin=Depends(require_perm('products')),
                 db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.commit()
    return {"ok": True}


@router.delete("/products/{product_id}")
def delete_product(product_id: int, admin=Depends(require_perm('products')),
                   db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    ordered = db.query(OrderItem).filter(
        OrderItem.product_id == product_id).count()
    if ordered:
        # keep history intact — hide instead of hard delete
        p.status = "hidden"
        db.commit()
        return {"ok": True, "hidden_instead": True,
                "reason": "Product appears in past orders"}
    db.delete(p); db.commit()
    return {"ok": True}


# ── RETAILERS ──────────────────────────────────────────────────────────────

class RetailerIn(BaseModel):
    name: str
    phone: str | None = None
    province: str | None = None
    district: str | None = None
    sector: str | None = None
    cell: str | None = None
    village: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool = True


@router.get("/retailers")
def admin_retailers(admin=Depends(require_perm('retailers')),
                    db: Session = Depends(get_db)):
    rows = db.query(Retailer).order_by(Retailer.id).all()
    return [{"id": r.id, "name": r.name, "phone": r.phone,
             "province": r.province, "district": r.district,
             "sector": r.sector, "cell": r.cell, "village": r.village,
             "latitude": r.latitude, "longitude": r.longitude,
             "is_active": r.is_active} for r in rows]


@router.post("/retailers")
def add_retailer(body: RetailerIn, admin=Depends(require_perm('retailers')),
                 db: Session = Depends(get_db)):
    r = Retailer(**body.model_dump())
    db.add(r); db.commit(); db.refresh(r)
    return {"id": r.id}


@router.put("/retailers/{retailer_id}")
def edit_retailer(retailer_id: int, body: RetailerIn,
                  admin=Depends(require_perm('retailers')),
                  db: Session = Depends(get_db)):
    r = db.get(Retailer, retailer_id)
    if not r:
        raise HTTPException(404, "Retailer not found")
    for k, v in body.model_dump().items():
        setattr(r, k, v)
    db.commit()
    return {"ok": True}


# ── STOCK (the daily-use table) ────────────────────────────────────────────

class StockIn(BaseModel):
    retailer_id: int
    product_id: int
    quantity: int


@router.get("/stock")
def admin_stock(admin=Depends(require_perm('stock')),
                db: Session = Depends(get_db),
                retailer_id: int | None = None,
                product_id: int | None = None):
    q = db.query(RetailerStock)
    if retailer_id:
        q = q.filter(RetailerStock.retailer_id == retailer_id)
    if product_id:
        q = q.filter(RetailerStock.product_id == product_id)
    rows = q.all()
    return [{"id": s.id, "retailer_id": s.retailer_id,
             "retailer": s.retailer.name,
             "product_id": s.product_id, "product": s.product.name_en,
             "quantity": s.quantity,
             "updated_at": s.updated_at.isoformat()} for s in rows]


@router.put("/stock")
def set_stock(body: StockIn, admin=Depends(require_perm('stock')),
              db: Session = Depends(get_db)):
    """Upsert: creates the row if this retailer never stocked this product."""
    if body.quantity < 0:
        raise HTTPException(400, "Quantity cannot be negative")
    row = (db.query(RetailerStock)
             .filter_by(retailer_id=body.retailer_id,
                        product_id=body.product_id).first())
    if row:
        row.quantity = body.quantity
    else:
        if not db.get(Retailer, body.retailer_id):
            raise HTTPException(404, "Retailer not found")
        if not db.get(Product, body.product_id):
            raise HTTPException(404, "Product not found")
        row = RetailerStock(**body.model_dump())
        db.add(row)
    db.commit()
    return {"ok": True, "quantity": row.quantity}


# ── ORDERS ─────────────────────────────────────────────────────────────────

ORDER_STATUSES = ["pending", "confirmed", "preparing", "ready",
                  "delivered", "cancelled"]

STATUS_MESSAGES = {
    "confirmed": "has been confirmed",
    "preparing": "is being prepared",
    "ready": "is ready for delivery/pickup",
    "delivered": "has been delivered. Thank you!",
    "cancelled": "has been cancelled",
}


@router.get("/orders")
def admin_orders(admin=Depends(require_perm('orders')),
                 db: Session = Depends(get_db),
                 status: str | None = None,
                 search: str | None = None):
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if search:
        like = f"%{search.strip()}%"
        q = (q.outerjoin(User)
              .filter(or_(Order.ref.ilike(like), User.name.ilike(like),
                          User.phone.ilike(like))))
    orders = q.order_by(Order.id.desc()).limit(300).all()
    return [{
        "id": o.id, "ref": o.ref,
        "customer": o.user.name if o.user else None,
        "phone": o.user.phone if o.user else None,
        "total": o.total, "status": o.status,
        "items_count": len(o.items),
        "district": o.district, "sector": o.sector,
        "cell": o.cell, "village": o.village,
        "landmark": o.landmark,
        "created_at": o.created_at.isoformat(),
        "items": [{"id": i.id, "name": i.name, "qty": i.qty,
                   "price": i.price, "retailer_id": i.retailer_id,
                   "retailer": i.retailer.name if i.retailer else None}
                  for i in o.items],
    } for o in orders]


class StatusIn(BaseModel):
    status: str


@router.put("/orders/{order_id}/status")
def set_order_status(order_id: int, body: StatusIn,
                     admin=Depends(require_perm('orders')),
                     db: Session = Depends(get_db)):
    if body.status not in ORDER_STATUSES:
        raise HTTPException(400, f"Status must be one of {ORDER_STATUSES}")
    o = db.get(Order, order_id)
    if not o:
        raise HTTPException(404, "Order not found")

    # Cancelling from the dashboard also restores stock
    if body.status == "cancelled" and o.status != "cancelled":
        for item in o.items:
            if item.retailer_id and item.product_id:
                row = (db.query(RetailerStock)
                         .filter_by(retailer_id=item.retailer_id,
                                    product_id=item.product_id).first())
                if row:
                    row.quantity += item.qty

    o.status = body.status
    o.updated_at = datetime.utcnow()
    o.assigned_admin_id = admin.id

    if o.user and body.status in STATUS_MESSAGES:
        msg = f"Order #{o.ref} {STATUS_MESSAGES[body.status]}."
        db.add(Notification(user_id=o.user_id, type="order",
                            title=f"Order {body.status}",
                            body=msg, order_ref=o.ref))
        send_sms(o.user.phone, "Tubura: " + msg)
    db.commit()
    return {"ok": True, "status": o.status}


class ReassignIn(BaseModel):
    retailer_id: int


@router.put("/order-items/{item_id}/retailer")
def reassign_item(item_id: int, body: ReassignIn,
                  admin=Depends(require_perm('orders')),
                  db: Session = Depends(get_db)):
    item = db.get(OrderItem, item_id)
    if not item:
        raise HTTPException(404, "Order item not found")
    new_row = (db.query(RetailerStock)
                 .filter_by(retailer_id=body.retailer_id,
                            product_id=item.product_id).first())
    if not new_row or new_row.quantity < item.qty:
        raise HTTPException(400, "That retailer does not have enough stock")
    # give stock back to the old retailer, take from the new
    if item.retailer_id:
        old = (db.query(RetailerStock)
                 .filter_by(retailer_id=item.retailer_id,
                            product_id=item.product_id).first())
        if old:
            old.quantity += item.qty
    new_row.quantity -= item.qty
    item.retailer_id = body.retailer_id
    db.commit()
    return {"ok": True}


# ── PRE-ORDERS ─────────────────────────────────────────────────────────────

PREORDER_STATUSES = ["received", "under_review", "approved", "ordered",
                     "ready", "cancelled"]


@router.get("/preorders")
def admin_preorders(admin=Depends(require_perm('preorders')),
                    db: Session = Depends(get_db),
                    status: str | None = None):
    q = db.query(PreOrder)
    if status:
        q = q.filter(PreOrder.status == status)
    rows = q.order_by(PreOrder.id.desc()).limit(300).all()
    return [{"id": p.id,
             "customer": p.user.name if p.user else None,
             "phone": p.user.phone if p.user else None,
             "product_id": p.product_id, "product_name": p.product_name,
             "requested_qty": p.requested_qty,
             "stock_at_request": p.stock_at_request,
             "status": p.status,
             "converted_order_id": p.converted_order_id,
             "created_at": p.created_at.isoformat()} for p in rows]


@router.put("/preorders/{po_id}/status")
def set_preorder_status(po_id: int, body: StatusIn,
                        admin=Depends(require_perm('preorders')),
                        db: Session = Depends(get_db)):
    if body.status not in PREORDER_STATUSES:
        raise HTTPException(400, f"Status must be one of {PREORDER_STATUSES}")
    p = db.get(PreOrder, po_id)
    if not p:
        raise HTTPException(404, "Pre-order not found")
    p.status = body.status
    p.assigned_admin_id = admin.id
    p.updated_at = datetime.utcnow()
    if p.user:
        db.add(Notification(user_id=p.user_id, type="order",
                            title="Pre-order update",
                            body=f"Your pre-order for {p.product_name} "
                                 f"is now: {body.status.replace('_', ' ')}."))
    db.commit()
    return {"ok": True}


# ── CUSTOMERS ──────────────────────────────────────────────────────────────

@router.get("/customers")
def admin_customers(admin=Depends(require_perm('customers')),
                    db: Session = Depends(get_db),
                    search: str | None = None,
                    care_status: str | None = None):
    q = db.query(User)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(or_(User.name.ilike(like), User.phone.ilike(like),
                         User.email.ilike(like)))
    if care_status:
        q = q.filter(User.care_status == care_status)
    users = q.order_by(User.id.desc()).limit(300).all()
    order_counts = dict(db.query(Order.user_id, func.count(Order.id))
                          .group_by(Order.user_id).all())
    preorder_counts = dict(db.query(PreOrder.user_id, func.count(PreOrder.id))
                             .group_by(PreOrder.user_id).all())
    return [{"id": u.id, "customer_code": u.customer_code,
             "name": u.name, "phone": u.phone, "email": u.email,
             "gender": u.gender,
             "dob": u.dob.isoformat() if u.dob else None,
             "language": u.language,
             "district": u.district, "customer_type": u.customer_type,
             "orders": order_counts.get(u.id, 0),
             "preorders": preorder_counts.get(u.id, 0),
             "care_status": u.care_status, "is_active": u.is_active,
             "date_joined": u.created_at.isoformat()} for u in users]


class CustomerUpdate(BaseModel):
    care_status: str | None = None    # normal | needs_followup | frequent_issues
    is_active: bool | None = None


@router.put("/customers/{user_id}")
def update_customer(user_id: int, body: CustomerUpdate,
                    admin=Depends(require_perm('customers')),
                    db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Customer not found")
    if body.care_status is not None:
        u.care_status = body.care_status
    if body.is_active is not None:
        u.is_active = body.is_active
    db.commit()
    return {"ok": True}


# ── NOTIFICATIONS / CAMPAIGNS ──────────────────────────────────────────────

class CampaignIn(BaseModel):
    type: str = "service"       # banner | push | promo | seasonal | service
    title: str
    body: str
    image: str | None = None
    button_text: str | None = None
    button_link: str | None = None
    audience: str = "all"       # all | selected | individual
    audience_user_ids: list[int] | None = None


@router.post("/notifications")
def create_campaign(body: CampaignIn, admin=Depends(require_perm('notifications')),
                    db: Session = Depends(get_db)):
    if body.audience == "all":
        n = Notification(**body.model_dump(), user_id=None,
                         send_status="sent", sent_at=datetime.utcnow(),
                         created_by_admin_id=admin.id)
        db.add(n)
    else:
        ids = body.audience_user_ids or []
        if not ids:
            raise HTTPException(400, "audience_user_ids required")
        data = body.model_dump(exclude={"audience", "audience_user_ids"})
        for uid in ids:
            db.add(Notification(**data, user_id=uid, audience="individual",
                                send_status="sent",
                                sent_at=datetime.utcnow(),
                                created_by_admin_id=admin.id))
    db.commit()
    return {"ok": True}


@router.get("/notifications")
def admin_notifications(admin=Depends(require_perm('notifications')),
                        db: Session = Depends(get_db)):
    rows = (db.query(Notification)
              .filter(Notification.created_by_admin_id.isnot(None))
              .order_by(Notification.id.desc()).limit(200).all())
    return [{"id": n.id, "type": n.type, "title": n.title,
             "audience": n.audience, "user_id": n.user_id,
             "send_status": n.send_status,
             "created_at": n.created_at.isoformat()} for n in rows]


@router.delete("/notifications/{notif_id}")
def delete_notification(notif_id: int, admin=Depends(require_perm('notifications')),
                        db: Session = Depends(get_db)):
    n = db.get(Notification, notif_id)
    if n:
        db.delete(n); db.commit()
    return {"ok": True}


# ── SUPPORT TICKETS ────────────────────────────────────────────────────────

TICKET_STATUSES = ["open", "in_progress", "resolved", "closed"]


@router.get("/tickets")
def admin_tickets(admin=Depends(require_perm('support')),
                  db: Session = Depends(get_db),
                  status: str | None = None):
    q = db.query(SupportTicket)
    if status:
        q = q.filter(SupportTicket.status == status)
    rows = q.order_by(SupportTicket.id.desc()).limit(300).all()
    return [{"id": t.id, "ticket_no": t.ticket_no,
             "customer": t.user.name if t.user else None,
             "phone": t.phone, "email": t.email, "subject": t.subject,
             "message": t.message, "status": t.status,
             "assigned_admin_id": t.assigned_admin_id,
             "created_at": t.created_at.isoformat()} for t in rows]


class TicketUpdate(BaseModel):
    status: str | None = None
    assign_to_me: bool = False


@router.put("/tickets/{ticket_id}")
def update_ticket(ticket_id: int, body: TicketUpdate,
                  admin=Depends(require_perm('support')),
                  db: Session = Depends(get_db)):
    t = db.get(SupportTicket, ticket_id)
    if not t:
        raise HTTPException(404, "Ticket not found")
    if body.status:
        if body.status not in TICKET_STATUSES:
            raise HTTPException(400, f"Status must be one of {TICKET_STATUSES}")
        t.status = body.status
    if body.assign_to_me:
        t.assigned_admin_id = admin.id
    t.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


# ── ADMINISTRATORS (superadmin only) ───────────────────────────────────────

class AdminIn(BaseModel):
    username: str
    password: str | None = None
    email: str | None = None
    role: str = "admin"
    permissions: list[str] = []
    is_active: bool = True


@router.get("/admins")
def list_admins(admin=Depends(require_superadmin),
                db: Session = Depends(get_db)):
    rows = db.query(Administrator).order_by(Administrator.id).all()
    return [{"id": a.id, "username": a.username, "email": a.email,
             "role": a.role, "permissions": a.permissions,
             "is_active": a.is_active} for a in rows]


@router.post("/admins")
def add_admin(body: AdminIn, admin=Depends(require_superadmin),
              db: Session = Depends(get_db)):
    if not body.password or len(body.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    if db.query(Administrator).filter_by(username=body.username).first():
        raise HTTPException(400, "Username already taken")
    a = Administrator(username=body.username,
                      password_hash=hash_password(body.password),
                      email=body.email, role=body.role,
                      permissions=body.permissions, is_active=body.is_active)
    db.add(a); db.commit(); db.refresh(a)
    return {"id": a.id}


@router.put("/admins/{admin_id}")
def edit_admin(admin_id: int, body: AdminIn,
               admin=Depends(require_superadmin),
               db: Session = Depends(get_db)):
    a = db.get(Administrator, admin_id)
    if not a:
        raise HTTPException(404, "Admin not found")
    a.username = body.username
    a.email = body.email
    a.role = body.role
    a.permissions = body.permissions
    a.is_active = body.is_active
    if body.password:
        a.password_hash = hash_password(body.password)
    db.commit()
    return {"ok": True}
