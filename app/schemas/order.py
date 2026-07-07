from typing import Optional, List

from pydantic import BaseModel


class OrderItemIn(BaseModel):
    id: Optional[int] = None
    name: str
    price: float
    unit: Optional[str] = None
    img: Optional[str] = None
    qty: int = 1


class OrderCreate(BaseModel):
    user_phone: Optional[str] = None
    retailer_id: Optional[int] = None
    delivery_method: str = "pickup"
    speed: Optional[str] = None
    payment_method: str = "mtn_momo"
    items: List[OrderItemIn]
