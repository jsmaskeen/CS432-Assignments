from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatCreateRequest(BaseModel):
    message_body: str = Field(min_length=1, max_length=2000)


class ChatReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    MessageID: int
    RideID: int
    Sender_MemberID: int
    Message_Body: str
    Sent_At: datetime
