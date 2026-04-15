from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.sharding import shard_id_for_ride_id
from models.shard_directory import RideShardDirectory


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
