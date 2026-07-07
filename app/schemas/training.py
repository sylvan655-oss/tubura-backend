from typing import Optional

from pydantic import BaseModel


class TrainingRequestIn(BaseModel):
    user_phone: Optional[str] = None
    training_id: int
    preferred_date: Optional[str] = None
