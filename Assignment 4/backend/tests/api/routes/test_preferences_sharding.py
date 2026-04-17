from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from api.routes import preferences as preferences_route
from models.member import Member
from models.preference import UserPreference
from schemas.preference import PreferenceUpsertRequest


def _make_sessionmaker() -> sessionmaker:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Member.__table__.create(bind=engine, checkfirst=True)
    UserPreference.__table__.create(bind=engine, checkfirst=True)
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


def test_my_preference_reads_from_shard_before_primary(monkeypatch) -> None:
    primary_maker = _make_sessionmaker()
    shard_makers = {
        0: _make_sessionmaker(),
        1: _make_sessionmaker(),
        2: _make_sessionmaker(),
    }

    with primary_maker() as db:
        _insert_member(db, 1)
        db.add(
            UserPreference(
                MemberID=1,
                Gender_Preference="Any",
                Notify_On_New_Ride=False,
                Music_Preference="Classical",
            )
        )
        db.commit()

    with shard_makers[2]() as db:
        _insert_member(db, 1)
        db.add(
            UserPreference(
                MemberID=1,
                Gender_Preference="Same-Gender Only",
                Notify_On_New_Ride=True,
                Music_Preference="Rock",
            )
        )
        db.commit()

    monkeypatch.setattr(preferences_route, "SHARD_SESSION_MAKERS", shard_makers)

    with primary_maker() as primary_db:
        pref = preferences_route.my_preference(
            current_member=SimpleNamespace(MemberID=1),
            db=primary_db,
        )

    assert pref is not None
    assert pref.Gender_Preference == "Same-Gender Only"
    assert pref.Notify_On_New_Ride is True
    assert pref.Music_Preference == "Rock"


def test_upsert_preference_writes_to_all_member_shards(monkeypatch) -> None:
    primary_maker = _make_sessionmaker()
    shard_makers = {
        0: _make_sessionmaker(),
        1: _make_sessionmaker(),
        2: _make_sessionmaker(),
    }

    with primary_maker() as db:
        _insert_member(db, 7)
        db.commit()

    with shard_makers[0]() as db:
        _insert_member(db, 7)
        db.commit()

    with shard_makers[2]() as db:
        _insert_member(db, 7)
        db.add(
            UserPreference(
                MemberID=7,
                Gender_Preference="Any",
                Notify_On_New_Ride=False,
                Music_Preference="Old",
            )
        )
        db.commit()

    monkeypatch.setattr(preferences_route, "SHARD_SESSION_MAKERS", shard_makers)
    monkeypatch.setattr(preferences_route, "audit_event", lambda **_kwargs: None)

    payload = PreferenceUpsertRequest(
        gender_preference="Same-Gender Only",
        notify_on_new_ride=True,
        music_preference="Lo-fi",
    )
    with primary_maker() as primary_db:
        pref = preferences_route.upsert_preference(
            payload=payload,
            current_member=SimpleNamespace(MemberID=7),
            db=primary_db,
        )

    assert pref.MemberID == 7
    assert pref.Gender_Preference == "Same-Gender Only"
    assert pref.Notify_On_New_Ride is True
    assert pref.Music_Preference == "Lo-fi"

    with shard_makers[0]() as db:
        shard_pref = db.scalar(select(UserPreference).where(UserPreference.MemberID == 7))
        assert shard_pref is not None
        assert shard_pref.Gender_Preference == "Same-Gender Only"
        assert shard_pref.Notify_On_New_Ride is True
        assert shard_pref.Music_Preference == "Lo-fi"

    with shard_makers[2]() as db:
        shard_pref = db.scalar(select(UserPreference).where(UserPreference.MemberID == 7))
        assert shard_pref is not None
        assert shard_pref.Gender_Preference == "Same-Gender Only"
        assert shard_pref.Notify_On_New_Ride is True
        assert shard_pref.Music_Preference == "Lo-fi"

    with shard_makers[1]() as db:
        shard_pref = db.scalar(select(UserPreference).where(UserPreference.MemberID == 7))
        assert shard_pref is None


def test_upsert_preference_falls_back_to_primary_when_member_not_in_shards(monkeypatch) -> None:
    primary_maker = _make_sessionmaker()
    shard_makers = {
        0: _make_sessionmaker(),
        1: _make_sessionmaker(),
        2: _make_sessionmaker(),
    }

    with primary_maker() as db:
        _insert_member(db, 42)
        db.commit()

    monkeypatch.setattr(preferences_route, "SHARD_SESSION_MAKERS", shard_makers)
    monkeypatch.setattr(preferences_route, "audit_event", lambda **_kwargs: None)

    payload = PreferenceUpsertRequest(
        gender_preference="Any",
        notify_on_new_ride=True,
        music_preference="Jazz",
    )
    with primary_maker() as primary_db:
        pref = preferences_route.upsert_preference(
            payload=payload,
            current_member=SimpleNamespace(MemberID=42),
            db=primary_db,
        )

    assert pref.MemberID == 42
    assert pref.Gender_Preference == "Any"
    assert pref.Notify_On_New_Ride is True
    assert pref.Music_Preference == "Jazz"

    with primary_maker() as db:
        primary_pref = db.scalar(select(UserPreference).where(UserPreference.MemberID == 42))
        assert primary_pref is not None
        assert primary_pref.Music_Preference == "Jazz"

    with shard_makers[0]() as db:
        assert db.scalar(select(UserPreference).where(UserPreference.MemberID == 42)) is None
    with shard_makers[1]() as db:
        assert db.scalar(select(UserPreference).where(UserPreference.MemberID == 42)) is None
    with shard_makers[2]() as db:
        assert db.scalar(select(UserPreference).where(UserPreference.MemberID == 42)) is None