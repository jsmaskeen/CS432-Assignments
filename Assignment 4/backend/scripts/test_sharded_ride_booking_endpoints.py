from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import requests
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.security import hash_password
from db.session import SessionLocal
from db.sharding import SHARD_SESSION_MAKERS, shard_id_for_ride_id
from models.auth_credential import AuthCredential
from models.booking import Booking
from models.member import Member
from models.ride import Ride

DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1"
DEFAULT_PASSWORD = "password123"
GEOHASH_ALPHABET = "0123456789bcdefghjkmnpqrstuvwxyz"
MAX_BOOKING_DISTANCE_KM = Decimal("9999.99")
MIN_BOOKING_DISTANCE_KM = Decimal("1.00")


@dataclass(frozen=True)
class RideContext:
    ride_id: int
    host_member_id: int
    passenger_member_id: int
    start_geohash: str
    end_geohash: str


def build_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def request_json(
    session: requests.Session,
    base_url: str,
    method: str,
    path: str,
    *,
    token: str | None = None,
    json_body: dict[str, Any] | None = None,
    expected_status: int = 200,
) -> dict[str, Any]:
    headers = dict(session.headers)
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    response = session.request(
        method=method,
        url=build_url(base_url, path),
        json=json_body,
        headers=headers,
        timeout=20,
    )
    if response.status_code != expected_status:
        raise RuntimeError(
            f"{method} {path} expected {expected_status}, got {response.status_code}: {response.text}"
        )
    if not response.text.strip():
        return {}
    return response.json()


def request_raw(
    session: requests.Session,
    base_url: str,
    method: str,
    path: str,
    *,
    token: str | None = None,
    json_body: dict[str, Any] | None = None,
) -> requests.Response:
    headers = dict(session.headers)
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    return session.request(
        method=method,
        url=build_url(base_url, path),
        json=json_body,
        headers=headers,
        timeout=20,
    )


def login_fake_user(session: requests.Session, base_url: str, member_id: int) -> str:
    username = f"fake_user_{member_id}"
    response = session.post(
        build_url(base_url, "/auth/login"),
        json={"username": username, "password": DEFAULT_PASSWORD},
        timeout=20,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Login failed for {username}: {response.status_code} {response.text}")
    token = response.json().get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError(f"Login response for {username} did not include an access_token")
    return token


def make_valid_geohash(seed: str, length: int = 6) -> str:
    if length < 4:
        raise ValueError("Geohash length must be at least 4")

    digest = hashlib.sha256(seed.lower().encode("utf-8") or b"u").digest()
    chars = [GEOHASH_ALPHABET[digest[index % len(digest)] % len(GEOHASH_ALPHABET)] for index in range(length)]
    return "".join(chars)


def decode_geohash(value: str) -> tuple[float, float]:
    base32_map = {char: index for index, char in enumerate(GEOHASH_ALPHABET)}
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]
    is_even = True

    for char in value.lower().strip():
        bits = base32_map[char]
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


def estimate_booking_distance_km(start_geohash: str, end_geohash: str) -> Decimal:
    start_lat, start_lon = decode_geohash(start_geohash)
    end_lat, end_lon = decode_geohash(end_geohash)

    lat1 = math.radians(start_lat)
    lon1 = math.radians(start_lon)
    lat2 = math.radians(end_lat)
    lon2 = math.radians(end_lon)
    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    c = 2 * math.asin(min(1.0, math.sqrt(a)))
    distance_km = Decimal(str(6371.0 * c))
    return distance_km.quantize(Decimal("0.01"))


def make_nearby_geohash_pair(seed: str, length: int = 6) -> tuple[str, str]:
    """Generate a geohash pair likely to satisfy booking distance constraints without external network calls."""
    for attempt in range(64):
        start = make_valid_geohash(f"{seed}-{attempt}", length)
        base_idx_1 = GEOHASH_ALPHABET.index(start[-1])
        base_idx_2 = GEOHASH_ALPHABET.index(start[-2])

        for delta2 in range(1, 12):
            for delta1 in range(1, len(GEOHASH_ALPHABET)):
                end = (
                    start[:-2]
                    + GEOHASH_ALPHABET[(base_idx_2 + delta2) % len(GEOHASH_ALPHABET)]
                    + GEOHASH_ALPHABET[(base_idx_1 + delta1) % len(GEOHASH_ALPHABET)]
                )

                if end == start:
                    continue

                try:
                    km = estimate_booking_distance_km(start, end)
                except Exception:
                    continue

                if MIN_BOOKING_DISTANCE_KM <= km <= MAX_BOOKING_DISTANCE_KM:
                    return start, end

    raise RuntimeError("Could not generate a booking geohash pair within valid distance bounds")


