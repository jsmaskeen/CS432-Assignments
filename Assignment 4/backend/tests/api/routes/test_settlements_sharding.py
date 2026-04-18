from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from api.routes import settlements as settlements_route
from models.booking import Booking
from models.member import Member
from models.ride import Ride
from models.settlement import CostSettlement
from schemas.settlement import SettlementStatusUpdateRequest


def _make_sessionmaker() -> sessionmaker:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Member.__table__.create(bind=engine, checkfirst=True)
    Ride.__table__.create(bind=engine, checkfirst=True)
    Booking.__table__.create(bind=engine, checkfirst=True)
    CostSettlement.__table__.create(bind=engine, checkfirst=True)
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


def _insert_ride(db, *, ride_id: int, host_member_id: int, fare_per_km: Decimal, status: str) -> None:
    db.add(
        Ride(
            RideID=ride_id,
            Host_MemberID=host_member_id,
            Start_GeoHash="u09tun",
            End_GeoHash="u09tvw",
            Departure_Time=datetime(2026, 1, 1, 10, 0, 0),
            Vehicle_Type="Sedan",
            Max_Capacity=4,
            Available_Seats=2,
            Base_Fare_Per_KM=fare_per_km,
            Ride_Status=status,
        )
    )


def test_update_settlement_status_updates_record_on_resolved_shard(monkeypatch) -> None:
    shard_makers = {
        0: _make_sessionmaker(),
        1: _make_sessionmaker(),
        2: _make_sessionmaker(),
    }

    with shard_makers[2]() as db:
        _insert_member(db, 1)
        _insert_member(db, 2)
        _insert_ride(db, ride_id=9, host_member_id=1, fare_per_km=Decimal("10.00"), status="Completed")
        db.add(
            Booking(
                BookingID=90,
                RideID=9,
                Passenger_MemberID=2,
                Booking_Status="Confirmed",
                Pickup_GeoHash="u09tun",
                Drop_GeoHash="u09tvw",
                Distance_Travelled_KM=Decimal("3.00"),
            )
        )
        db.add(
            CostSettlement(
                SettlementID=900,
                BookingID=90,
                Calculated_Cost=Decimal("30.00"),
                Payment_Status="Unpaid",
            )
        )
        db.commit()

    monkeypatch.setattr(settlements_route, "SHARD_SESSION_MAKERS", shard_makers)
    monkeypatch.setattr(settlements_route, "audit_event", lambda **_kwargs: None)

    updated = settlements_route.update_settlement_status(
        settlement_id=900,
        payload=SettlementStatusUpdateRequest(payment_status="Settled"),
        current_member=SimpleNamespace(MemberID=2),
    )

    assert updated.SettlementID == 900
    assert updated.Payment_Status == "Settled"

    with shard_makers[2]() as db:
        persisted = db.scalar(select(CostSettlement).where(CostSettlement.SettlementID == 900))
        assert persisted is not None
        assert persisted.Payment_Status == "Settled"


def test_get_booking_settlement_resolves_shard_and_creates_missing_settlement(monkeypatch) -> None:
    primary_maker = _make_sessionmaker()
    shard_makers = {
        0: _make_sessionmaker(),
        1: _make_sessionmaker(),
        2: _make_sessionmaker(),
    }

    with shard_makers[1]() as db:
        _insert_member(db, 1)
        _insert_member(db, 2)
        _insert_ride(db, ride_id=5, host_member_id=1, fare_per_km=Decimal("10.00"), status="Completed")
        db.add(
            Booking(
                BookingID=50,
                RideID=5,
                Passenger_MemberID=2,
                Booking_Status="Confirmed",
                Pickup_GeoHash="u09tun",
                Drop_GeoHash="u09tvw",
                Distance_Travelled_KM=Decimal("4.00"),
            )
        )
        db.commit()

    monkeypatch.setattr(settlements_route, "SHARD_SESSION_MAKERS", shard_makers)
    monkeypatch.setattr(settlements_route, "audit_event", lambda **_kwargs: None)

    with primary_maker() as primary_db:
        settlement = settlements_route.get_booking_settlement(
            booking_id=50,
            current_member=SimpleNamespace(MemberID=2),
            primary_db=primary_db,
        )

    assert settlement is not None
    assert settlement.BookingID == 50
    assert settlement.Payment_Status == "Unpaid"
    assert settlement.Calculated_Cost == Decimal("40.00")

    with shard_makers[1]() as db:
        persisted = db.scalar(select(CostSettlement).where(CostSettlement.BookingID == 50))
        assert persisted is not None
        assert persisted.Calculated_Cost == Decimal("40.00")


def test_my_settlements_fans_out_and_merges_shard_results(monkeypatch) -> None:
    shard_makers = {
        0: _make_sessionmaker(),
        1: _make_sessionmaker(),
        2: _make_sessionmaker(),
    }

    with shard_makers[0]() as db:
        _insert_member(db, 1)
        _insert_member(db, 2)
        _insert_ride(db, ride_id=1, host_member_id=1, fare_per_km=Decimal("10.00"), status="Completed")
        db.add(
            Booking(
                BookingID=10,
                RideID=1,
                Passenger_MemberID=2,
                Booking_Status="Confirmed",
                Pickup_GeoHash="u09tun",
                Drop_GeoHash="u09tvw",
                Distance_Travelled_KM=Decimal("2.00"),
            )
        )
        db.commit()

    with shard_makers[1]() as db:
        _insert_member(db, 1)
        _insert_member(db, 2)
        _insert_ride(db, ride_id=2, host_member_id=1, fare_per_km=Decimal("12.00"), status="Completed")
        db.add(
            Booking(
                BookingID=20,
                RideID=2,
                Passenger_MemberID=2,
                Booking_Status="Confirmed",
                Pickup_GeoHash="u09tun",
                Drop_GeoHash="u09tvw",
                Distance_Travelled_KM=Decimal("1.00"),
            )
        )
        db.add(
            CostSettlement(
                SettlementID=500,
                BookingID=20,
                Calculated_Cost=Decimal("12.00"),
                Payment_Status="Settled",
            )
        )
        db.commit()

    monkeypatch.setattr(settlements_route, "SHARD_SESSION_MAKERS", shard_makers)
    monkeypatch.setattr(settlements_route, "audit_event", lambda **_kwargs: None)

    settlements = settlements_route.my_settlements(current_member=SimpleNamespace(MemberID=2))

    assert len(settlements) == 2
    assert {settlement.BookingID for settlement in settlements} == {10, 20}
    assert settlements[0].SettlementID == 500

    with shard_makers[0]() as db:
        created = db.scalar(select(CostSettlement).where(CostSettlement.BookingID == 10))
        assert created is not None
        assert created.Calculated_Cost == Decimal("20.00")