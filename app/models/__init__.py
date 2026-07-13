"""
All V1 models. Alembic's env.py does `from app.models import *`,
so every model MUST be imported here or its table won't be created.
"""
from app.models.user import User
from app.models.admin import Administrator
from app.models.category import Category
from app.models.product import Product
from app.models.retailer import Retailer
from app.models.retailer_stock import RetailerStock
from app.models.order import Order, OrderItem
from app.models.preorder import PreOrder
from app.models.notification import Notification
from app.models.support import SupportTicket
from app.models.otp import OTP

__all__ = [
    "User", "Administrator", "Category", "Product", "Retailer",
    "RetailerStock", "Order", "OrderItem", "PreOrder", "Notification",
    "SupportTicket", "OTP",
]
