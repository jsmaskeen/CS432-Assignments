from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import func, select

from db.sharding import SHARD_SESSION_MAKERS, VALID_SHARD_IDS
from models.booking import Booking
from models.ride import Ride

RIDE_STATUS_BUCKETS = ("Open", "Started", "Full", "Cancelled", "Completed")
BOOKING_STATUS_BUCKETS = ("Pending", "Confirmed", "Rejected", "Cancelled")


def list_rides_across_shards(
    *,
    statuses: Sequence[str],
    limit: int | None = None,
    order_desc: bool = False,
) -> list[Ride]:
    if not statuses:
        return []

    unique_statuses = tuple(dict.fromkeys(statuses))
    rides: list[Ride] = []

    for shard_id in VALID_SHARD_IDS:
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            stmt = select(Ride).where(Ride.Ride_Status.in_(unique_statuses))
            if order_desc:
                stmt = stmt.order_by(Ride.Departure_Time.desc(), Ride.RideID.desc())
            else:
                stmt = stmt.order_by(Ride.Departure_Time.asc(), Ride.RideID.asc())

            if limit is not None:
                stmt = stmt.limit(limit)

            rides.extend(list(shard_db.scalars(stmt)))
        finally:
            shard_db.close()

    rides.sort(key=lambda ride: (ride.Departure_Time, ride.RideID), reverse=order_desc)
    if limit is not None:
        return rides[:limit]
    return rides


def aggregate_ride_booking_stats_across_shards() -> dict[str, int | float]:
    ride_counts = {status: 0 for status in RIDE_STATUS_BUCKETS}
    booking_counts = {status: 0 for status in BOOKING_STATUS_BUCKETS}

    total_rides = 0
    total_bookings = 0
    total_capacity_seats = 0
    total_available_seats = 0
    total_base_fare_sum = Decimal("0")

    for shard_id in VALID_SHARD_IDS:
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            ride_status_rows = shard_db.execute(
                select(
                    Ride.Ride_Status,
                    func.count(Ride.RideID),
                ).group_by(Ride.Ride_Status)
            ).all()
            for ride_status, count in ride_status_rows:
                count_int = int(count or 0)
                total_rides += count_int
                if ride_status in ride_counts:
                    ride_counts[ride_status] += count_int

            capacity_row = shard_db.execute(
                select(
                    func.coalesce(func.sum(Ride.Max_Capacity), 0),
                    func.coalesce(func.sum(Ride.Available_Seats), 0),
                    func.coalesce(func.sum(Ride.Base_Fare_Per_KM), 0),
                )
            ).one()
            total_capacity_seats += int(capacity_row[0] or 0)
            total_available_seats += int(capacity_row[1] or 0)

            fare_sum = capacity_row[2]
            if fare_sum is not None:
                if isinstance(fare_sum, Decimal):
                    total_base_fare_sum += fare_sum
                else:
                    total_base_fare_sum += Decimal(str(fare_sum))

            booking_status_rows = shard_db.execute(
                select(
                    Booking.Booking_Status,
                    func.count(Booking.BookingID),
                ).group_by(Booking.Booking_Status)
            ).all()
            for booking_status, count in booking_status_rows:
                count_int = int(count or 0)
                total_bookings += count_int
                if booking_status in booking_counts:
                    booking_counts[booking_status] += count_int
        finally:
            shard_db.close()

    average_base_fare = float((total_base_fare_sum / total_rides) if total_rides > 0 else Decimal("0"))

    return {
        "total_rides": total_rides,
        "open_rides": ride_counts["Open"],
        "full_rides": ride_counts["Full"],
        "cancelled_rides": ride_counts["Cancelled"],
        "completed_rides": ride_counts["Completed"],
        "total_bookings": total_bookings,
        "pending_bookings": booking_counts["Pending"],
        "confirmed_bookings": booking_counts["Confirmed"],
        "rejected_bookings": booking_counts["Rejected"],
        "cancelled_bookings": booking_counts["Cancelled"],
        "total_capacity_seats": total_capacity_seats,
        "total_available_seats": total_available_seats,
        "average_base_fare_per_km": average_base_fare,
    }
