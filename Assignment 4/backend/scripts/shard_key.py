from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


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


def _collect_api_routing_metrics(route_dir: Path) -> tuple[int, int]:
    ride_path_hits = 0
    rideid_predicate_hits = 0

    for py in route_dir.rglob("*.py"):
        text = py.read_text(encoding="utf-8", errors="ignore")
        ride_path_hits += len(re.findall(r"/\{ride_id\}|/ride/\{ride_id\}", text))
        rideid_predicate_hits += len(re.findall(r"RideID|ride_id", text))

    return ride_path_hits, rideid_predicate_hits


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute evidence metrics for shard key selection")
    parser.add_argument(
        "--dump",
        default="../../SQL-Dump/dump.sql",
        help="Path to SQL dump file relative to backend/scripts",
    )
    parser.add_argument(
        "--routes",
        default="../api/routes",
        help="Path to FastAPI route directory relative to backend/scripts",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    dump_path = (script_dir / args.dump).resolve()
    routes_path = (script_dir / args.routes).resolve()

    sql_text = dump_path.read_text(encoding="utf-8", errors="ignore")

    ride_rows = _extract_insert_rows(sql_text, "Rides")
    booking_rows = _extract_insert_rows(sql_text, "Bookings")

    rides = []
    for row in ride_rows:
        vals = _split_sql_tuple(row)
        ride_id = int(vals[0])
        host_id = int(vals[1])
        start_gh = vals[2].strip("'")
        rides.append((ride_id, host_id, start_gh))

    bookings = []
    for row in booking_rows:
        vals = _split_sql_tuple(row)
        booking_id = int(vals[0])
        ride_id = int(vals[1])
        bookings.append((booking_id, ride_id))

    ride_mod3 = Counter(((ride_id - 1) % 3) + 1 for ride_id, _, _ in rides)
    host_mod3 = Counter(((host_id - 1) % 3) + 1 for _, host_id, _ in rides)
    start_geohash_counts = Counter(start_gh for _, _, start_gh in rides)
    booking_mod3 = Counter(((ride_id - 1) % 3) + 1 for _, ride_id in bookings)

    ride_path_hits, rideid_predicate_hits = _collect_api_routing_metrics(routes_path)

    print(f"routes_with_ride_path_parameters={ride_path_hits}")
    print(f"ride_id_or_RideID_occurrences_in_routes={rideid_predicate_hits}")
    print(f"rides_total={len(rides)}")
    print(f"bookings_total={len(bookings)}")
    print(f"rides_distribution_rideid_mod3={dict(sorted(ride_mod3.items()))}")
    print(f"bookings_distribution_by_ride_shard={dict(sorted(booking_mod3.items()))}")
    print(f"rides_distribution_hostid_mod3={dict(sorted(host_mod3.items()))}")
    print(f"top_start_geohash_counts={start_geohash_counts.most_common(5)}")


if __name__ == "__main__":
    main()
