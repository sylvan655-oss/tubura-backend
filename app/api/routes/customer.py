import random

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.api.deps import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.models import (User, Product, PreOrder, Notification, SupportTicket)
from app.api.routes.catalog import stock_totals

router = APIRouter(prefix="/api", tags=["customer"])


# ── PRE-ORDERS ─────────────────────────────────────────────────────────────

class PreOrderIn(BaseModel):
    product_id: int | None = None     # None = "couldn't find it" case
    product_name: str | None = None   # what the customer typed
    requested_qty: int = 1


@router.post("/preorders")
def create_preorder(body: PreOrderIn, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    name = (body.product_name or "").strip()
    stock_now = None
    if body.product_id:
        product = db.get(Product, body.product_id)
        if not product:
            raise HTTPException(404, "Product not found")
        name = product.name_en
        stock_now = stock_totals(db, [product.id]).get(product.id, 0)
    if not name:
        raise HTTPException(400, "Tell us which product you need")
    if body.requested_qty < 1:
        raise HTTPException(400, "Quantity must be at least 1")

    po = PreOrder(user_id=user.id, product_id=body.product_id,
                  product_name=name, requested_qty=body.requested_qty,
                  stock_at_request=stock_now, status="received")
    db.add(po)
    db.add(Notification(user_id=user.id, type="order",
                        title="Pre-order received",
                        body=f"Your pre-order for {body.requested_qty} × "
                             f"{name} was received. We will contact you."))
    db.commit()
    db.refresh(po)
    return {"id": po.id, "status": po.status}


@router.get("/preorders")
def my_preorders(user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    rows = (db.query(PreOrder).filter(PreOrder.user_id == user.id)
              .order_by(PreOrder.id.desc()).all())
    return [{"id": p.id, "product_name": p.product_name,
             "requested_qty": p.requested_qty, "status": p.status,
             "created_at": p.created_at.isoformat()} for p in rows]


# ── NOTIFICATIONS ──────────────────────────────────────────────────────────

@router.get("/notifications")
def my_notifications(user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    rows = (db.query(Notification)
              .filter(or_(
                  Notification.user_id == user.id,
                  and_(Notification.user_id.is_(None),
                       Notification.send_status == "sent",
                       Notification.audience == "all")))
              .order_by(Notification.id.desc()).limit(50).all())
    return [{"id": n.id, "type": n.type, "title": n.title, "body": n.body,
             "image": n.image, "button_text": n.button_text,
             "button_link": n.button_link, "order_ref": n.order_ref,
             "read": n.read if n.user_id else True,
             "created_at": n.created_at.isoformat()} for n in rows]


@router.put("/notifications/{notif_id}/read")
def mark_read(notif_id: int, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    n = db.get(Notification, notif_id)
    if n and n.user_id == user.id:
        n.read = True
        db.commit()
    return {"ok": True}


@router.get("/banners")
def banner_list(db: Session = Depends(get_db)):
    """Up to 5 newest sent banners — the app's Home carousel. Public."""
    rows = (db.query(Notification)
              .filter(Notification.user_id.is_(None),
                      Notification.type == "banner",
                      Notification.send_status == "sent")
              .order_by(Notification.id.desc()).limit(5).all())
    return [{"id": n.id, "title": n.title, "body": n.body, "image": n.image,
             "button_text": n.button_text, "button_link": n.button_link,
             "created_at": n.created_at.isoformat()} for n in rows]


@router.get("/banner")
def current_banner(db: Session = Depends(get_db)):
    """Latest sent announcement banner, for the Home screen. Public."""
    n = (db.query(Notification)
           .filter(Notification.user_id.is_(None),
                   Notification.type == "banner",
                   Notification.send_status == "sent")
           .order_by(Notification.id.desc()).first())
    if not n:
        return None
    return {"id": n.id, "title": n.title, "body": n.body, "image": n.image,
            "button_text": n.button_text, "button_link": n.button_link}


# ── SUPPORT ────────────────────────────────────────────────────────────────

class TicketIn(BaseModel):
    subject: str
    message: str
    email: str | None = None
    phone: str | None = None


@router.post("/support")
def create_ticket(body: TicketIn,
                  user: User | None = Depends(get_current_user_optional),
                  db: Session = Depends(get_db)):
    ticket_no = "TKT" + "".join(random.choices("0123456789", k=6))
    t = SupportTicket(ticket_no=ticket_no,
                      user_id=user.id if user else None,
                      phone=(user.phone if user else body.phone),
                      email=body.email, subject=body.subject.strip()[:150],
                      message=body.message.strip())
    db.add(t)
    db.commit()
    return {"ticket_no": ticket_no, "status": "open"}


@router.get("/support")
def my_tickets(user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    rows = (db.query(SupportTicket).filter(SupportTicket.user_id == user.id)
              .order_by(SupportTicket.id.desc()).all())
    return [{"ticket_no": t.ticket_no, "subject": t.subject,
             "status": t.status, "created_at": t.created_at.isoformat()}
            for t in rows]
