from typing import Optional, List

from pydantic import BaseModel, Field


class RequestOTP(BaseModel):
    phone: str


class VerifyOTP(BaseModel):
    phone: str
    code: str


class SignupIn(BaseModel):
    name: str
    phone: str
    dob: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    sector: Optional[str] = None
    cell: Optional[str] = None
    village: Optional[str] = None
    customer_type: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    crops: List[str] = Field(default_factory=list)
    password: Optional[str] = None


class LoginIn(BaseModel):
    phone: str
    password: str


class FarmerOut(BaseModel):
    id: int
    phone: str
    name: str
    farmer_id: Optional[str] = None
    district: Optional[str] = None
    province: Optional[str] = None
    sector: Optional[str] = None
    cell: Optional[str] = None
    village: Optional[str] = None
    customer_type: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    crops: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    farmer: FarmerOut
