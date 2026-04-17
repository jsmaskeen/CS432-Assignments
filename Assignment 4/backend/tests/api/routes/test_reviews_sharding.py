from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from api.routes import reviews as reviews_route
from models.booking import Booking
from models.member import Member
from models.review import ReputationReview
from models.ride import Ride
from models.shard_directory import ReviewShardDirectory
from schemas.review import ReviewCreateRequest


def _make_sessionmaker() -> sessionmaker:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Member.__table__.create(bind=engine, checkfirst=True)
    Ride.__table__.create(bind=engine, checkfirst=True)
    Booking.__table__.create(bind=engine, checkfirst=True)
    ReputationReview.__table__.create(bind=engine, checkfirst=True)
    ReviewShardDirectory.__table__.create(bind=engine, checkfirst=True)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _insert_member(db, member_id: int, *, name: str | None = None) -> None:
    db.add(
        Member(
            MemberID=member_id,
            OAUTH_TOKEN=f"oauth_{member_id}",
            Email=f"member_{member_id}@iitgn.ac.in",
            Full_Name=name or f"Member {member_id}",
            Reputation_Score=Decimal("5.0"),
            Phone_Number=f"{member_id:010d}"[-10:],
            Gender="Other",
        )
    )


def _insert_ride(db, *, ride_id: int, host_member_id: int, status: str = "Completed") -> None:
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
            Base_Fare_Per_KM=Decimal("10.00"),
            Ride_Status=status,
        )
    )


def test_create_review_writes_to_resolved_shard(monkeypatch) -> None:
    primary_maker = _make_sessionmaker()
    shard_makers = {
        0: _make_sessionmaker(),
        1: _make_sessionmaker(),
        2: _make_sessionmaker(),
    }

    with primary_maker() as db:
        _insert_member(db, 1)
        _insert_member(db, 2)
        db.commit()

    with shard_makers[1]() as db:
        _insert_member(db, 1)
        _insert_member(db, 2)
        _insert_ride(db, ride_id=41, host_member_id=2, status="Completed")
        db.add(
            Booking(
                BookingID=401,
                RideID=41,
                Passenger_MemberID=1,
                Booking_Status="Confirmed",
                Pickup_GeoHash="u09tun",
                Drop_GeoHash="u09tvw",
                Distance_Travelled_KM=Decimal("3.00"),
            )
        )
        db.commit()

    monkeypatch.setattr(reviews_route, "SHARD_SESSION_MAKERS", shard_makers)
    monkeypatch.setattr(reviews_route, "get_ride_shard_id", lambda _ride_id, _db: 1)
    monkeypatch.setattr(reviews_route, "audit_event", lambda **_kwargs: None)

    payload = ReviewCreateRequest(
        ride_id=41,
        reviewee_member_id=2,
        rating=4,
        comments="good trip",
    )
    with primary_maker() as primary_db:
        review = reviews_route.create_review(
            payload=payload,
            current_member=SimpleNamespace(MemberID=1),
            primary_db=primary_db,
        )

    assert review.RideID == 41
    assert review.Reviewer_MemberID == 1
    assert review.Reviewee_MemberID == 2
    assert review.Rating == 4

    with shard_makers[1]() as db:
        shard_review = db.scalar(select(ReputationReview).where(ReputationReview.RideID == 41))
        assert shard_review is not None
        reviewee = db.scalar(select(Member).where(Member.MemberID == 2))
        assert reviewee is not None
        assert reviewee.Reputation_Score == Decimal("4.0")

    with primary_maker() as db:
        reviewee = db.scalar(select(Member).where(Member.MemberID == 2))
        assert reviewee is not None
        assert reviewee.Reputation_Score == Decimal("4.0")
        directory = db.scalar(select(ReviewShardDirectory).where(ReviewShardDirectory.ReviewID == review.ReviewID))
        assert directory is not None
        assert int(directory.ShardID) == 1

    with shard_makers[0]() as db:
        assert db.scalar(select(ReputationReview).where(ReputationReview.RideID == 41)) is None
    with shard_makers[2]() as db:
        assert db.scalar(select(ReputationReview).where(ReputationReview.RideID == 41)) is None


def test_list_ride_reviews_reads_from_resolved_shard(monkeypatch) -> None:
    primary_maker = _make_sessionmaker()
    shard_makers = {
        0: _make_sessionmaker(),
        1: _make_sessionmaker(),
        2: _make_sessionmaker(),
    }

    with primary_maker() as db:
        _insert_member(db, 10, name="Primary Reviewer")
        _insert_member(db, 11, name="Primary Reviewee")
        db.commit()

    with shard_makers[2]() as db:
        _insert_member(db, 10, name="Shard Reviewer")
        _insert_member(db, 11, name="Shard Reviewee")
        _insert_ride(db, ride_id=88, host_member_id=11, status="Completed")
        db.add(
            ReputationReview(
                ReviewID=880,
                RideID=88,
                Reviewer_MemberID=10,
                Reviewee_MemberID=11,
                Rating=5,
                Comments="excellent",
            )
        )
        db.commit()

    monkeypatch.setattr(reviews_route, "SHARD_SESSION_MAKERS", shard_makers)
    monkeypatch.setattr(reviews_route, "get_ride_shard_id", lambda _ride_id, _db: 2)

    with primary_maker() as primary_db:
        response = reviews_route.list_ride_reviews(
            ride_id=88,
            _=SimpleNamespace(MemberID=10),
            primary_db=primary_db,
        )

    assert len(response) == 1
    assert response[0]["ReviewID"] == 880
    assert response[0]["Reviewer_Name"] == "Primary Reviewer"
    assert response[0]["Reviewee_Name"] == "Primary Reviewee"


