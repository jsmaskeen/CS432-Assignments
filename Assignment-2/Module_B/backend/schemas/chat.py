from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    MessageID: int
    RideID: int
    Sender_MemberID: int
    Sender_Name: str | None = None
    Message_Body: str
    Sent_At: datetime
