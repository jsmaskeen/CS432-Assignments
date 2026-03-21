from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import requests
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from core.config import settings
from models.booking import Booking
from models.ride import Ride

_BASE32_MAP = {char: index for index, char in enumerate("0123456789bcdefghjkmnpqrstuvwxyz")}


def _decode_geohash(value: str) -> tuple[float, float]:
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]
    is_even = True

    for char in value.lower().strip():
        if char not in _BASE32_MAP:
            raise ValueError("Invalid geohash")
        bits = _BASE32_MAP[char]
        for mask in (16, 8, 4, 2, 1):
            if is_even:
                mid = (lon_interval[0] + lon_interval[1]) / 2
                if bits & mask:
                    lon_interval[0] = mid
                else:
                    lon_interval[1] = mid
            else:
                mid = (lat_interval[0] + lat_interval[1]) / 2
                if bits & mask:
                    lat_interval[0] = mid
                else:
                    lat_interval[1] = mid
            is_even = not is_even

    lat = (lat_interval[0] + lat_interval[1]) / 2
    lon = (lon_interval[0] + lon_interval[1]) / 2
    return lat, lon


def _ors_request(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not settings.ORS_API_KEY:
        raise RuntimeError("ORS_API_KEY is not configured")

    url = f"{settings.ORS_BASE_URL.rstrip('/')}{path}"
    response = requests.post(
        url,
        json=payload,
        headers={"Authorization": settings.ORS_API_KEY},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def recalculate_ride_route_and_distances(ride: Ride, db: Session) -> int:
    bookings = list(
        db.scalars(
            select(Booking).where(
                Booking.RideID == ride.RideID,
                Booking.Booking_Status == "Confirmed",
                Booking.Passenger_MemberID != ride.Host_MemberID,
            )
        )
    )
    if not bookings:
        return 0

    start_lat, start_lon = _decode_geohash(ride.Start_GeoHash)
    end_lat, end_lon = _decode_geohash(ride.End_GeoHash)

    shipments: list[dict[str, Any]] = []
    id_map: dict[int, tuple[str, int]] = {}
    next_id = 1
    for booking in bookings:
        pickup_lat, pickup_lon = _decode_geohash(booking.Pickup_GeoHash)
        drop_lat, drop_lon = _decode_geohash(booking.Drop_GeoHash)
        pickup_id = next_id
        delivery_id = next_id + 1
        next_id += 2

        id_map[pickup_id] = ("pickup", booking.BookingID)
        id_map[delivery_id] = ("delivery", booking.BookingID)

        shipments.append(
            {
                "pickup": {"id": pickup_id, "location": [pickup_lon, pickup_lat]},
                "delivery": {"id": delivery_id, "location": [drop_lon, drop_lat]},
            }
        )

    payload = {
        "vehicles": [
            {
                "id": 1,
                "profile": "driving-car",
                "start": [start_lon, start_lat],
                "end": [end_lon, end_lat],
            }
        ],
        "shipments": shipments,
    }

    data = _ors_request("/optimization", payload)
    routes = data.get("routes") or []
    if not routes:
        raise RuntimeError("ORS optimization returned no routes")

    activities = routes[0].get("activities") or []
    if not activities:
        raise RuntimeError("ORS optimization returned no activities")

    pickup_distances: dict[int, Decimal] = {}
    delivery_distances: dict[int, Decimal] = {}
    for activity in activities:
        activity_id = activity.get("id")
        if activity_id is None or activity_id not in id_map:
            continue
        distance = activity.get("distance")
        if distance is None:
            continue
        distance_km = Decimal(str(distance)) / Decimal("1000")
        kind, booking_id = id_map[activity_id]
        if kind == "pickup":
            pickup_distances[booking_id] = distance_km
        else:
            delivery_distances[booking_id] = distance_km

    updated = 0
    for booking in bookings:
        pickup_km = pickup_distances.get(booking.BookingID)
        delivery_km = delivery_distances.get(booking.BookingID)
        if pickup_km is None or delivery_km is None or delivery_km < pickup_km:
            continue
        distance_km = (delivery_km - pickup_km).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        booking.Distance_Travelled_KM = distance_km
        updated += 1

    return updated
