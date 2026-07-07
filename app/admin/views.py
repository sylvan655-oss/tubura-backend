"""
Admin dashboard views.

Each ModelView below configures ONE table you'll see in the sidebar at
/admin — which columns show in the list, which are searchable/filterable,
and (importantly) which sensitive fields are excluded entirely so they
never render in the browser, get exported, or appear in forms.
"""
from sqladmin import ModelView
from sqladmin.filters import AllUniqueStringValuesFilter, BooleanFilter, StaticValuesFilter

from app.models.farmer import Farmer
from app.models.otp import OTP
from app.models.product import Product
from app.models.retailer import Retailer
from app.models.order import Order, OrderItem
from app.models.training import Training, TrainingBooking
from app.models.delivery_location import DeliveryLocation
from app.models.notification import Notification
from app.models.support import SupportRequest


class FarmerAdmin(ModelView, model=Farmer):
    name = "Farmer"
    name_plural = "Farmers"
    icon = "fa-solid fa-user"
    category = "Customers"

    # password_hash is deliberately left out of every list below —
    # it must never be visible, searchable, exportable, or editable here.
    column_list = [
        Farmer.id, Farmer.name, Farmer.phone, Farmer.farmer_id,
        Farmer.district, Farmer.customer_type, Farmer.gender,
        Farmer.age, Farmer.is_active, Farmer.created_at,
    ]
    column_searchable_list = [Farmer.name, Farmer.phone, Farmer.farmer_id, Farmer.district]
    column_sortable_list = [Farmer.id, Farmer.name, Farmer.district, Farmer.created_at]
    column_filters = [
        AllUniqueStringValuesFilter(Farmer.district),
        AllUniqueStringValuesFilter(Farmer.province),
        AllUniqueStringValuesFilter(Farmer.customer_type),
        AllUniqueStringValuesFilter(Farmer.gender),
        BooleanFilter(Farmer.is_active),
    ]
    form_columns = [
        Farmer.name, Farmer.phone, Farmer.dob, Farmer.age, Farmer.gender,
        Farmer.province, Farmer.district, Farmer.sector, Farmer.cell, Farmer.village,
        Farmer.customer_type, Farmer.interests, Farmer.crops, Farmer.farmer_id, Farmer.is_active,
    ]
    can_export = True
    page_size = 25


class OrderAdmin(ModelView, model=Order):
    name = "Order"
    name_plural = "Orders"
    icon = "fa-solid fa-cart-shopping"
    category = "Sales"

    column_list = [
        Order.id, Order.ref, Order.farmer, Order.retailer, Order.status,
        Order.payment_status, Order.payment_method, Order.delivery_method,
        Order.total, Order.created_at,
    ]
    column_searchable_list = [Order.ref]
    column_sortable_list = [Order.id, Order.total, Order.created_at]
    column_filters = [
        StaticValuesFilter(
            Order.status,
            values=[(s, s.capitalize()) for s in ("confirmed", "processing", "shipped", "delivered", "cancelled")],
        ),
        StaticValuesFilter(
            Order.payment_status,
            values=[(s, s.capitalize()) for s in ("pending", "paid", "refunded", "cancelled")],
        ),
        StaticValuesFilter(
            Order.payment_method,
            values=[("mtn_momo", "MTN Mobile Money"), ("airtel", "Airtel Money"), ("card", "Card")],
        ),
        StaticValuesFilter(
            Order.delivery_method,
            values=[("pickup", "Pickup"), ("delivery", "Delivery")],
        ),
    ]
    column_default_sort = [(Order.created_at, True)]
    form_columns = [Order.status, Order.payment_status]  # ops staff can update status; totals/items stay read-only here
    can_create = False
    can_export = True
    page_size = 25


class OrderItemAdmin(ModelView, model=OrderItem):
    name = "Order Item"
    name_plural = "Order Items"
    icon = "fa-solid fa-box"
    category = "Sales"

    column_list = [OrderItem.id, OrderItem.order, OrderItem.name, OrderItem.price, OrderItem.qty]
    column_searchable_list = [OrderItem.name]
    can_create = False
    can_edit = False
    page_size = 25


class ProductAdmin(ModelView, model=Product):
    name = "Product"
    name_plural = "Products"
    icon = "fa-solid fa-seedling"
    category = "Catalogue"

    column_list = [
        Product.id, Product.name_en, Product.category_key, Product.price,
        Product.stock, Product.rating, Product.sold,
    ]
    column_searchable_list = [Product.name_en, Product.name_rw, Product.name_fr]
    column_sortable_list = [Product.price, Product.stock, Product.sold]
    column_filters = [AllUniqueStringValuesFilter(Product.category_key)]
    can_export = True
    page_size = 25


