from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text

QUERIES = {
    "duplicate_bookings": """
        SELECT RideID, Passenger_MemberID, COUNT(*) AS cnt
        FROM Bookings
        GROUP BY RideID, Passenger_MemberID
        HAVING COUNT(*) > 1
    """,
    "duplicate_participants": """
        SELECT RideID, MemberID, COUNT(*) AS cnt
        FROM Ride_Participants
        GROUP BY RideID, MemberID
        HAVING COUNT(*) > 1
    """,
    "duplicate_settlements": """
        SELECT BookingID, COUNT(*) AS cnt
        FROM Cost_Settlements
        GROUP BY BookingID
        HAVING COUNT(*) > 1
    """,
    "seat_mismatch": """
        SELECT
            r.RideID,
            r.Max_Capacity,
            r.Available_Seats,
            COALESCE(c.confirmed_non_host_count, 0) AS confirmed_non_host_count,
            (r.Max_Capacity - 1 - COALESCE(c.confirmed_non_host_count, 0)) AS expected_available
        FROM Rides r
        LEFT JOIN (
            SELECT b.RideID, COUNT(*) AS confirmed_non_host_count
            FROM Bookings b
            JOIN Rides rr ON rr.RideID = b.RideID
            WHERE b.Booking_Status = 'Confirmed'
              AND b.Passenger_MemberID <> rr.Host_MemberID
            GROUP BY b.RideID
        ) c ON c.RideID = r.RideID
        WHERE r.Available_Seats <> (r.Max_Capacity - 1 - COALESCE(c.confirmed_non_host_count, 0))
    """,
    "invalid_seat_bounds": """
        SELECT RideID, Max_Capacity, Available_Seats
        FROM Rides
        WHERE Available_Seats < 0 OR Available_Seats > Max_Capacity
    """,
    "invalid_status_vs_seats": """
        SELECT RideID, Ride_Status, Available_Seats
        FROM Rides
        WHERE (Ride_Status = 'Full' AND Available_Seats <> 0)
           OR (Ride_Status = 'Open' AND Available_Seats = 0)
    """,
    "missing_host_booking": """
        SELECT r.RideID, r.Host_MemberID, COUNT(b.BookingID) AS host_confirmed_rows
        FROM Rides r
        LEFT JOIN Bookings b
          ON b.RideID = r.RideID
         AND b.Passenger_MemberID = r.Host_MemberID
         AND b.Booking_Status = 'Confirmed'
        GROUP BY r.RideID, r.Host_MemberID
        HAVING host_confirmed_rows <> 1
    """,
    "missing_host_participant": """
        SELECT r.RideID, r.Host_MemberID
        FROM Rides r
        LEFT JOIN Ride_Participants rp
          ON rp.RideID = r.RideID
         AND rp.MemberID = r.Host_MemberID
         AND rp.Role = 'Host'
        WHERE rp.ParticipantID IS NULL
    """,
    "missing_confirmed_participant": """
        SELECT b.BookingID, b.RideID, b.Passenger_MemberID
        FROM Bookings b
        LEFT JOIN Ride_Participants rp
          ON rp.RideID = b.RideID
         AND rp.MemberID = b.Passenger_MemberID
         AND rp.Role IN ('Passenger', 'Host')
        WHERE b.Booking_Status = 'Confirmed'
          AND rp.ParticipantID IS NULL
    """,
    "participant_without_confirmed_booking": """
        SELECT rp.ParticipantID, rp.RideID, rp.MemberID
        FROM Ride_Participants rp
        LEFT JOIN Bookings b
          ON b.RideID = rp.RideID
         AND b.Passenger_MemberID = rp.MemberID
         AND b.Booking_Status = 'Confirmed'
        WHERE rp.Role = 'Passenger'
          AND b.BookingID IS NULL
    """,
    "non_confirmed_booking_with_participant": """
        SELECT b.BookingID, b.RideID, b.Passenger_MemberID, b.Booking_Status, rp.ParticipantID
        FROM Bookings b
        JOIN Ride_Participants rp
          ON rp.RideID = b.RideID
         AND rp.MemberID = b.Passenger_MemberID
         AND rp.Role = 'Passenger'
        WHERE b.Booking_Status IN ('Pending', 'Rejected', 'Cancelled')
    """,
    "missing_settlement_for_completed": """
        SELECT b.BookingID, b.RideID
        FROM Bookings b
        JOIN Rides r ON r.RideID = b.RideID
        LEFT JOIN Cost_Settlements s ON s.BookingID = b.BookingID
        WHERE r.Ride_Status = 'Completed'
          AND b.Booking_Status = 'Confirmed'
          AND b.Passenger_MemberID <> r.Host_MemberID
          AND s.SettlementID IS NULL
    """,
    "orphan_or_invalid_settlement": """
        SELECT s.SettlementID, s.BookingID
        FROM Cost_Settlements s
        LEFT JOIN Bookings b ON b.BookingID = s.BookingID
        WHERE b.BookingID IS NULL
           OR b.Booking_Status <> 'Confirmed'
    """,
}


def load_env_file(path: str) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def build_db_url(args: argparse.Namespace) -> str:
    user = args.user or os.getenv("MYSQL_USER")
    password = args.password or os.getenv("MYSQL_PASSWORD")
    host = args.host or os.getenv("MYSQL_HOST", "localhost")
    port = args.port or int(os.getenv("MYSQL_PORT", "3306"))
    database = args.database or os.getenv("MYSQL_DB", "cabSharing")

    if not user or not password:
        raise ValueError("MYSQL_USER and MYSQL_PASSWORD are required via args or environment")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="unspecified")
    parser.add_argument(
        "--env-file",
        default=str((Path(__file__).resolve().parents[2] / "Assignment-2/Module_B/backend/.env")),
    )
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--user")
    parser.add_argument("--password")
    parser.add_argument("--database")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    load_env_file(args.env_file)

    try:
        url = build_db_url(args)
    except ValueError as exc:
        print(f"CONFIG_ERROR: {exc}")
        return 2

    engine = create_engine(url, pool_pre_ping=True)
    result = {
        "stage": args.stage,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "checks": {},
        "has_violations": False,
    }

    with engine.connect() as conn:
        for name, query in QUERIES.items():
            rows = conn.execute(text(query)).mappings().all()
            result["checks"][name] = {
                "violations": len(rows),
                "rows": [dict(row) for row in rows[:50]],
                "truncated": len(rows) > 50,
            }
            if rows:
                result["has_violations"] = True

    output_text = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(output_text)
    else:
        print(output_text)

    return 1 if result["has_violations"] else 0


if __name__ == "__main__":
    sys.exit(main())
