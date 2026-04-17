from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core import shard_queries
from models.booking import Booking
from models.member import Member
from models.ride import Ride


def _make_sqlite_shard_session_makers() -> dict[int, sessionmaker]:
    session_makers: dict[int, sessionmaker] = {}
    for shard_id in (0, 1, 2):
        engine = create_engine(
            "sqlite+pysqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Member.__table__.create(bind=engine, checkfirst=True)
        Ride.__table__.create(bind=engine, checkfirst=True)
        Booking.__table__.create(bind=engine, checkfirst=True)
        session_makers[shard_id] = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return session_makers


def _insert_member(db, member_id: int) -> None:
    db.add(
        Member(
            MemberID=member_id,
            OAUTH_TOKEN=f"oauth_{member_id}",
            Email=f"user_{member_id}@iitgn.ac.in",
            Full_Name=f"User {member_id}",
            Reputation_Score=Decimal("5.0"),
            Phone_Number=f"{member_id:010d}"[-10:],
            Gender="Other",
        )
    )


def test_list_rides_across_shards_merges_globally_with_limit(monkeypatch) -> None:
    session_makers = _make_sqlite_shard_session_makers()
    monkeypatch.setattr(shard_queries, "SHARD_SESSION_MAKERS", session_makers)
    monkeypatch.setattr(shard_queries, "VALID_SHARD_IDS", (0, 1, 2))

    with session_makers[0]() as db:
        _insert_member(db, 1)
        db.add_all(
            [
                Ride(
                    RideID=1,
                    Host_MemberID=1,
                    Start_GeoHash="u09tun",
                    End_GeoHash="u09tvw",
                    Departure_Time=datetime(2026, 1, 1, 10, 0, 0),
                    Vehicle_Type="Sedan",
                    Max_Capacity=4,
                    Available_Seats=2,
                    Base_Fare_Per_KM=Decimal("10.00"),
                    Ride_Status="Open",
                ),
                Ride(
                    RideID=4,
                    Host_MemberID=1,
                    Start_GeoHash="u09tun",
                    End_GeoHash="u09tvw",
                    Departure_Time=datetime(2026, 1, 1, 9, 0, 0),
                    Vehicle_Type="Sedan",
                    Max_Capacity=4,
                    Available_Seats=0,
                    Base_Fare_Per_KM=Decimal("12.00"),
                    Ride_Status="Full",
                ),
            ]
        )
        db.commit()

    with session_makers[1]() as db:
        _insert_member(db, 2)
        db.add_all(
            [
                Ride(
                    RideID=2,
                    Host_MemberID=2,
                    Start_GeoHash="u09tun",
                    End_GeoHash="u09tvw",
                    Departure_Time=datetime(2026, 1, 1, 8, 0, 0),
                    Vehicle_Type="Bike",
                    Max_Capacity=2,
                    Available_Seats=1,
                    Base_Fare_Per_KM=Decimal("8.00"),
                    Ride_Status="Open",
                ),
                Ride(
                    RideID=5,
                    Host_MemberID=2,
                    Start_GeoHash="u09tun",
                    End_GeoHash="u09tvw",
                    Departure_Time=datetime(2026, 1, 1, 11, 0, 0),
                    Vehicle_Type="SUV",
                    Max_Capacity=5,
                    Available_Seats=0,
                    Base_Fare_Per_KM=Decimal("15.00"),
                    Ride_Status="Full",
                ),
            ]
        )
        db.commit()

    with session_makers[2]() as db:
        _insert_member(db, 3)
        db.add(
            Ride(
                RideID=6,
                Host_MemberID=3,
                Start_GeoHash="u09tun",
                End_GeoHash="u09tvw",
                Departure_Time=datetime(2026, 1, 1, 9, 30, 0),
                Vehicle_Type="Mini",
                Max_Capacity=3,
                Available_Seats=1,
                Base_Fare_Per_KM=Decimal("9.00"),
                Ride_Status="Open",
            )
        )
        db.commit()

    rides = shard_queries.list_rides_across_shards(
        statuses=("Open", "Full"),
        limit=3,
        order_desc=False,
    )

    assert [ride.RideID for ride in rides] == [2, 4, 6]


def test_aggregate_ride_booking_stats_across_shards(monkeypatch) -> None:
    session_makers = _make_sqlite_shard_session_makers()
    monkeypatch.setattr(shard_queries, "SHARD_SESSION_MAKERS", session_makers)
    monkeypatch.setattr(shard_queries, "VALID_SHARD_IDS", (0, 1, 2))

    with session_makers[0]() as db:
        _insert_member(db, 1)
        _insert_member(db, 11)
        db.add_all(
            [
                Ride(
                    RideID=1,
                    Host_MemberID=1,
                    Start_GeoHash="u09tun",
                    End_GeoHash="u09tvw",
                    Departure_Time=datetime(2026, 1, 1, 8, 0, 0),
                    Vehicle_Type="Sedan",
                    Max_Capacity=4,
                    Available_Seats=2,
                    Base_Fare_Per_KM=Decimal("10.00"),
                    Ride_Status="Open",
                ),
                Ride(
                    RideID=4,
                    Host_MemberID=1,
                    Start_GeoHash="u09tun",
                    End_GeoHash="u09tvw",
                    Departure_Time=datetime(2026, 1, 1, 9, 0, 0),
                    Vehicle_Type="Sedan",
                    Max_Capacity=3,
                    Available_Seats=0,
                    Base_Fare_Per_KM=Decimal("20.00"),
                    Ride_Status="Completed",
                ),
            ]
        )
        db.add_all(
            [
                Booking(
                    BookingID=1,
                    RideID=1,
                    Passenger_MemberID=11,
                    Booking_Status="Pending",
                    Pickup_GeoHash="u09tun",
                    Drop_GeoHash="u09tvw",
                    Distance_Travelled_KM=Decimal("5.00"),
                ),
                Booking(
                    BookingID=2,
                    RideID=4,
                    Passenger_MemberID=11,
                    Booking_Status="Confirmed",
                    Pickup_GeoHash="u09tun",
                    Drop_GeoHash="u09tvw",
                    Distance_Travelled_KM=Decimal("5.00"),
                ),
            ]
        )
        db.commit()

    with session_makers[1]() as db:
        _insert_member(db, 2)
        _insert_member(db, 12)
        db.add_all(
            [
                Ride(
                    RideID=2,
                    Host_MemberID=2,
                    Start_GeoHash="u09tun",
                    End_GeoHash="u09tvw",
                    Departure_Time=datetime(2026, 1, 1, 8, 30, 0),
                    Vehicle_Type="Bike",
                    Max_Capacity=2,
                    Available_Seats=0,
                    Base_Fare_Per_KM=Decimal("15.00"),
                    Ride_Status="Full",
                ),
                Ride(
                    RideID=5,
                    Host_MemberID=2,
                    Start_GeoHash="u09tun",
                    End_GeoHash="u09tvw",
                    Departure_Time=datetime(2026, 1, 1, 9, 30, 0),
                    Vehicle_Type="SUV",
                    Max_Capacity=5,
                    Available_Seats=5,
                    Base_Fare_Per_KM=Decimal("25.00"),
                    Ride_Status="Cancelled",
                ),
            ]
        )
        db.add_all(
            [
                Booking(
                    BookingID=3,
                    RideID=2,
                    Passenger_MemberID=12,
                    Booking_Status="Rejected",
                    Pickup_GeoHash="u09tun",
                    Drop_GeoHash="u09tvw",
                    Distance_Travelled_KM=Decimal("3.00"),
                ),
                Booking(
                    BookingID=4,
                    RideID=5,
                    Passenger_MemberID=12,
                    Booking_Status="Cancelled",
                    Pickup_GeoHash="u09tun",
                    Drop_GeoHash="u09tvw",
                    Distance_Travelled_KM=Decimal("3.00"),
                ),
            ]
        )
        db.commit()

    with session_makers[2]() as db:
        _insert_member(db, 3)
        _insert_member(db, 13)
        db.add(
            Ride(
                RideID=3,
                Host_MemberID=3,
                Start_GeoHash="u09tun",
                End_GeoHash="u09tvw",
                Departure_Time=datetime(2026, 1, 1, 10, 0, 0),
                Vehicle_Type="Mini",
                Max_Capacity=6,
                Available_Seats=4,
                Base_Fare_Per_KM=Decimal("30.00"),
                Ride_Status="Started",
            )
        )
        db.add(
            Booking(
                BookingID=5,
                RideID=3,
                Passenger_MemberID=13,
                Booking_Status="Confirmed",
                Pickup_GeoHash="u09tun",
                Drop_GeoHash="u09tvw",
                Distance_Travelled_KM=Decimal("2.00"),
            )
        )
        db.commit()

    stats = shard_queries.aggregate_ride_booking_stats_across_shards()

    assert int(stats["total_rides"]) == 5
    assert int(stats["open_rides"]) == 1
    assert int(stats["full_rides"]) == 1
    assert int(stats["cancelled_rides"]) == 1
    assert int(stats["completed_rides"]) == 1

    assert int(stats["total_bookings"]) == 5
    assert int(stats["pending_bookings"]) == 1
    assert int(stats["confirmed_bookings"]) == 2
    assert int(stats["rejected_bookings"]) == 1
    assert int(stats["cancelled_bookings"]) == 1

    assert int(stats["total_capacity_seats"]) == 20
    assert int(stats["total_available_seats"]) == 11
    assert float(stats["average_base_fare_per_km"]) == 20.0
