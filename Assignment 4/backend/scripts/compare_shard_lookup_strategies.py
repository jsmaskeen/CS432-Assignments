from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from db.session import SessionLocal
from db.sharding import shard_id_for_ride_id
from models.shard_directory import RideShardDirectory, RideShardRangeDirectory


def _load_ride_ids(db) -> list[int]:
    ride_ids = [int(value) for value in db.scalars(select(RideShardDirectory.RideID)).all()]
    return sorted(ride_ids)


def _load_exact_directory(db) -> dict[int, int]:
    rows = db.execute(select(RideShardDirectory.RideID, RideShardDirectory.ShardID)).all()
    return {int(ride_id): int(shard_id) for ride_id, shard_id in rows}


def _load_range_directory(db) -> list[tuple[int, int | None, int]]:
    RideShardRangeDirectory.__table__.create(bind=db.get_bind(), checkfirst=True)
    db.commit()
    stmt = select(
        RideShardRangeDirectory.MinRideID,
        RideShardRangeDirectory.MaxRideID,
        RideShardRangeDirectory.ShardID,
    ).order_by(RideShardRangeDirectory.MinRideID.asc())
    try:
        rows = db.execute(stmt).all()
    except OperationalError:
        db.rollback()
        rows = db.execute(stmt).all()
    return [(int(start), int(end) if end is not None else None, int(shard_id)) for start, end, shard_id in rows]


def _lookup_range(ride_id: int, ranges: list[tuple[int, int | None, int]]) -> int | None:
    for start, end, shard_id in ranges:
        if ride_id < start:
            continue
        if end is None or ride_id <= end:
            return shard_id
    return None


def _resolve_range_or_modulo(ride_id: int, ranges: list[tuple[int, int | None, int]]) -> int:
    shard_id = _lookup_range(ride_id, ranges)
    if shard_id is None:
        return shard_id_for_ride_id(ride_id)
    return shard_id


def _distribution_entropy(distribution: dict[int, int], *, shard_count: int = 3) -> tuple[float, float, float]:
    total = sum(distribution.values())
    if total <= 0 or shard_count <= 1:
        return 0.0, 0.0, 0.0

    entropy_bits = 0.0
    for shard_id in range(shard_count):
        count = distribution.get(shard_id, 0)
        if count <= 0:
            continue
        probability = count / total
        entropy_bits -= probability * math.log2(probability)

    max_entropy_bits = math.log2(shard_count)
    normalized_entropy = entropy_bits / max_entropy_bits if max_entropy_bits > 0 else 0.0
    return entropy_bits, max_entropy_bits, normalized_entropy


def _benchmark(name: str, resolver, ride_ids: list[int], iterations: int) -> dict[str, object]:
    samples = [random.choice(ride_ids) for _ in range(iterations)]
    latencies_ms: list[float] = []
    distribution: dict[int, int] = {0: 0, 1: 0, 2: 0}

    start = time.perf_counter()
    for ride_id in samples:
        t0 = time.perf_counter()
        shard_id = int(resolver(ride_id))
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)
        distribution[shard_id] = distribution.get(shard_id, 0) + 1
    total_ms = (time.perf_counter() - start) * 1000.0

    latencies_ms.sort()
    p95_index = max(0, int(len(latencies_ms) * 0.95) - 1)
    p99_index = max(0, int(len(latencies_ms) * 0.99) - 1)
    entropy_bits, max_entropy_bits, normalized_entropy = _distribution_entropy(distribution)
    imbalance_spread = max(distribution.values()) - min(distribution.values())

    return {
        "strategy": name,
        "iterations": iterations,
        "avg_ms": sum(latencies_ms) / len(latencies_ms),
        "p95_ms": latencies_ms[p95_index],
        "p99_ms": latencies_ms[p99_index],
        "max_ms": max(latencies_ms),
        "total_ms": total_ms,
        "lookups_per_second": (iterations / (total_ms / 1000.0)) if total_ms > 0 else 0.0,
        "sampled_distribution": distribution,
        "entropy_bits": entropy_bits,
        "max_entropy_bits": max_entropy_bits,
        "normalized_entropy": normalized_entropy,
        "imbalance_spread": imbalance_spread,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare modulo and directory-based shard lookup strategies")
    parser.add_argument("--iterations", type=int, default=10000, help="Number of lookup samples")
    parser.add_argument(
        "--output",
        default="shard_lookup_comparison.json",
        help="Output JSON path relative to backend/scripts or absolute path",
    )
    args = parser.parse_args()

    random.seed(432)

    db = SessionLocal()
    try:
        ride_ids = _load_ride_ids(db)
        if not ride_ids:
            raise RuntimeError("Ride_Shard_Directory is empty. Run migration or create rides first.")

        exact_directory = _load_exact_directory(db)
        ranges = _load_range_directory(db)

        results: list[dict[str, object]] = []
        results.append(_benchmark("modulo", shard_id_for_ride_id, ride_ids, args.iterations))

        if exact_directory:
            results.append(
                _benchmark(
                    "directory_exact_cache",
                    lambda ride_id: exact_directory.get(ride_id, shard_id_for_ride_id(ride_id)),
                    ride_ids,
                    args.iterations,
                )
            )

        if ranges:
            results.append(
                _benchmark(
                    "directory_range_cache",
                    lambda ride_id: _resolve_range_or_modulo(ride_id, ranges),
                    ride_ids,
                    args.iterations,
                )
            )

        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = Path(__file__).resolve().with_name(args.output)

        payload = {
            "ride_count": len(ride_ids),
            "range_rule_count": len(ranges),
            "results": results,
        }
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        print(json.dumps(payload, indent=2))
        print(f"Saved comparison to: {output_path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