def test_list_member_reviews_fans_out_across_shards(monkeypatch) -> None:
    primary_maker = _make_sessionmaker()
    shard_makers = {
        0: _make_sessionmaker(),
        1: _make_sessionmaker(),
        2: _make_sessionmaker(),
    }

    with primary_maker() as db:
        _insert_member(db, 5, name="Target Member")
        _insert_member(db, 6, name="Reviewer A")
        _insert_member(db, 7, name="Reviewer B")
        db.commit()

    with shard_makers[0]() as db:
        _insert_member(db, 5)
        _insert_member(db, 6)
        _insert_ride(db, ride_id=1, host_member_id=5, status="Completed")
        db.add(
            ReputationReview(
                ReviewID=101,
                RideID=1,
                Reviewer_MemberID=6,
                Reviewee_MemberID=5,
                Rating=3,
                Comments="older",
                Created_At=datetime(2026, 1, 1, 8, 0, 0),
            )
        )
        db.commit()

    with shard_makers[1]() as db:
        _insert_member(db, 5)
        _insert_member(db, 7)
        _insert_ride(db, ride_id=2, host_member_id=7, status="Completed")
        db.add(
            ReputationReview(
                ReviewID=202,
                RideID=2,
                Reviewer_MemberID=5,
                Reviewee_MemberID=7,
                Rating=5,
                Comments="newer",
                Created_At=datetime(2026, 1, 1, 9, 0, 0),
            )
        )
        db.commit()

    monkeypatch.setattr(reviews_route, "SHARD_SESSION_MAKERS", shard_makers)

    with primary_maker() as primary_db:
        response = reviews_route.list_member_reviews(
            member_id=5,
            _=SimpleNamespace(MemberID=5),
            primary_db=primary_db,
        )

    assert len(response) == 2
    assert response[0]["ReviewID"] == 202
    assert response[1]["ReviewID"] == 101
    assert response[0]["Reviewer_Name"] == "Target Member"
    assert response[1]["Reviewee_Name"] == "Target Member"


def test_delete_review_uses_resolved_shard_and_recomputes_score(monkeypatch) -> None:
    primary_maker = _make_sessionmaker()
    shard_makers = {
        0: _make_sessionmaker(),
        1: _make_sessionmaker(),
        2: _make_sessionmaker(),
    }

    with primary_maker() as db:
        _insert_member(db, 1)
        _insert_member(db, 2)
        _insert_member(db, 3)
        db.commit()

    with shard_makers[0]() as db:
        _insert_member(db, 2)
        _insert_member(db, 3)
        _insert_ride(db, ride_id=10, host_member_id=2, status="Completed")
        db.add(
            ReputationReview(
                ReviewID=100,
                RideID=10,
                Reviewer_MemberID=3,
                Reviewee_MemberID=2,
                Rating=1,
                Comments="remaining review",
            )
        )
        db.commit()

    with shard_makers[2]() as db:
        _insert_member(db, 1)
        _insert_member(db, 2)
        _insert_ride(db, ride_id=20, host_member_id=2, status="Completed")
        db.add(
            ReputationReview(
                ReviewID=200,
                RideID=20,
                Reviewer_MemberID=1,
                Reviewee_MemberID=2,
                Rating=5,
                Comments="to delete",
            )
        )
        db.commit()

    monkeypatch.setattr(reviews_route, "SHARD_SESSION_MAKERS", shard_makers)
    monkeypatch.setattr(reviews_route, "audit_event", lambda **_kwargs: None)

    with primary_maker() as primary_db:
        response = reviews_route.delete_review(
            review_id=200,
            current_member=SimpleNamespace(MemberID=1),
            primary_db=primary_db,
        )

    assert response == {"message": "Review deleted"}

    with shard_makers[2]() as db:
        assert db.scalar(select(ReputationReview).where(ReputationReview.ReviewID == 200)) is None
        reviewee = db.scalar(select(Member).where(Member.MemberID == 2))
        assert reviewee is not None
        assert reviewee.Reputation_Score == Decimal("1.0")

    with shard_makers[0]() as db:
        reviewee = db.scalar(select(Member).where(Member.MemberID == 2))
        assert reviewee is not None
        assert reviewee.Reputation_Score == Decimal("1.0")

    with primary_maker() as db:
        reviewee = db.scalar(select(Member).where(Member.MemberID == 2))
        assert reviewee is not None
        assert reviewee.Reputation_Score == Decimal("1.0")
        directory = db.scalar(select(ReviewShardDirectory).where(ReviewShardDirectory.ReviewID == 200))
        assert directory is None