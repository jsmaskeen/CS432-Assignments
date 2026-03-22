from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    MemberID: int
    Email: EmailStr
    Full_Name: str
    Reputation_Score: Decimal
    Phone_Number: str | None
    Created_At: datetime
    Gender: str
