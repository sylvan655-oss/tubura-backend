from typing import Optional

from pydantic import BaseModel, EmailStr


class SupportRequestIn(BaseModel):
    phone: Optional[str] = None
    email: EmailStr
    message: str
