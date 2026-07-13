from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.config import settings
from app.db.session import engine
from app.models import (User, Administrator, Category, Product, Retailer,
                        RetailerStock, Order, OrderItem, PreOrder,
                        Notification, SupportTicket)
from app.api.routes import auth, catalog, orders, customer, admin as admin_api

app = FastAPI(title="Tubura API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(orders.router)
app.include_router(customer.router)
app.include_router(admin_api.router)


@app.get("/")
def root():
    return {"service": "Tubura API", "status": "ok"}


# ── SQLAdmin backdoor at /admin (raw table access for emergencies) ─────────

class BasicAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        if (form.get("username") == settings.ADMIN_USERNAME
                and form.get("password") == settings.ADMIN_PASSWORD):
            request.session.update({"admin": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("admin"))


sqladmin = Admin(app, engine,
                 authentication_backend=BasicAuth(
                     secret_key=settings.SECRET_KEY))


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.name, User.phone, User.district,
                   User.customer_type, User.care_status, User.is_active]
    column_searchable_list = [User.name, User.phone]
    column_details_exclude_list = [User.password_hash]
    column_export_exclude_list = [User.password_hash]
    form_excluded_columns = [User.password_hash]


class AdminAdmin(ModelView, model=Administrator):
    column_list = [Administrator.id, Administrator.username,
                   Administrator.role, Administrator.is_active]
    column_details_exclude_list = [Administrator.password_hash]
    column_export_exclude_list = [Administrator.password_hash]
    form_excluded_columns = [Administrator.password_hash]


class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name_en, Category.is_hidden,
                   Category.sort_order]


class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.name_en, Product.price,
                   Product.low_stock_threshold, Product.featured,
                   Product.status]
    column_searchable_list = [Product.name_en]


class RetailerAdmin(ModelView, model=Retailer):
    column_list = [Retailer.id, Retailer.name, Retailer.district,
                   Retailer.sector, Retailer.is_active]
    column_searchable_list = [Retailer.name]


class StockAdmin(ModelView, model=RetailerStock):
    column_list = [RetailerStock.id, RetailerStock.retailer,
                   RetailerStock.product, RetailerStock.quantity,
                   RetailerStock.updated_at]


class OrderAdmin(ModelView, model=Order):
    column_list = [Order.id, Order.ref, Order.status, Order.total,
                   Order.district, Order.created_at]
    column_searchable_list = [Order.ref]


class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [OrderItem.id, OrderItem.order_id, OrderItem.name,
                   OrderItem.qty, OrderItem.price, OrderItem.retailer]


class PreOrderAdmin(ModelView, model=PreOrder):
    column_list = [PreOrder.id, PreOrder.product_name,
                   PreOrder.requested_qty, PreOrder.status,
                   PreOrder.created_at]


class NotificationAdmin(ModelView, model=Notification):
    column_list = [Notification.id, Notification.type, Notification.title,
                   Notification.audience, Notification.send_status,
                   Notification.created_at]


class TicketAdmin(ModelView, model=SupportTicket):
    column_list = [SupportTicket.id, SupportTicket.ticket_no,
                   SupportTicket.subject, SupportTicket.status,
                   SupportTicket.created_at]


for view in (UserAdmin, AdminAdmin, CategoryAdmin, ProductAdmin,
             RetailerAdmin, StockAdmin, OrderAdmin, OrderItemAdmin,
             PreOrderAdmin, NotificationAdmin, TicketAdmin):
    sqladmin.add_view(view)
