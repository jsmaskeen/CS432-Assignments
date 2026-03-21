from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AdminMemberReadResponse(BaseModel):
    member_id: int
    username: str
    role: str
    email: EmailStr
    full_name: str
    reputation_score: float
    phone_number: str | None = None
    gender: str
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


class AdminRideStatsResponse(BaseModel):
    total_members: int
    total_rides: int
    open_rides: int
    full_rides: int
    cancelled_rides: int
    completed_rides: int
    total_bookings: int
    pending_bookings: int
    confirmed_bookings: int
    rejected_bookings: int
    cancelled_bookings: int
    total_capacity_seats: int
    total_available_seats: int
    total_booked_seats: int
    average_base_fare_per_km: float
