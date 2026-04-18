from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core import sharding as sharding_core
from models.shard_directory import RideShardDirectory, RideShardRangeDirectory


def _make_sessionmaker() -> sessionmaker:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    RideShardDirectory.__table__.create(bind=engine, checkfirst=True)
    RideShardRangeDirectory.__table__.create(bind=engine, checkfirst=True)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def test_get_ride_shard_id_defaults_to_modulo(monkeypatch) -> None:
    monkeypatch.setattr(sharding_core.settings, "RIDE_SHARD_LOOKUP_MODE", "modulo")
    maker = _make_sessionmaker()

    with maker() as db:
        sharding_core.upsert_ride_shard_range(100, 199, 2, db)
        db.add(
            RideShardDirectory(
                RideID=150,
                ShardID=1,
                Strategy="manual_override",
            )
        )
        db.commit()

    with maker() as db:
        assert sharding_core.get_ride_shard_id(150, db) == 2
        assert sharding_core.get_ride_shard_id(10, db) == 0


def test_get_ride_shard_id_can_use_exact_directory(monkeypatch) -> None:
    monkeypatch.setattr(sharding_core.settings, "RIDE_SHARD_LOOKUP_MODE", "directory_exact")
    maker = _make_sessionmaker()

    with maker() as db:
        db.add(
            RideShardDirectory(
                RideID=120,
                ShardID=2,
                Strategy="manual_override",
            )
        )
        db.commit()

    with maker() as db:
        assert sharding_core.get_ride_shard_id(120, db) == 2
        assert sharding_core.get_ride_shard_id(10, db) == 0


def test_get_ride_shard_id_can_use_range_directory(monkeypatch) -> None:
    monkeypatch.setattr(sharding_core.settings, "RIDE_SHARD_LOOKUP_MODE", "directory_range")
    maker = _make_sessionmaker()

    with maker() as db:
        sharding_core.upsert_ride_shard_range(100, 199, 1, db)
        db.commit()

    with maker() as db:
        assert sharding_core.get_ride_shard_id(150, db) == 1
        assert sharding_core.get_ride_shard_id(10, db) == 0


def test_get_or_create_ride_shard_id_persists_modulo_strategy(monkeypatch) -> None:
    monkeypatch.setattr(sharding_core.settings, "RIDE_SHARD_LOOKUP_MODE", "modulo")
    maker = _make_sessionmaker()

    with maker() as db:
        shard_id = sharding_core.get_or_create_ride_shard_id(1234, db)
        assert shard_id == ((1234 - 1) % 3)

        directory_entry = db.query(RideShardDirectory).filter(RideShardDirectory.RideID == 1234).one()
        assert int(directory_entry.ShardID) == ((1234 - 1) % 3)
        assert directory_entry.Strategy == "ride_id_mod_3"


def test_get_or_create_ride_shard_id_persists_exact_directory_strategy(monkeypatch) -> None:
    monkeypatch.setattr(sharding_core.settings, "RIDE_SHARD_LOOKUP_MODE", "directory_exact")
    maker = _make_sessionmaker()

    with maker() as db:
        db.add(RideShardDirectory(RideID=120, ShardID=2, Strategy="manual_override"))
        db.commit()

    with maker() as db:
        shard_id = sharding_core.get_or_create_ride_shard_id(120, db)
        assert shard_id == 2

        directory_entry = db.query(RideShardDirectory).filter(RideShardDirectory.RideID == 120).one()
        assert int(directory_entry.ShardID) == 2
        assert directory_entry.Strategy == "ride_id_directory_exact"


def test_get_or_create_ride_shard_id_persists_range_directory_strategy(monkeypatch) -> None:
    monkeypatch.setattr(sharding_core.settings, "RIDE_SHARD_LOOKUP_MODE", "directory_range")
    maker = _make_sessionmaker()

    with maker() as db:
        sharding_core.upsert_ride_shard_range(100, 199, 1, db)
        db.commit()

    with maker() as db:
        shard_id = sharding_core.get_or_create_ride_shard_id(150, db)
        assert shard_id == 1

        directory_entry = db.query(RideShardDirectory).filter(RideShardDirectory.RideID == 150).one()
        assert int(directory_entry.ShardID) == 1
        assert directory_entry.Strategy == "ride_id_range_directory"
