from __future__ import annotations

from sqlalchemy import text

from db.session import SessionLocal
from db.sharding import SHARD_SESSION_MAKERS, shard_id_for_ride_id

RIDE_CENTRIC_TABLES = [
    "Rides",
    "Bookings",
    "Ride_Chat",
    "Ride_Participants",
    "Reputation_Reviews",
    "Cost_Settlements",
]


def _count(db, table_name: str) -> int:
    return int(db.scalar(text(f"SELECT COUNT(*) FROM `{table_name}`")) or 0)


def main() -> None:
    source = SessionLocal()
    shard_sessions = {shard_id: SHARD_SESSION_MAKERS[shard_id]() for shard_id in (0, 1, 2)}

    try:
        print("Count Validation")
        for table in RIDE_CENTRIC_TABLES:
            source_count = _count(source, table)
            shard_counts = {sid: _count(db, table) for sid, db in shard_sessions.items()}
            shard_total = sum(shard_counts.values())
            status = "OK" if source_count == shard_total else "MISMATCH"
            print(
                f"{table}: source={source_count}, shards={shard_counts}, total={shard_total}, status={status}"
            )

        print("\nRide Placement Validation")
        misplaced = 0
        duplicate = 0

        seen_rides: set[int] = set()
        for shard_id, db in shard_sessions.items():
            ride_ids = [int(row[0]) for row in db.execute(text("SELECT RideID FROM Rides")).all()]
            for ride_id in ride_ids:
                expected = shard_id_for_ride_id(ride_id)
                if expected != shard_id:
                    misplaced += 1
                    print(f"MISPLACED: RideID={ride_id}, actual_shard={shard_id}, expected_shard={expected}")
                if ride_id in seen_rides:
                    duplicate += 1
                    print(f"DUPLICATE: RideID={ride_id} found in multiple shards")
                seen_rides.add(ride_id)

        print(
            f"ride_placement_summary: misplaced={misplaced}, duplicate={duplicate}, unique_rides={len(seen_rides)}"
        )

        print("\nDirectory Validation")
        directory_rows = source.execute(
            text("SELECT RideID, ShardID FROM Ride_Shard_Directory ORDER BY RideID")
        ).all()
        bad_directory = 0
        for ride_id, shard_id in directory_rows:
            expected = shard_id_for_ride_id(int(ride_id))
            if int(shard_id) != expected:
                bad_directory += 1
                print(
                    f"DIRECTORY_MISMATCH: RideID={ride_id}, directory_shard={shard_id}, expected_shard={expected}"
                )

        print(f"directory_summary: entries={len(directory_rows)}, mismatches={bad_directory}")
    finally:
        source.close()
        for db in shard_sessions.values():
            db.close()


if __name__ == "__main__":
    main()
