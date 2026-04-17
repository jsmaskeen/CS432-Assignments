from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from api.routes import rides as rides_route
from models.booking import Booking
from models.chat_message import RideChatMessage
from models.member import Member
from models.ride import Ride
from models.ride_participant import RideParticipant
from models.settlement import CostSettlement
from models.shard_directory import RideShardDirectory
from schemas.ride import RideCreateRequest


def _make_sessionmaker() -> sessionmaker:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Member.__table__.create(bind=engine, checkfirst=True)
    Ride.__table__.create(bind=engine, checkfirst=True)
    Booking.__table__.create(bind=engine, checkfirst=True)
    RideParticipant.__table__.create(bind=engine, checkfirst=True)
    RideChatMessage.__table__.create(bind=engine, checkfirst=True)
    CostSettlement.__table__.create(bind=engine, checkfirst=True)
    RideShardDirectory.__table__.create(bind=engine, checkfirst=True)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _insert_member(db, member_id: int) -> None:
    db.add(
        Member(
            MemberID=member_id,
            OAUTH_TOKEN=f"oauth_{member_id}",
            Email=f"member_{member_id}@iitgn.ac.in",
            Full_Name=f"Member {member_id}",
            Reputation_Score=Decimal("5.0"),
            Phone_Number=f"{member_id:010d}"[-10:],
            Gender="Other",
        )
    )


