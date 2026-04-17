from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import settings
from db.sharding import shard_id_for_ride_id, validate_shard_id
from models.shard_directory import ReviewShardDirectory, RideShardDirectory, RideShardRangeDirectory


def _ride_shard_lookup_mode() -> str:
    mode = settings.RIDE_SHARD_LOOKUP_MODE.strip().lower()
    if mode in {"modulo", "directory_exact", "directory_range"}:
        return mode
    return "modulo"


def _resolve_ride_shard_from_directory(ride_id: int, db: Session) -> int | None:
    entry = db.scalar(select(RideShardDirectory).where(RideShardDirectory.RideID == ride_id))
    if entry is None:
        return None
    return validate_shard_id(int(entry.ShardID))


def _resolve_ride_shard_from_range_directory(ride_id: int, db: Session) -> int | None:
    entries = db.scalars(select(RideShardRangeDirectory).order_by(RideShardRangeDirectory.MinRideID.asc())).all()
    for entry in entries:
        if ride_id < int(entry.MinRideID):
            continue
        max_ride_id = entry.MaxRideID
        if max_ride_id is None or ride_id <= int(max_ride_id):
            return validate_shard_id(int(entry.ShardID))
    return None


def _resolve_ride_shard(ride_id: int, db: Session) -> tuple[int, str]:
    mode = _ride_shard_lookup_mode()
    if mode == "directory_exact":
        shard_id = _resolve_ride_shard_from_directory(ride_id, db)
        if shard_id is not None:
            return shard_id, "ride_id_directory_exact"
    elif mode == "directory_range":
        shard_id = _resolve_ride_shard_from_range_directory(ride_id, db)
        if shard_id is not None:
            return shard_id, "ride_id_range_directory"

    return shard_id_for_ride_id(ride_id), "ride_id_mod_3"


def get_ride_shard_id(ride_id: int, db: Session) -> int:
    if ride_id <= 0:
        raise ValueError(f"ride_id must be positive, got {ride_id}")

    shard_id, _ = _resolve_ride_shard(ride_id, db)
    return shard_id


def get_or_create_ride_shard_id(ride_id: int, db: Session) -> int:
    if ride_id <= 0:
        raise ValueError(f"ride_id must be positive, got {ride_id}")

    shard_id, strategy = _resolve_ride_shard(ride_id, db)

    entry = db.scalar(select(RideShardDirectory).where(RideShardDirectory.RideID == ride_id))
    if entry is None:
        db.add(
            RideShardDirectory(
                RideID=ride_id,
                ShardID=shard_id,
                Strategy=strategy,
            )
        )
    else:
        entry.ShardID = shard_id
        entry.Strategy = strategy

    db.flush()
    return shard_id


def upsert_ride_shard_range(min_ride_id: int, max_ride_id: int | None, shard_id: int, db: Session) -> int:
    if min_ride_id <= 0:
        raise ValueError(f"min_ride_id must be positive, got {min_ride_id}")
    if max_ride_id is not None and max_ride_id < min_ride_id:
        raise ValueError("max_ride_id must be >= min_ride_id when provided")

    shard_id = validate_shard_id(shard_id)
    max_clause = (
        RideShardRangeDirectory.MaxRideID.is_(None)
        if max_ride_id is None
        else RideShardRangeDirectory.MaxRideID == max_ride_id
    )
    entry = db.scalar(
        select(RideShardRangeDirectory).where(
            RideShardRangeDirectory.MinRideID == min_ride_id,
            max_clause,
        )
    )

    if entry is None:
        db.add(
            RideShardRangeDirectory(
                MinRideID=min_ride_id,
                MaxRideID=max_ride_id,
                ShardID=shard_id,
                Strategy="ride_id_range_directory",
            )
        )
    else:
        entry.ShardID = shard_id
        entry.Strategy = "ride_id_range_directory"

    db.flush()
    return shard_id


def get_review_shard_id(review_id: int, db: Session) -> int | None:
    entry = db.scalar(select(ReviewShardDirectory).where(ReviewShardDirectory.ReviewID == review_id))
    if entry is None:
        return None
    return int(entry.ShardID)


def upsert_review_shard_id(review_id: int, shard_id: int, db: Session) -> int:
    shard_id = validate_shard_id(shard_id)
    entry = db.scalar(select(ReviewShardDirectory).where(ReviewShardDirectory.ReviewID == review_id))
    if entry is None:
        db.add(
            ReviewShardDirectory(
                ReviewID=review_id,
                ShardID=shard_id,
                Strategy="review_ride_shard",
            )
        )
    else:
        entry.ShardID = shard_id
        entry.Strategy = "review_ride_shard"

    db.flush()
    return shard_id


def delete_review_shard_id(review_id: int, db: Session) -> None:
    entry = db.scalar(select(ReviewShardDirectory).where(ReviewShardDirectory.ReviewID == review_id))
    if entry is not None:
        db.delete(entry)
        db.flush()