def create_booking_with_retry(
    session: requests.Session,
    base_url: str,
    ride_id: int,
    token: str,
    preferred_pair: tuple[str, str],
    seed: str,
) -> dict[str, Any]:
    known_pairs = [
        ("u09tun", "u09tvw"),
        ("dr5reg", "dr5ru6"),
        ("9q8yyk", "9q8zn1"),
        ("gcpvj0", "gcpvj9"),
    ]

    candidates: list[tuple[str, str]] = [preferred_pair]
    for idx in range(80):
        try:
            candidates.append(make_nearby_geohash_pair(f"{seed}-{idx}"))
        except Exception:
            continue
    candidates.extend(known_pairs)

    last_error = ""
    for pickup_geohash, drop_geohash in candidates:
        response = request_raw(
            session,
            base_url,
            "POST",
            f"/rides/{ride_id}/book",
            token=token,
            json_body={"pickup_geohash": pickup_geohash, "drop_geohash": drop_geohash},
        )

        if response.status_code == 201:
            return response.json()

        detail = response.text
        last_error = f"{response.status_code}: {detail}"
        if response.status_code == 400 and "Distance must be greater than 0" in detail:
            continue
        if response.status_code == 400 and "Out of range value" in detail:
            continue

        raise RuntimeError(
            f"POST /rides/{ride_id}/book failed with non-retryable error {response.status_code}: {response.text}"
        )

    raise RuntimeError(
        f"POST /rides/{ride_id}/book could not find a valid geohash pair after retries. Last error: {last_error}"
    )


def get_max_member_id() -> int:
    max_member_id = 0

    with SessionLocal() as primary_db:
        primary_max = primary_db.scalar(select(func.max(Member.MemberID))) or 0
        max_member_id = max(max_member_id, int(primary_max))

    for shard_id in (0, 1, 2):
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            shard_max = shard_db.scalar(select(func.max(Member.MemberID))) or 0
            max_member_id = max(max_member_id, int(shard_max))
        finally:
            shard_db.close()

    return max_member_id


def mirror_member_to_shards(member: Member, credential: AuthCredential) -> None:
    for shard_id in (0, 1, 2):
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            shard_member = shard_db.scalar(select(Member).where(Member.MemberID == member.MemberID))
            if shard_member is None:
                shard_db.add(
                    Member(
                        MemberID=member.MemberID,
                        OAUTH_TOKEN=member.OAUTH_TOKEN,
                        Email=member.Email,
                        Full_Name=member.Full_Name,
                        Reputation_Score=member.Reputation_Score,
                        Phone_Number=member.Phone_Number,
                        Created_At=member.Created_At,
                        Gender=member.Gender,
                    )
                )
                shard_db.flush()

            shard_credential = shard_db.scalar(
                select(AuthCredential).where(AuthCredential.MemberID == credential.MemberID)
            )
            if shard_credential is None:
                shard_db.add(
                    AuthCredential(
                        MemberID=credential.MemberID,
                        Username=credential.Username,
                        Password_Hash=credential.Password_Hash,
                        Role=credential.Role,
                        Created_At=credential.Created_At,
                    )
                )

            shard_db.commit()
        finally:
            shard_db.close()


