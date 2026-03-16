from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class MemberCreate(BaseModel):
    oauth_token: str = Field(min_length=3, max_length=100)
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)
    phone_number: str | None = Field(default=None, max_length=15)
    gender: str = Field(pattern="^(Male|Female|Other)$")

    @field_validator("email")
    @classmethod
    def validate_iitgn_domain(cls, value: EmailStr) -> EmailStr:
        if not str(value).endswith("@iitgn.ac.in"):
            raise ValueError("Only @iitgn.ac.in email addresses are allowed")
        return value


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    MemberID: int
    OAUTH_TOKEN: str
    Email: EmailStr
    Full_Name: str
    Reputation_Score: Decimal
    Phone_Number: str | None
    Created_At: datetime
    Gender: str
