from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Callable

from sqlalchemy import select

from core.config import settings
from db.sharding import SHARD_SESSION_MAKERS, VALID_SHARD_IDS
from db.session import SessionLocal
from models.booking import Booking
from models.ride import Ride

SHARD_COUNT = 3


def _extract_insert_rows(sql_text: str, table_name: str) -> list[str]:
    pattern = rf"INSERT INTO `{table_name}` VALUES (.*?);"
    match = re.search(pattern, sql_text, re.S)
    if not match:
        return []

    raw = match.group(1)
    rows: list[str] = []
    current = ""
    depth = 0
    for ch in raw:
        if ch == "(":
            depth += 1
        if depth > 0:
            current += ch
        if ch == ")":
            depth -= 1
            if depth == 0:
                rows.append(current)
                current = ""
    return rows


def _split_sql_tuple(row: str) -> list[str]:
    values: list[str] = []
    token = ""
    in_quote = False
    escaped = False

    for ch in row[1:-1]:
        if ch == "'" and not escaped:
            in_quote = not in_quote
            token += ch
            continue
        if ch == "," and not in_quote:
            values.append(token.strip())
            token = ""
            continue

        escaped = ch == "\\" and not escaped
        token += ch

    values.append(token.strip())
    return values


def _strip_sql_literal(value: str) -> str:
    token = value.strip()
    if token.upper() == "NULL":
        return ""

    if len(token) >= 2 and token[0] == "'" and token[-1] == "'":
        token = token[1:-1]

    return token.replace("\\'", "'")


def _id_modulo_shard(identifier: int) -> int:
    return (identifier - 1) % SHARD_COUNT


