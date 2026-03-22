from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SettlementCreateRequest(BaseModel):
    booking_id: int


class SettlementStatusUpdateRequest(BaseModel):
    payment_status: str = Field(pattern="^(Unpaid|Settled)$")


class SettlementReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    SettlementID: int
    BookingID: int
    Calculated_Cost: Decimal
    Payment_Status: str
