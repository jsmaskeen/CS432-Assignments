from __future__ import annotations

import argparse

from sqlalchemy import delete, select

from core.sharding import upsert_ride_shard_range
from db.session import SessionLocal
from models.shard_directory import RideShardRangeDirectory


def _parse_rule(rule: str) -> tuple[int, int | None, int]:
    try:
        range_part, shard_part = rule.split(":", 1)
        start_part, end_part = range_part.split("-", 1)
        min_ride_id = int(start_part)
        max_ride_id = None if end_part.lower() in {"*", "max", "none"} else int(end_part)
        shard_id = int(shard_part)
    except ValueError as exc:
        raise ValueError(
            f"Invalid rule '{rule}'. Expected format start-end:shard, example 1-50000:0 or 50001-*:1"
        ) from exc

    return min_ride_id, max_ride_id, shard_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Configure key-range to shard mappings")
    parser.add_argument(
        "--rule",
        action="append",
        required=True,
        help="Range mapping rule. Example: 1-50000:0 or 50001-*:1",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete all existing range rules before applying new ones",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        RideShardRangeDirectory.__table__.create(bind=db.get_bind(), checkfirst=True)

        if args.replace:
            db.execute(delete(RideShardRangeDirectory))
            db.flush()

        for rule in args.rule:
            min_ride_id, max_ride_id, shard_id = _parse_rule(rule)
            upsert_ride_shard_range(min_ride_id, max_ride_id, shard_id, db)

        db.commit()

        rows = db.execute(
            select(
                RideShardRangeDirectory.RangeID,
                RideShardRangeDirectory.MinRideID,
                RideShardRangeDirectory.MaxRideID,
                RideShardRangeDirectory.ShardID,
            ).order_by(RideShardRangeDirectory.MinRideID.asc())
        ).all()

        print("Configured ride shard ranges:")
        for row in rows:
            max_label = "*" if row.MaxRideID is None else str(int(row.MaxRideID))
            print(f"  id={int(row.RangeID)} range={int(row.MinRideID)}-{max_label} shard={int(row.ShardID)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
