from typing import Optional

from pydantic import BaseModel


class DeliveryLocationIn(BaseModel):
    user_phone: Optional[str] = None
    name: str
    icon: Optional[str] = "pin"
    province: Optional[str] = None
    district: Optional[str] = None
    sector: Optional[str] = None
    cell: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DeliveryLocationUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    sector: Optional[str] = None
    cell: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
