from __future__ import annotations

import argparse
from collections import defaultdict

from sqlalchemy import text

# for SQLAlchemy metadata to includes all tables.
import models.auth_credential 
import models.booking  
import models.chat_message   
import models.location 
import models.member   
import models.preference
import models.review 
import models.ride 
import models.ride_participant  
import models.saved_address  
import models.settlement
import models.shard_directory  
from db.session import Base, SessionLocal
from db.sharding import SHARD_ENGINES, SHARD_SESSION_MAKERS, shard_id_for_ride_id

RIDE_CENTRIC_TABLES_CLEAR_ORDER = [
    "Cost_Settlements",
    "Reputation_Reviews",
    "Ride_Participants",
    "Ride_Chat",
    "Bookings",
    "Rides",
]

PARENT_TABLES_CLEAR_ORDER = [
    "Auth_Credentials",
    "Saved_Addresses",
    "User_Preferences",
    "Members",
]


def _fetch_rows(source_db, sql: str) -> list[dict[str, object]]:
    return [dict(row) for row in source_db.execute(text(sql)).mappings()]


def _bulk_insert(target_db, table_name: str, rows: list[dict[str, object]]) -> None:
    if not rows:
        return

    columns = list(rows[0].keys())
    columns_csv = ", ".join(f"`{col}`" for col in columns)
    params_csv = ", ".join(f":{col}" for col in columns)
    sql = text(f"INSERT INTO `{table_name}` ({columns_csv}) VALUES ({params_csv})")
    target_db.execute(sql, rows)


def _prepare_shard_engines() -> None:
    for engine in SHARD_ENGINES.values():
        Base.metadata.create_all(bind=engine)


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate ride-centric data to 3 shards")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute shard buckets and print counts without writing to shard databases",
    )
    args = parser.parse_args()

    _prepare_shard_engines()

    source = SessionLocal()
    try:
        rides = _fetch_rows(source, "SELECT * FROM Rides ORDER BY RideID")
        bookings = _fetch_rows(source, "SELECT * FROM Bookings ORDER BY BookingID")
        chats = _fetch_rows(source, "SELECT * FROM Ride_Chat ORDER BY MessageID")
        participants = _fetch_rows(source, "SELECT * FROM Ride_Participants ORDER BY ParticipantID")
        reviews = _fetch_rows(source, "SELECT * FROM Reputation_Reviews ORDER BY ReviewID")
        settlements = _fetch_rows(
            source,
            """
            SELECT cs.*, b.RideID AS __RideID
            FROM Cost_Settlements cs
            JOIN Bookings b ON b.BookingID = cs.BookingID
            ORDER BY cs.SettlementID
            """,
        )
        members = _fetch_rows(source, "SELECT * FROM Members ORDER BY MemberID")

        shard_rows: dict[int, dict[str, list[dict[str, object]]]] = {
            0: defaultdict(list),
            1: defaultdict(list),
            2: defaultdict(list),
        }

        directory_rows: list[dict[str, object]] = []
        for ride in rides:
            shard_id = shard_id_for_ride_id(int(ride["RideID"]))
            shard_rows[shard_id]["Rides"].append(ride)
            directory_rows.append(
                {
                    "RideID": int(ride["RideID"]),
                    "ShardID": shard_id,
                    "Strategy": "ride_id_mod_3",
                }
            )

        for booking in bookings:
            shard_id = shard_id_for_ride_id(int(booking["RideID"]))
            shard_rows[shard_id]["Bookings"].append(booking)

        for chat in chats:
            shard_id = shard_id_for_ride_id(int(chat["RideID"]))
            shard_rows[shard_id]["Ride_Chat"].append(chat)

        for participant in participants:
            shard_id = shard_id_for_ride_id(int(participant["RideID"]))
            shard_rows[shard_id]["Ride_Participants"].append(participant)

        for review in reviews:
            shard_id = shard_id_for_ride_id(int(review["RideID"]))
            shard_rows[shard_id]["Reputation_Reviews"].append(review)

        for settlement in settlements:
            shard_id = shard_id_for_ride_id(int(settlement["__RideID"]))
            row = dict(settlement)
            row.pop("__RideID", None)
            shard_rows[shard_id]["Cost_Settlements"].append(row)

        used_member_ids: dict[int, set[int]] = {0: set(), 1: set(), 2: set()}
        for shard_id in (0, 1, 2):
            for ride in shard_rows[shard_id]["Rides"]:
                used_member_ids[shard_id].add(int(ride["Host_MemberID"]))
            for booking in shard_rows[shard_id]["Bookings"]:
                used_member_ids[shard_id].add(int(booking["Passenger_MemberID"]))
            for chat in shard_rows[shard_id]["Ride_Chat"]:
                used_member_ids[shard_id].add(int(chat["Sender_MemberID"]))
            for participant in shard_rows[shard_id]["Ride_Participants"]:
                used_member_ids[shard_id].add(int(participant["MemberID"]))
            for review in shard_rows[shard_id]["Reputation_Reviews"]:
                used_member_ids[shard_id].add(int(review["Reviewer_MemberID"]))
                used_member_ids[shard_id].add(int(review["Reviewee_MemberID"]))

        member_by_id = {int(member["MemberID"]): member for member in members}
        shard_member_rows: dict[int, list[dict[str, object]]] = {0: [], 1: [], 2: []}
        for shard_id in (0, 1, 2):
            shard_member_rows[shard_id] = [
                member_by_id[member_id]
                for member_id in sorted(used_member_ids[shard_id])
                if member_id in member_by_id
            ]

        print("Proposed shard distribution")
        for shard_id in (0, 1, 2):
            counts = {table: len(rows) for table, rows in shard_rows[shard_id].items()}
            counts["Members"] = len(shard_member_rows[shard_id])
            print(f"shard_{shard_id}: {counts}")

        if args.dry_run:
            print("Dry run complete. No writes were executed.")
            return

        source.execute(
            text(
                """
                INSERT INTO Ride_Shard_Directory (RideID, ShardID, Strategy)
                VALUES (:RideID, :ShardID, :Strategy)
                ON DUPLICATE KEY UPDATE
                    ShardID = VALUES(ShardID),
                    Strategy = VALUES(Strategy)
                """
            ),
            directory_rows,
        )
        source.commit()

        for shard_id in (0, 1, 2):
            target = SHARD_SESSION_MAKERS[shard_id]()
            try:
                for table in RIDE_CENTRIC_TABLES_CLEAR_ORDER:
                    target.execute(text(f"DELETE FROM `{table}`"))
                for table in PARENT_TABLES_CLEAR_ORDER:
                    target.execute(text(f"DELETE FROM `{table}`"))

                _bulk_insert(target, "Members", shard_member_rows[shard_id])

                _bulk_insert(target, "Rides", shard_rows[shard_id]["Rides"])
                _bulk_insert(target, "Bookings", shard_rows[shard_id]["Bookings"])
                _bulk_insert(target, "Ride_Chat", shard_rows[shard_id]["Ride_Chat"])
                _bulk_insert(target, "Ride_Participants", shard_rows[shard_id]["Ride_Participants"])
                _bulk_insert(target, "Reputation_Reviews", shard_rows[shard_id]["Reputation_Reviews"])
                _bulk_insert(target, "Cost_Settlements", shard_rows[shard_id]["Cost_Settlements"])

                target.commit()
            except Exception:
                target.rollback()
                raise
            finally:
                target.close()

        print("Migration complete. Ride-centric data written to all 3 shards.")
    finally:
        source.close()


if __name__ == "__main__":
    main()
