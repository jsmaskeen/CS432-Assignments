from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings

NUM_SHARDS = 3
VALID_SHARD_IDS = (0, 1, 2)


def shard_id_for_ride_id(ride_id: int) -> int:
    if ride_id <= 0:
        raise ValueError(f"ride_id must be positive, got {ride_id}")
    return (ride_id - 1) % NUM_SHARDS


def validate_shard_id(shard_id: int) -> int:
    if shard_id not in VALID_SHARD_IDS:
        raise ValueError(f"Invalid shard_id={shard_id}. Expected one of {VALID_SHARD_IDS}")
    return shard_id


SHARD_ENGINES = {
    shard_id: create_engine(
        settings.shard_database_uri(shard_id),
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
    )
    for shard_id in VALID_SHARD_IDS
}

SHARD_SESSION_MAKERS = {
    shard_id: sessionmaker(bind=engine, autocommit=False, autoflush=False)
    for shard_id, engine in SHARD_ENGINES.items()
}


def get_shard_session(shard_id: int):
    shard_id = validate_shard_id(shard_id)
    db = SHARD_SESSION_MAKERS[shard_id]()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def shard_session_scope(shard_id: int):
    shard_id = validate_shard_id(shard_id)
    db = SHARD_SESSION_MAKERS[shard_id]()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
