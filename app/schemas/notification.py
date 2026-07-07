from typing import Optional

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    user_phone: Optional[str] = None
    category: str = "order"
    title: str
    body: str
    order_id: Optional[str] = None


class MarkAllReadIn(BaseModel):
    phone: Optional[str] = None