def _stable_hash_shard(raw_value: str) -> int:
    digest = hashlib.md5(raw_value.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % SHARD_COUNT


def _normalize_shard_counts(counts: Counter[int]) -> dict[int, int]:
    return {shard_id: int(counts.get(shard_id, 0)) for shard_id in range(SHARD_COUNT)}


def _entropy_metrics(shard_counts: dict[int, int]) -> tuple[float, float, float]:
    total = sum(shard_counts.values())
    if total <= 0 or SHARD_COUNT <= 1:
        return 0.0, 0.0, 0.0

    entropy_bits = 0.0
    for shard_id in range(SHARD_COUNT):
        count = shard_counts.get(shard_id, 0)
        if count <= 0:
            continue
        probability = count / total
        entropy_bits -= probability * math.log2(probability)

    max_entropy_bits = math.log2(SHARD_COUNT)
    normalized_entropy = entropy_bits / max_entropy_bits if max_entropy_bits > 0 else 0.0
    return entropy_bits, max_entropy_bits, normalized_entropy


def _evaluate_shard_key_candidates(rides: list[dict[str, object]]) -> list[dict[str, object]]:
    candidates: list[tuple[str, str, Callable[[dict[str, object]], int]]] = [
        ("ride_id_mod3", "(RideID - 1) % 3", lambda ride: _id_modulo_shard(int(ride["ride_id"]))),
        (
            "host_member_id_mod3",
            "(Host_MemberID - 1) % 3",
            lambda ride: _id_modulo_shard(int(ride["host_member_id"])),
        ),
        (
            "start_geohash_hash",
            "md5(Start_GeoHash) % 3",
            lambda ride: _stable_hash_shard(str(ride["start_geohash"])),
        ),
        (
            "end_geohash_hash",
            "md5(End_GeoHash) % 3",
            lambda ride: _stable_hash_shard(str(ride["end_geohash"])),
        ),
        (
            "vehicle_type_hash",
            "md5(Vehicle_Type) % 3",
            lambda ride: _stable_hash_shard(str(ride["vehicle_type"])),
        ),
        (
            "ride_status_hash",
            "md5(Ride_Status) % 3",
            lambda ride: _stable_hash_shard(str(ride["ride_status"])),
        ),
        (
            "host_plus_start_hash",
            "md5(Host_MemberID|Start_GeoHash) % 3",
            lambda ride: _stable_hash_shard(f"{ride['host_member_id']}|{ride['start_geohash']}"),
        ),
        (
            "route_pair_hash",
            "md5(Start_GeoHash|End_GeoHash) % 3",
            lambda ride: _stable_hash_shard(f"{ride['start_geohash']}|{ride['end_geohash']}"),
        ),
    ]
    candidate_priority = {name: idx for idx, (name, _, _) in enumerate(candidates)}

    results: list[dict[str, object]] = []
    for name, method, resolver in candidates:
        counts: Counter[int] = Counter()
        for ride in rides:
            shard_id = int(resolver(ride))
            counts[shard_id] += 1

        shard_counts = _normalize_shard_counts(counts)
        entropy_bits, max_entropy_bits, normalized_entropy = _entropy_metrics(shard_counts)
        max_load = max(shard_counts.values()) if shard_counts else 0
        min_load = min(shard_counts.values()) if shard_counts else 0

        results.append(
            {
                "candidate": name,
                "method": method,
                "counts_by_shard": shard_counts,
                "entropy_bits": entropy_bits,
                "max_entropy_bits": max_entropy_bits,
                "normalized_entropy": normalized_entropy,
                "imbalance_spread": max_load - min_load,
            }
        )

    results.sort(
        key=lambda result: (
            -float(result["normalized_entropy"]),
            int(result["imbalance_spread"]),
            candidate_priority.get(str(result["candidate"]), 10_000),
            result["candidate"],
        )
    )
    return results


def _collect_api_routing_metrics(route_dir: Path) -> tuple[int, int]:
    ride_path_hits = 0
    rideid_predicate_hits = 0

    for py in route_dir.rglob("*.py"):
        text = py.read_text(encoding="utf-8", errors="ignore")
        ride_path_hits += len(re.findall(r"/\{ride_id\}|/ride/\{ride_id\}", text))
        rideid_predicate_hits += len(re.findall(r"RideID|ride_id", text))

    return ride_path_hits, rideid_predicate_hits


def _load_data_from_session_factory(session_factory) -> tuple[list[dict[str, object]], list[tuple[int, int]]]:
    rides: list[dict[str, object]] = []
    bookings: list[tuple[int, int]] = []

    db = session_factory()
    try:
        ride_rows = db.execute(
            select(
                Ride.RideID,
                Ride.Host_MemberID,
                Ride.Start_GeoHash,
                Ride.End_GeoHash,
                Ride.Vehicle_Type,
                Ride.Ride_Status,
            )
        ).all()

        for row in ride_rows:
            rides.append(
                {
                    "ride_id": int(row[0]),
                    "host_member_id": int(row[1]),
                    "start_geohash": str(row[2]),
                    "end_geohash": str(row[3]),
                    "vehicle_type": str(row[4]),
                    "ride_status": str(row[5]),
                }
            )

        booking_rows = db.execute(select(Booking.BookingID, Booking.RideID)).all()
        bookings = [(int(booking_id), int(ride_id)) for booking_id, ride_id in booking_rows]
    finally:
        db.close()

    return rides, bookings


def _load_data_from_db_primary() -> tuple[list[dict[str, object]], list[tuple[int, int]]]:
    return _load_data_from_session_factory(SessionLocal)


def _load_data_from_db_shards() -> tuple[list[dict[str, object]], list[tuple[int, int]], dict[str, int]]:
    rides_by_id: dict[int, dict[str, object]] = {}
    bookings_by_id: dict[int, tuple[int, int]] = {}
    duplicate_rides = 0
    duplicate_bookings = 0

    for shard_id in VALID_SHARD_IDS:
        shard_rides, shard_bookings = _load_data_from_session_factory(SHARD_SESSION_MAKERS[shard_id])

        for ride in shard_rides:
            ride_id = int(ride["ride_id"])
            if ride_id in rides_by_id:
                duplicate_rides += 1
                continue
            rides_by_id[ride_id] = ride

        for booking_id, ride_id in shard_bookings:
            if booking_id in bookings_by_id:
                duplicate_bookings += 1
                continue
            bookings_by_id[booking_id] = (booking_id, ride_id)

    rides = list(sorted(rides_by_id.values(), key=lambda row: int(row["ride_id"])))
    bookings = list(sorted(bookings_by_id.values(), key=lambda row: int(row[0])))
    diagnostics = {
        "duplicate_rides_removed": duplicate_rides,
        "duplicate_bookings_removed": duplicate_bookings,
    }
    return rides, bookings, diagnostics


def _resolve_db_scope(requested_scope: str) -> str:
    if requested_scope in {"primary", "shards"}:
        return requested_scope

    shard_ports = {settings.shard_port(shard_id) for shard_id in VALID_SHARD_IDS}
    if int(settings.MYSQL_PORT) in shard_ports:
        return "shards"
    return "primary"


def _load_data_from_dump(dump_path: Path) -> tuple[list[dict[str, object]], list[tuple[int, int]]]:
    sql_text = dump_path.read_text(encoding="utf-8", errors="ignore")

    ride_rows = _extract_insert_rows(sql_text, "Rides")
    booking_rows = _extract_insert_rows(sql_text, "Bookings")

    rides: list[dict[str, object]] = []
    for row in ride_rows:
        vals = _split_sql_tuple(row)
        if len(vals) < 10:
            continue

        rides.append(
            {
                "ride_id": int(vals[0]),
                "host_member_id": int(vals[1]),
                "start_geohash": _strip_sql_literal(vals[2]),
                "end_geohash": _strip_sql_literal(vals[3]),
                "vehicle_type": _strip_sql_literal(vals[5]),
                "ride_status": _strip_sql_literal(vals[9]),
            }
        )

    bookings: list[tuple[int, int]] = []
    for row in booking_rows:
        vals = _split_sql_tuple(row)
        booking_id = int(vals[0])
        ride_id = int(vals[1])
        bookings.append((booking_id, ride_id))

    return rides, bookings


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute evidence metrics for shard key selection")
    parser.add_argument(
        "--source",
        choices=("db", "dump"),
        default="db",
        help="Input source for rides/bookings. Use 'db' for live generated/migrated data, 'dump' for SQL dump parsing.",
    )
    parser.add_argument(
        "--db-scope",
        choices=("auto", "primary", "shards"),
        default="auto",
        help="When --source db: read from primary DB, all shards, or auto-detect based on MYSQL_PORT.",
    )
    parser.add_argument(
        "--dump",
        default="../../SQL-Dump/dump.sql",
        help="Path to SQL dump file relative to backend/scripts (used only when --source dump)",
    )
    parser.add_argument(
        "--routes",
        default="../api/routes",
        help="Path to FastAPI route directory relative to backend/scripts",
    )
    parser.add_argument(
        "--entropy-output",
        default=None,
        help="Optional JSON output path for shard-key entropy comparison (relative to backend/scripts)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    routes_path = (script_dir / args.routes).resolve()
    db_scope_used = "n/a"
    diagnostics: dict[str, int] = {}

    if args.source == "db":
        db_scope_used = _resolve_db_scope(args.db_scope)
        if db_scope_used == "primary":
            rides, bookings = _load_data_from_db_primary()
        else:
            rides, bookings, diagnostics = _load_data_from_db_shards()
    else:
        dump_path = (script_dir / args.dump).resolve()
        rides, bookings = _load_data_from_dump(dump_path)

    ride_mod3 = Counter(_id_modulo_shard(int(ride["ride_id"])) for ride in rides)
    host_mod3 = Counter(_id_modulo_shard(int(ride["host_member_id"])) for ride in rides)
    start_geohash_counts = Counter(str(ride["start_geohash"]) for ride in rides)
    booking_mod3 = Counter(_id_modulo_shard(ride_id) for _, ride_id in bookings)

    entropy_results = _evaluate_shard_key_candidates(rides)
    best_candidate = entropy_results[0] if entropy_results else None

    ride_path_hits, rideid_predicate_hits = _collect_api_routing_metrics(routes_path)

    print(f"data_source={args.source}")
    if args.source == "db":
        print(f"db_scope={db_scope_used}")
        if diagnostics:
            print(f"db_scope_diagnostics={diagnostics}")
    print(f"routes_with_ride_path_parameters={ride_path_hits}")
    print(f"ride_id_or_RideID_occurrences_in_routes={rideid_predicate_hits}")
    print(f"rides_total={len(rides)}")
    print(f"bookings_total={len(bookings)}")
    print(f"rides_distribution_rideid_mod3={_normalize_shard_counts(ride_mod3)}")
    print(f"bookings_distribution_by_ride_shard={_normalize_shard_counts(booking_mod3)}")
    print(f"rides_distribution_hostid_mod3={_normalize_shard_counts(host_mod3)}")
    print(f"top_start_geohash_counts={start_geohash_counts.most_common(5)}")

    print("candidate_shard_key_entropy_ranking=")
    for result in entropy_results:
        print(
            "  "
            + f"{result['candidate']}: counts={result['counts_by_shard']} "
            + f"entropy_bits={float(result['entropy_bits']):.6f} "
            + f"normalized_entropy={float(result['normalized_entropy']):.6f} "
            + f"imbalance_spread={int(result['imbalance_spread'])}"
        )

    if best_candidate is not None:
        print(f"recommended_shard_key={best_candidate['candidate']}")
        print(f"recommended_shard_key_method={best_candidate['method']}")
        print(f"recommended_shard_key_normalized_entropy={float(best_candidate['normalized_entropy']):.6f}")

    if args.entropy_output:
        entropy_output_path = Path(args.entropy_output)
        if not entropy_output_path.is_absolute():
            entropy_output_path = (script_dir / entropy_output_path).resolve()

        payload = {
            "rides_total": len(rides),
            "bookings_total": len(bookings),
            "shard_count": SHARD_COUNT,
            "data_source": args.source,
            "db_scope": db_scope_used,
            "db_scope_diagnostics": diagnostics,
            "max_entropy_bits": math.log2(SHARD_COUNT),
            "recommended_shard_key": best_candidate,
            "ranked_candidates": entropy_results,
        }
        entropy_output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"entropy_report_saved_to={entropy_output_path}")


if __name__ == "__main__":
    main()
