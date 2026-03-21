from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AdminMemberReadResponse(BaseModel):
    member_id: int
    username: str
    role: str
    email: EmailStr
    full_name: str
    created_at: datetime


class AdminMemberRoleUpdateRequest(BaseModel):
    role: str = Field(pattern="^(user|admin)$")


class AuditLogReadResponse(BaseModel):
    ts: str
    action: str
    status: str
    actor_member_id: int | None = None
    actor_username: str | None = None
    details: dict