class RetailerAdmin(ModelView, model=Retailer):
    name = "Retailer"
    name_plural = "Retailers"
    icon = "fa-solid fa-shop"
    category = "Catalogue"

    column_list = [Retailer.id, Retailer.name, Retailer.phone, Retailer.district, Retailer.stock_level]
    column_searchable_list = [Retailer.name, Retailer.phone, Retailer.district]
    column_filters = [
        AllUniqueStringValuesFilter(Retailer.district),
        StaticValuesFilter(Retailer.stock_level, values=[("High", "High"), ("Medium", "Medium"), ("Low", "Low")]),
    ]
    can_export = True
    page_size = 25


class TrainingAdmin(ModelView, model=Training):
    name = "Training"
    name_plural = "Trainings"
    icon = "fa-solid fa-chalkboard-user"
    category = "Training"

    column_list = [Training.id, Training.title_en, Training.duration_en, Training.available]
    column_searchable_list = [Training.title_en]
    column_filters = [BooleanFilter(Training.available)]
    page_size = 25


class TrainingBookingAdmin(ModelView, model=TrainingBooking):
    name = "Training Booking"
    name_plural = "Training Bookings"
    icon = "fa-solid fa-calendar-check"
    category = "Training"

    column_list = [
        TrainingBooking.id, TrainingBooking.training, TrainingBooking.farmer,
        TrainingBooking.user_phone, TrainingBooking.preferred_date,
        TrainingBooking.status, TrainingBooking.created_at,
    ]
    column_searchable_list = [TrainingBooking.user_phone]
    column_filters = [
        StaticValuesFilter(
            TrainingBooking.status,
            values=[("pending", "Pending"), ("confirmed", "Confirmed"), ("done", "Done")],
        )
    ]
    column_default_sort = [(TrainingBooking.created_at, True)]
    form_columns = [TrainingBooking.status, TrainingBooking.preferred_date]
    can_create = False
    page_size = 25


class DeliveryLocationAdmin(ModelView, model=DeliveryLocation):
    name = "Delivery Location"
    name_plural = "Delivery Locations"
    icon = "fa-solid fa-location-dot"
    category = "Customers"

    column_list = [
        DeliveryLocation.id, DeliveryLocation.farmer, DeliveryLocation.name,
        DeliveryLocation.district, DeliveryLocation.sector, DeliveryLocation.is_default,
    ]
    column_searchable_list = [DeliveryLocation.name, DeliveryLocation.district]
    column_filters = [
        AllUniqueStringValuesFilter(DeliveryLocation.district),
        BooleanFilter(DeliveryLocation.is_default),
    ]
    can_create = False
    page_size = 25


class NotificationAdmin(ModelView, model=Notification):
    name = "Notification"
    name_plural = "Notifications"
    icon = "fa-solid fa-bell"
    category = "Support"

    column_list = [
        Notification.id, Notification.farmer, Notification.category,
        Notification.title, Notification.read, Notification.created_at,
    ]
    column_searchable_list = [Notification.title, Notification.body]
    column_filters = [
        StaticValuesFilter(
            Notification.category,
            values=[("order", "Order"), ("delivery", "Delivery"), ("promo", "Promo"), ("feedback", "Feedback")],
        ),
        BooleanFilter(Notification.read),
    ]
    column_default_sort = [(Notification.created_at, True)]
    can_create = False
    page_size = 25


class SupportRequestAdmin(ModelView, model=SupportRequest):
    name = "Support Request"
    name_plural = "Support Requests"
    icon = "fa-solid fa-headset"
    category = "Support"

    column_list = [
        SupportRequest.id, SupportRequest.phone, SupportRequest.email,
        SupportRequest.message, SupportRequest.resolved, SupportRequest.created_at,
    ]
    column_searchable_list = [SupportRequest.email, SupportRequest.phone]
    column_filters = [BooleanFilter(SupportRequest.resolved)]
    column_default_sort = [(SupportRequest.created_at, True)]
    form_columns = [SupportRequest.resolved]
    can_create = False
    page_size = 25


class OTPAdmin(ModelView, model=OTP):
    # Included mainly for debugging OTP delivery issues in dev — codes are
    # short-lived, but hidden from list/search by default for safety.
    name = "OTP Log"
    name_plural = "OTP Logs"
    icon = "fa-solid fa-key"
    category = "Support"

    column_list = [OTP.id, OTP.phone, OTP.verified, OTP.expires_at, OTP.created_at]
    column_searchable_list = [OTP.phone]
    column_filters = [BooleanFilter(OTP.verified)]
    column_default_sort = [(OTP.created_at, True)]
    can_create = False
    can_edit = False
    page_size = 25


ALL_ADMIN_VIEWS = [
    FarmerAdmin, OrderAdmin, OrderItemAdmin, ProductAdmin, RetailerAdmin,
    TrainingAdmin, TrainingBookingAdmin, DeliveryLocationAdmin,
    NotificationAdmin, SupportRequestAdmin, OTPAdmin,
]