def ensure_fake_users(target_count: int = 2) -> list[Member]:
    with SessionLocal() as db:
        fake_members = list(
            db.scalars(
                select(Member)
                .join(AuthCredential, AuthCredential.MemberID == Member.MemberID)
                .where(AuthCredential.Username.like("fake_user_%"))
                .order_by(Member.MemberID.asc())
            )
        )

        if len(fake_members) >= target_count:
            return fake_members

        now = datetime.now(UTC)
        next_member_id = get_max_member_id() + 1
        needed = target_count - len(fake_members)
        created_members: list[Member] = []

        for index in range(needed):
            member_id = next_member_id + index
            member = Member(
                MemberID=member_id,
                OAUTH_TOKEN=f"oauth_fake_{member_id}",
                Email=f"fake_{member_id}@iitgn.ac.in",
                Full_Name=f"Fake User {member_id}",
                Reputation_Score=Decimal("5.0"),
                Phone_Number=f"{member_id:010d}"[-10:],
                Created_At=now,
                Gender="Other",
            )
            db.add(member)
            db.flush()
            credential = AuthCredential(
                MemberID=member.MemberID,
                Username=f"fake_user_{member.MemberID}",
                Password_Hash=hash_password(DEFAULT_PASSWORD),
                Role="user",
                Created_At=now,
            )
            db.add(credential)
            created_members.append(member)

        db.commit()

        for member in created_members:
            credential = db.scalar(select(AuthCredential).where(AuthCredential.MemberID == member.MemberID))
            if credential is not None:
                mirror_member_to_shards(member, credential)

        fake_members.extend(created_members)
        return fake_members[:target_count]


def choose_member(db: Session, ride: Ride, excluded_member_ids: set[int]) -> int | None:
    stmt = (
        select(Member.MemberID)
        .join(AuthCredential, AuthCredential.MemberID == Member.MemberID)
        .where(AuthCredential.Username.like("fake_user_%"))
        .where(Member.MemberID != ride.Host_MemberID)
    )
    if excluded_member_ids:
        stmt = stmt.where(~Member.MemberID.in_(excluded_member_ids))

    booked_member_ids = set(
        db.scalars(select(Booking.Passenger_MemberID).where(Booking.RideID == ride.RideID)).all()
    )
    if booked_member_ids:
        stmt = stmt.where(~Member.MemberID.in_(booked_member_ids))

    return db.scalar(stmt.order_by(Member.MemberID.asc()))


def get_max_ride_id() -> int:
    max_ride_id = 0

    with SessionLocal() as primary_db:
        primary_max = primary_db.scalar(select(func.max(Ride.RideID))) or 0
        max_ride_id = max(max_ride_id, int(primary_max))

    for shard_id in (0, 1, 2):
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            shard_max = shard_db.scalar(select(func.max(Ride.RideID))) or 0
            max_ride_id = max(max_ride_id, int(shard_max))
        finally:
            shard_db.close()

    return max_ride_id


def mirror_ride_to_primary(ride: Ride) -> None:
    with SessionLocal() as primary_db:
        existing = primary_db.scalar(select(Ride).where(Ride.RideID == ride.RideID))
        if existing is not None:
            return

        primary_db.add(
            Ride(
                RideID=ride.RideID,
                Host_MemberID=ride.Host_MemberID,
                Start_GeoHash=ride.Start_GeoHash,
                End_GeoHash=ride.End_GeoHash,
                Departure_Time=ride.Departure_Time,
                Vehicle_Type=ride.Vehicle_Type,
                Max_Capacity=ride.Max_Capacity,
                Available_Seats=ride.Available_Seats,
                Base_Fare_Per_KM=ride.Base_Fare_Per_KM,
                Ride_Status=ride.Ride_Status,
                Created_At=ride.Created_At,
            )
        )
        primary_db.commit()


def create_test_ride_for_shard(
    shard_id: int,
    host_member_id: int,
    passenger_member_id: int,
    ride_index: int,
) -> RideContext:
    candidate = get_max_ride_id() + 1
    while shard_id_for_ride_id(candidate) != shard_id:
        candidate += 1

    now = datetime.now(UTC)
    start_geohash = make_valid_geohash(f"shard{shard_id}ride{ride_index}start", 6)
    end_geohash = make_valid_geohash(f"shard{shard_id}ride{ride_index}end", 6)
    suffix = 0
    while start_geohash == end_geohash:
        suffix += 1
        end_geohash = make_valid_geohash(f"shard{shard_id}ride{ride_index}end{suffix}", 6)

    ride = Ride(
        RideID=candidate,
        Host_MemberID=host_member_id,
        Start_GeoHash=start_geohash,
        End_GeoHash=end_geohash,
        Departure_Time=now + timedelta(hours=24 + ride_index),
        Vehicle_Type="Sedan",
        Max_Capacity=4,
        Available_Seats=3,
        Base_Fare_Per_KM=Decimal("12.50"),
        Ride_Status="Open",
        Created_At=now,
    )

    shard_db = SHARD_SESSION_MAKERS[shard_id]()
    try:
        shard_db.add(ride)
        shard_db.commit()
        shard_db.refresh(ride)
    finally:
        shard_db.close()

    mirror_ride_to_primary(ride)
    return RideContext(
        ride_id=ride.RideID,
        host_member_id=host_member_id,
        passenger_member_id=passenger_member_id,
        start_geohash=start_geohash,
        end_geohash=end_geohash,
    )


