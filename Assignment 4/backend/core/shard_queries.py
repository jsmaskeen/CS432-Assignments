from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
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
    def _fetch_rides_for_shard(shard_id: int) -> list[Ride]:
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            stmt = select(Ride).where(Ride.Ride_Status.in_(unique_statuses))
            if order_desc:
                stmt = stmt.order_by(Ride.Departure_Time.desc(), Ride.RideID.desc())
            else:
                stmt = stmt.order_by(Ride.Departure_Time.asc(), Ride.RideID.asc())

            if limit is not None:
                stmt = stmt.limit(limit)

            return list(shard_db.scalars(stmt))
        finally:
            shard_db.close()

    rides: list[Ride] = []
    max_workers = max(1, len(VALID_SHARD_IDS))
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="rides-list-shard") as executor:
        futures = [executor.submit(_fetch_rides_for_shard, shard_id) for shard_id in VALID_SHARD_IDS]
        for future in futures:
            rides.extend(future.result())

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

    def _fetch_shard_stats(shard_id: int) -> dict[str, object]:
        local_ride_counts = {status: 0 for status in RIDE_STATUS_BUCKETS}
        local_booking_counts = {status: 0 for status in BOOKING_STATUS_BUCKETS}
        local_total_rides = 0
        local_total_bookings = 0
        local_total_capacity_seats = 0
        local_total_available_seats = 0
        local_total_base_fare_sum = Decimal("0")

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
                local_total_rides += count_int
                if ride_status in local_ride_counts:
                    local_ride_counts[ride_status] += count_int

            capacity_row = shard_db.execute(
                select(
                    func.coalesce(func.sum(Ride.Max_Capacity), 0),
                    func.coalesce(func.sum(Ride.Available_Seats), 0),
                    func.coalesce(func.sum(Ride.Base_Fare_Per_KM), 0),
                )
            ).one()
            local_total_capacity_seats += int(capacity_row[0] or 0)
            local_total_available_seats += int(capacity_row[1] or 0)

            fare_sum = capacity_row[2]
            if fare_sum is not None:
                if isinstance(fare_sum, Decimal):
                    local_total_base_fare_sum += fare_sum
                else:
                    local_total_base_fare_sum += Decimal(str(fare_sum))

            booking_status_rows = shard_db.execute(
                select(
                    Booking.Booking_Status,
                    func.count(Booking.BookingID),
                ).group_by(Booking.Booking_Status)
            ).all()
            for booking_status, count in booking_status_rows:
                count_int = int(count or 0)
                local_total_bookings += count_int
                if booking_status in local_booking_counts:
                    local_booking_counts[booking_status] += count_int
        finally:
            shard_db.close()

        return {
            "total_rides": local_total_rides,
            "ride_counts": local_ride_counts,
            "total_bookings": local_total_bookings,
            "booking_counts": local_booking_counts,
            "total_capacity_seats": local_total_capacity_seats,
            "total_available_seats": local_total_available_seats,
            "total_base_fare_sum": local_total_base_fare_sum,
        }

    max_workers = max(1, len(VALID_SHARD_IDS))
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="rides-stats-shard") as executor:
        futures = [executor.submit(_fetch_shard_stats, shard_id) for shard_id in VALID_SHARD_IDS]
        for future in futures:
            shard_stats = future.result()
            total_rides += int(shard_stats["total_rides"])
            total_bookings += int(shard_stats["total_bookings"])
            total_capacity_seats += int(shard_stats["total_capacity_seats"])
            total_available_seats += int(shard_stats["total_available_seats"])
            total_base_fare_sum += shard_stats["total_base_fare_sum"]

            for ride_status, count in shard_stats["ride_counts"].items():
                ride_counts[ride_status] += int(count)

            for booking_status, count in shard_stats["booking_counts"].items():
                booking_counts[booking_status] += int(count)

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