def test_list_rides_only_open_uses_open_filter(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_list_rides_across_shards(*, statuses, limit, order_desc):
        captured["statuses"] = statuses
        captured["limit"] = limit
        captured["order_desc"] = order_desc
        return ["ok"]

    monkeypatch.setattr(rides_route, "list_rides_across_shards", _fake_list_rides_across_shards)

    result = rides_route.list_rides(only_open=True, limit=12)

    assert result == ["ok"]
    assert captured == {
        "statuses": ("Open",),
        "limit": 12,
        "order_desc": False,
    }


def test_list_rides_open_and_full_filter(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_list_rides_across_shards(*, statuses, limit, order_desc):
        captured["statuses"] = statuses
        captured["limit"] = limit
        captured["order_desc"] = order_desc
        return ["ok"]

    monkeypatch.setattr(rides_route, "list_rides_across_shards", _fake_list_rides_across_shards)

    result = rides_route.list_rides(only_open=False, limit=30)

    assert result == ["ok"]
    assert captured == {
        "statuses": ("Open", "Full"),
        "limit": 30,
        "order_desc": False,
    }


def test_create_ride_writes_to_shard(monkeypatch) -> None:
    primary_maker = _make_sessionmaker()
    shard_makers = {
        0: _make_sessionmaker(),
        1: _make_sessionmaker(),
        2: _make_sessionmaker(),
    }

    with primary_maker() as db:
        _insert_member(db, 1)
        db.commit()

    for maker in shard_makers.values():
        with maker() as db:
            _insert_member(db, 1)
            db.commit()

    monkeypatch.setattr(rides_route, "SHARD_SESSION_MAKERS", shard_makers)
    monkeypatch.setattr(rides_route, "calculate_booking_distance_km", lambda *_args, **_kwargs: Decimal("12.50"))
    monkeypatch.setattr(rides_route, "audit_event", lambda **_kwargs: None)

    payload = RideCreateRequest(
        start_geohash="u09tun",
        end_geohash="u09tvw",
        departure_time=datetime(2026, 1, 1, 10, 0, 0),
        vehicle_type="Sedan",
        max_capacity=4,
        base_fare_per_km=Decimal("10.00"),
    )

    with primary_maker() as primary_db:
        ride = rides_route.create_ride(
            payload=payload,
            current_member=SimpleNamespace(MemberID=1),
            db=primary_db,
        )
        assert ride.RideID == 1

        directory_entry = primary_db.scalar(
            select(RideShardDirectory).where(RideShardDirectory.RideID == ride.RideID)
        )
        assert directory_entry is not None
        assert int(directory_entry.ShardID) == 0

    with shard_makers[0]() as shard_db:
        shard_ride = shard_db.scalar(select(Ride).where(Ride.RideID == 1))
        assert shard_ride is not None
        assert shard_ride.Ride_Status == "Open"

        shard_host_booking = shard_db.scalar(select(Booking).where(Booking.RideID == 1, Booking.Passenger_MemberID == 1))
        assert shard_host_booking is not None
        assert shard_host_booking.Booking_Status == "Confirmed"

        shard_host_participant = shard_db.scalar(
            select(RideParticipant).where(RideParticipant.RideID == 1, RideParticipant.MemberID == 1)
        )
        assert shard_host_participant is not None
        assert shard_host_participant.Role == "Host"

        shard_message = shard_db.scalar(select(RideChatMessage).where(RideChatMessage.RideID == 1))
        assert shard_message is not None


def test_start_ride_updates_status_on_shard(monkeypatch) -> None:
    shard_maker = _make_sessionmaker()

    with shard_maker() as db:
        _insert_member(db, 1)
        db.add(
            Ride(
                RideID=5,
                Host_MemberID=1,
                Start_GeoHash="u09tun",
                End_GeoHash="u09tvw",
                Departure_Time=datetime(2026, 1, 1, 10, 0, 0),
                Vehicle_Type="Sedan",
                Max_Capacity=4,
                Available_Seats=2,
                Base_Fare_Per_KM=Decimal("10.00"),
                Ride_Status="Open",
            )
        )
        db.commit()

    monkeypatch.setattr(rides_route, "audit_event", lambda **_kwargs: None)

    with shard_maker() as db:
        ride = rides_route.start_ride(
            ride_id=5,
            current_member=SimpleNamespace(MemberID=1),
            db=db,
        )
        assert ride.Ride_Status == "Started"

        persisted = db.scalar(select(Ride).where(Ride.RideID == 5))
        assert persisted is not None
        assert persisted.Ride_Status == "Started"


def test_end_ride_creates_settlement_on_shard(monkeypatch) -> None:
    shard_maker = _make_sessionmaker()

    with shard_maker() as db:
        _insert_member(db, 1)
        _insert_member(db, 2)
        db.add(
            Ride(
                RideID=8,
                Host_MemberID=1,
                Start_GeoHash="u09tun",
                End_GeoHash="u09tvw",
                Departure_Time=datetime(2026, 1, 1, 10, 0, 0),
                Vehicle_Type="Sedan",
                Max_Capacity=4,
                Available_Seats=2,
                Base_Fare_Per_KM=Decimal("10.00"),
                Ride_Status="Started",
            )
        )
        db.flush()
        db.add(
            Booking(
                BookingID=21,
                RideID=8,
                Passenger_MemberID=2,
                Booking_Status="Confirmed",
                Pickup_GeoHash="u09tun",
                Drop_GeoHash="u09tvw",
                Distance_Travelled_KM=Decimal("4.00"),
            )
        )
        db.commit()

    monkeypatch.setattr(rides_route, "consume_failure", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(rides_route, "audit_event", lambda **_kwargs: None)

    with shard_maker() as db:
        ride = rides_route.end_ride(
            ride_id=8,
            current_member=SimpleNamespace(MemberID=1),
            db=db,
        )
        assert ride.Ride_Status == "Completed"

        settlement = db.scalar(select(CostSettlement).where(CostSettlement.BookingID == 21))
        assert settlement is not None
        assert settlement.Calculated_Cost == Decimal("40.00")
        assert settlement.Payment_Status == "Unpaid"


def test_delete_ride_deletes_from_shard(monkeypatch) -> None:
    shard_maker = _make_sessionmaker()

    with shard_maker() as db:
        _insert_member(db, 1)
        db.add(
            Ride(
                RideID=11,
                Host_MemberID=1,
                Start_GeoHash="u09tun",
                End_GeoHash="u09tvw",
                Departure_Time=datetime(2026, 1, 1, 10, 0, 0),
                Vehicle_Type="Sedan",
                Max_Capacity=4,
                Available_Seats=2,
                Base_Fare_Per_KM=Decimal("10.00"),
                Ride_Status="Open",
            )
        )
        db.commit()

    monkeypatch.setattr(rides_route, "audit_event", lambda **_kwargs: None)

    with shard_maker() as db:
        response = rides_route.delete_ride(
            ride_id=11,
            admin_credential=SimpleNamespace(MemberID=1, Username="admin"),
            db=db,
        )
        assert response == {"message": "Ride deleted"}
        assert db.scalar(select(Ride).where(Ride.RideID == 11)) is None
