from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RideCreateRequest(BaseModel):
    start_geohash: str = Field(min_length=4, max_length=20)
    end_geohash: str = Field(min_length=4, max_length=20)
    departure_time: datetime
    vehicle_type: str = Field(min_length=2, max_length=50)
    max_capacity: int = Field(ge=1, le=10)
    base_fare_per_km: Decimal = Field(gt=0)


class RideUpdateRequest(BaseModel):
    start_geohash: str | None = Field(default=None, min_length=4, max_length=20)
    end_geohash: str | None = Field(default=None, min_length=4, max_length=20)
    departure_time: datetime | None = None
    vehicle_type: str | None = Field(default=None, min_length=2, max_length=50)
    max_capacity: int | None = Field(default=None, ge=1, le=10)
    base_fare_per_km: Decimal | None = Field(default=None, gt=0)


class RideReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    RideID: int
    Host_MemberID: int
    Start_GeoHash: str
    End_GeoHash: str
    Departure_Time: datetime
    Vehicle_Type: str
    Max_Capacity: int
    Available_Seats: int
    Base_Fare_Per_KM: Decimal
    Ride_Status: str


class RideWithBookingsResponse(BaseModel):
    ride: RideReadResponse
    bookings: list[BookingReadResponse]


class BookingCreateRequest(BaseModel):
    pickup_geohash: str = Field(min_length=4, max_length=20)
    drop_geohash: str = Field(min_length=4, max_length=20)
    distance_travelled_km: Decimal = Field(gt=0)


class BookingReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    BookingID: int
    RideID: int
    Passenger_MemberID: int
    Booking_Status: str
    Pickup_GeoHash: str
    Drop_GeoHash: str
    Distance_Travelled_KM: Decimal
    Booked_At: datetime
