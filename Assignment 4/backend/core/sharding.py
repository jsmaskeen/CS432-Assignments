from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.sharding import shard_id_for_ride_id, validate_shard_id
from models.shard_directory import ReviewShardDirectory, RideShardDirectory


def get_ride_shard_id(ride_id: int, db: Session) -> int:
    entry = db.scalar(select(RideShardDirectory).where(RideShardDirectory.RideID == ride_id))
    if entry is None:
        return shard_id_for_ride_id(ride_id)
    return int(entry.ShardID)


def get_or_create_ride_shard_id(ride_id: int, db: Session) -> int:
    entry = db.scalar(select(RideShardDirectory).where(RideShardDirectory.RideID == ride_id))
    if entry is not None:
        return int(entry.ShardID)

    shard_id = shard_id_for_ride_id(ride_id)
    db.add(
        RideShardDirectory(
            RideID=ride_id,
            ShardID=shard_id,
            Strategy="ride_id_mod_3",
        )
    )
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
