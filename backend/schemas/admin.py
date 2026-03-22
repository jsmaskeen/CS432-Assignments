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
    request_id: str | None = None
    action: str
    status: str
    actor_member_id: int | None = None
    actor_username: str | None = None
    details: dict


class UnauthorizedDbModificationReadResponse(BaseModel):
    log_id: int
    table_name: str
    operation: str
    primary_key_name: str
    primary_key_value: str
    db_user: str
    connection_id: int
    app_request_id: str | None = None
    app_actor_member_id: int | None = None
    app_actor_username: str | None = None
    app_actor_role: str | None = None
    source_tag: str
    is_authorized: bool
    old_values_json: dict | None = None
    new_values_json: dict | None = None
    created_at: datetime


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


class AdminRideReadResponse(BaseModel):
    ride_id: int
    host_member_id: int
    start_geohash: str
    end_geohash: str
    departure_time: datetime
    vehicle_type: str
    max_capacity: int
    available_seats: int
    base_fare_per_km: float
    ride_status: str
    created_at: datetime


class AdminRideParticipantResponse(BaseModel):
    member_id: int
    full_name: str
    email: EmailStr
    phone_number: str | None = None
    gender: str
    is_host: bool
    booking_id: int | None = None
    booking_status: str | None = None