def find_or_create_ride_contexts() -> list[RideContext]:
    with SessionLocal() as db:
        rides = list(
            db.scalars(
                select(Ride)
                .where(Ride.Ride_Status == "Open")
                .where(Ride.Available_Seats > 0)
                .order_by(Ride.RideID.asc())
            )
        )

        contexts: list[RideContext] = []
        used_passenger_ids: set[int] = set()

        for ride in rides:
            host_credential = db.scalar(select(AuthCredential).where(AuthCredential.MemberID == ride.Host_MemberID))
            if host_credential is None or not host_credential.Username.startswith("fake_user_"):
                continue

            passenger_member_id = choose_member(db, ride, used_passenger_ids)
            if passenger_member_id is None:
                continue

            contexts.append(
                RideContext(
                    ride_id=ride.RideID,
                    host_member_id=ride.Host_MemberID,
                    passenger_member_id=passenger_member_id,
                    start_geohash=ride.Start_GeoHash,
                    end_geohash=ride.End_GeoHash,
                )
            )
            used_passenger_ids.add(passenger_member_id)
            if len(contexts) >= 2:
                break

        if len(contexts) >= 2:
            return contexts

        fake_members = ensure_fake_users(2)

    return [
        create_test_ride_for_shard(0, fake_members[0].MemberID, fake_members[1].MemberID, 1),
        create_test_ride_for_shard(1, fake_members[1].MemberID, fake_members[0].MemberID, 2),
    ]


def mirror_booking_to_primary(booking_payload: dict[str, Any]) -> None:
    with SessionLocal() as primary_db:
        existing = primary_db.scalar(select(Booking).where(Booking.BookingID == booking_payload["BookingID"]))
        if existing is not None:
            return

        primary_db.add(
            Booking(
                BookingID=booking_payload["BookingID"],
                RideID=booking_payload["RideID"],
                Passenger_MemberID=booking_payload["Passenger_MemberID"],
                Booking_Status=booking_payload["Booking_Status"],
                Pickup_GeoHash=booking_payload["Pickup_GeoHash"],
                Drop_GeoHash=booking_payload["Drop_GeoHash"],
                Distance_Travelled_KM=Decimal(str(booking_payload["Distance_Travelled_KM"])),
            )
        )
        primary_db.commit()


def future_iso(hours_ahead: int) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours_ahead)).isoformat()


def run_flow_accept_and_delete(
    session: requests.Session,
    base_url: str,
    context: RideContext,
) -> dict[str, Any]:
    host_token = login_fake_user(session, base_url, context.host_member_id)
    passenger_token = login_fake_user(session, base_url, context.passenger_member_id)

    ride_before = request_json(session, base_url, "GET", f"/rides/{context.ride_id}", token=host_token)
    ride_patch = request_json(
        session,
        base_url,
        "PATCH",
        f"/rides/{context.ride_id}",
        token=host_token,
        json_body={"departure_time": future_iso(36)},
    )
    with_bookings_before = request_json(
        session,
        base_url,
        "GET",
        f"/rides/{context.ride_id}/with-bookings",
        token=host_token,
    )
    pending_before = request_json(
        session,
        base_url,
        "GET",
        f"/rides/{context.ride_id}/bookings/pending",
        token=host_token,
    )
    pickup_geohash, drop_geohash = make_nearby_geohash_pair(f"ride-{context.ride_id}-accept")
    booking_created = create_booking_with_retry(
        session,
        base_url,
        context.ride_id,
        passenger_token,
        (pickup_geohash, drop_geohash),
        f"ride-{context.ride_id}-accept",
    )
    mirror_booking_to_primary(booking_created)
    pending_after = request_json(
        session,
        base_url,
        "GET",
        f"/rides/{context.ride_id}/bookings/pending",
        token=host_token,
    )
    accepted_booking = request_json(
        session,
        base_url,
        "POST",
        f"/rides/bookings/{booking_created['BookingID']}/accept",
        token=host_token,
    )
    confirmed_after_accept = request_json(
        session,
        base_url,
        "GET",
        f"/rides/{context.ride_id}/bookings/confirmed-stops",
        token=host_token,
    )
    deleted_booking = request_json(
        session,
        base_url,
        "DELETE",
        f"/rides/bookings/{booking_created['BookingID']}",
        token=passenger_token,
    )
    with_bookings_after = request_json(
        session,
        base_url,
        "GET",
        f"/rides/{context.ride_id}/with-bookings",
        token=host_token,
    )

    return {
        "ride_id": context.ride_id,
        "flow": "accept_and_delete",
        "ride_before": ride_before,
        "ride_patch": ride_patch,
        "with_bookings_before": with_bookings_before,
        "pending_before": pending_before,
        "booking_created": booking_created,
        "pending_after": pending_after,
        "accepted_booking": accepted_booking,
        "confirmed_after_accept": confirmed_after_accept,
        "deleted_booking": deleted_booking,
        "with_bookings_after": with_bookings_after,
    }


def run_flow_reject(
    session: requests.Session,
    base_url: str,
    context: RideContext,
) -> dict[str, Any]:
    host_token = login_fake_user(session, base_url, context.host_member_id)
    passenger_token = login_fake_user(session, base_url, context.passenger_member_id)

    ride_before = request_json(session, base_url, "GET", f"/rides/{context.ride_id}", token=host_token)
    ride_patch = request_json(
        session,
        base_url,
        "PATCH",
        f"/rides/{context.ride_id}",
        token=host_token,
        json_body={"departure_time": future_iso(48)},
    )
    with_bookings_before = request_json(
        session,
        base_url,
        "GET",
        f"/rides/{context.ride_id}/with-bookings",
        token=host_token,
    )
    pending_before = request_json(
        session,
        base_url,
        "GET",
        f"/rides/{context.ride_id}/bookings/pending",
        token=host_token,
    )
    pickup_geohash, drop_geohash = make_nearby_geohash_pair(f"ride-{context.ride_id}-reject")
    booking_created = create_booking_with_retry(
        session,
        base_url,
        context.ride_id,
        passenger_token,
        (pickup_geohash, drop_geohash),
        f"ride-{context.ride_id}-reject",
    )
    mirror_booking_to_primary(booking_created)
    pending_after = request_json(
        session,
        base_url,
        "GET",
        f"/rides/{context.ride_id}/bookings/pending",
        token=host_token,
    )
    rejected_booking = request_json(
        session,
        base_url,
        "POST",
        f"/rides/bookings/{booking_created['BookingID']}/reject",
        token=host_token,
    )
    confirmed_after_reject = request_json(
        session,
        base_url,
        "GET",
        f"/rides/{context.ride_id}/bookings/confirmed-stops",
        token=host_token,
    )

    return {
        "ride_id": context.ride_id,
        "flow": "reject",
        "ride_before": ride_before,
        "ride_patch": ride_patch,
        "with_bookings_before": with_bookings_before,
        "pending_before": pending_before,
        "booking_created": booking_created,
        "pending_after": pending_after,
        "rejected_booking": rejected_booking,
        "confirmed_after_reject": confirmed_after_reject,
    }


def run_test(base_url: str) -> dict[str, Any]:
    contexts = find_or_create_ride_contexts()
    session = requests.Session()

    return {
        "base_url": base_url,
        "flows": [
            run_flow_accept_and_delete(session, base_url, contexts[0]),
            run_flow_reject(session, base_url, contexts[1]),
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Test sharded ride and booking endpoints")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base API URL, including /api/v1")
    args = parser.parse_args()

    summary = run_test(args.base_url)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()