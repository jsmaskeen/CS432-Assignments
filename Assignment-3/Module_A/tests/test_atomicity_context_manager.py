import os
import signal
import subprocess
import sys
import tempfile
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager
from database.transaction import Transaction


class TestAtomicityWithContextManager(unittest.TestCase):
    def setUp(self):
        self.db_manager = DatabaseManager()
        self.db = self.db_manager.create_database("test_integrity_db")

        self.db.create_table(
            name="Members",
            columns=[
                "MemberID",
                "OAUTH_TOKEN",
                "Email",
                "Full_Name",
                "Reputation_Score",
                "Phone_Number",
                "Created_At",
                "Gender",
            ],
            primary_key="MemberID",
            integrity_checks=[
                {"column": "OAUTH_TOKEN", "not_null": True},
                {"column": "Email", "not_null": True, "check": lambda value: value.endswith("@iitgn.ac.in")},
                {"column": "Full_Name", "not_null": True},
                {"column": "Reputation_Score", "not_null": True, "check": lambda value: 0.0 <= value <= 5.0},
                {"column": "Gender", "not_null": True, "check": lambda value: value in {"Male", "Female", "Other"}},
            ],
        )

        self.db.create_table(
            name="Rides",
            columns=[
                "RideID",
                "Host_MemberID",
                "Start_GeoHash",
                "End_GeoHash",
                "Departure_Time",
                "Vehicle_Type",
                "Max_Capacity",
                "Available_Seats",
                "Base_Fare_Per_KM",
                "Ride_Status",
                "Created_At",
            ],
            primary_key="RideID",
            foreign_keys=[
                {
                    "column": "Host_MemberID",
                    "references_table": "Members",
                    "references_column": "MemberID",
                }
            ],
        )

        self.db.create_table(
            name="Bookings",
            columns=[
                "BookingID",
                "RideID",
                "Passenger_MemberID",
                "Booking_Status",
                "Pickup_GeoHash",
                "Drop_GeoHash",
                "Distance_Travelled_KM",
                "Booked_At",
            ],
            primary_key="BookingID",
            foreign_keys=[
                {
                    "column": "RideID",
                    "references_table": "Rides",
                    "references_column": "RideID",
                    "on_delete": "CASCADE",
                },
                {
                    "column": "Passenger_MemberID",
                    "references_table": "Members",
                    "references_column": "MemberID",
                    "on_delete": "CASCADE",
                },
            ],
        )

        members = self.db.get_table("Members")
        members.insert_row(
            {
                "MemberID": 1,
                "OAUTH_TOKEN": "tok_alice",
                "Email": "alice@iitgn.ac.in",
                "Full_Name": "Alice",
                "Reputation_Score": 4.7,
                "Phone_Number": "9999999999",
                "Created_At": "2026-01-01 10:00:00",
                "Gender": "Female",
            }
        )

    # Verifies atomic success: all valid statements inside the context manager are committed together.
    def test_context_manager_commits_all_when_no_error(self):
        members = self.db.get_table("Members")
        rides = self.db.get_table("Rides")
        bookings = self.db.get_table("Bookings")

        with self.db.begin_transaction() as tx:
            members.insert_row(
                {
                    "MemberID": 2,
                    "OAUTH_TOKEN": "tok_bob",
                    "Email": "bob@iitgn.ac.in",
                    "Full_Name": "Bob",
                    "Reputation_Score": 3.8,
                    "Phone_Number": "8888888888",
                    "Created_At": "2026-01-02 11:00:00",
                    "Gender": "Male",
                },
                tx=tx,
            )
            rides.insert_row(
                {
                    "RideID": 1,
                    "Host_MemberID": 1,
                    "Start_GeoHash": "dr5ru",
                    "End_GeoHash": "dr5rv",
                    "Departure_Time": "2026-01-02 11:30:00",
                    "Vehicle_Type": "Sedan",
                    "Max_Capacity": 4,
                    "Available_Seats": 3,
                    "Base_Fare_Per_KM": 12.0,
                    "Ride_Status": "Open",
                    "Created_At": "2026-01-02 11:00:00",
                },
                tx=tx,
            )
            bookings.insert_row(
                {
                    "BookingID": 1,
                    "RideID": 1,
                    "Passenger_MemberID": 2,
                    "Booking_Status": "Confirmed",
                    "Pickup_GeoHash": "dr5ru",
                    "Drop_GeoHash": "dr5rv",
                    "Distance_Travelled_KM": 8.5,
                    "Booked_At": "2026-01-02 11:15:00",
                },
                tx=tx,
            )
            members.update_row(1, {"Reputation_Score": 4.9}, tx=tx)

        self.assertEqual(members.select(1)["Reputation_Score"], 4.9)
        self.assertIsNotNone(members.select(2))
        self.assertIsNotNone(rides.select(1))
        self.assertIsNotNone(bookings.select(1))

    # Verifies atomic failure: if one statement fails, the context manager rolls back the entire transaction.
    def test_context_manager_rolls_back_all_when_error_occurs(self):
        members = self.db.get_table("Members")
        rides = self.db.get_table("Rides")
        bookings = self.db.get_table("Bookings")

        with self.assertRaises(ValueError):
            with self.db.begin_transaction() as tx:
                members.insert_row(
                    {
                        "MemberID": 3,
                        "OAUTH_TOKEN": "tok_charlie",
                        "Email": "charlie@iitgn.ac.in",
                        "Full_Name": "Charlie",
                        "Reputation_Score": 4.1,
                        "Phone_Number": "7777777777",
                        "Created_At": "2026-01-03 12:00:00",
                        "Gender": "Other",
                    },
                    tx=tx,
                )
                rides.insert_row(
                    {
                        "RideID": 1,
                        "Host_MemberID": 1,
                        "Start_GeoHash": "dr5ru",
                        "End_GeoHash": "dr5rv",
                        "Departure_Time": "2026-01-03 13:00:00",
                        "Vehicle_Type": "SUV",
                        "Max_Capacity": 4,
                        "Available_Seats": 2,
                        "Base_Fare_Per_KM": 11.0,
                        "Ride_Status": "Open",
                        "Created_At": "2026-01-03 12:30:00",
                    },
                    tx=tx,
                )
                bookings.insert_row(
                    {
                        "BookingID": 1,
                        "RideID": 1,
                        "Passenger_MemberID": 2,
                        "Booking_Status": "Confirmed",
                        "Pickup_GeoHash": "dr5ru",
                        "Drop_GeoHash": "dr5rv",
                        "Distance_Travelled_KM": 9.0,
                        "Booked_At": "2026-01-03 12:45:00",
                    },
                    tx=tx,
                )
                members.update_row(1, {"Reputation_Score": 9.9}, tx=tx)

        # The valid insert above must also be absent because the whole transaction is rolled back.
        self.assertIsNone(members.select(3))
        self.assertEqual(members.select(1)["Reputation_Score"], 4.7)
        self.assertIsNone(rides.select(1))
        self.assertIsNone(bookings.select(1))

    # Verifies crash-like interruption in the middle of a transaction rolls back all staged work.
    def test_context_manager_rolls_back_all_on_mid_transaction_signal(self):
        members = self.db.get_table("Members")
        rides = self.db.get_table("Rides")
        bookings = self.db.get_table("Bookings")

        def _signal_handler(_signum, _frame):
            raise RuntimeError("Simulated mid-transaction signal")

        previous_handler = signal.getsignal(signal.SIGUSR1)
        signal.signal(signal.SIGUSR1, _signal_handler)
        try:
            with self.assertRaises(RuntimeError):
                with self.db.begin_transaction() as tx:
                    members.insert_row(
                        {
                            "MemberID": 4,
                            "OAUTH_TOKEN": "tok_signal",
                            "Email": "signal@iitgn.ac.in",
                            "Full_Name": "Signal User",
                            "Reputation_Score": 4.2,
                            "Phone_Number": "7444444444",
                            "Created_At": "2026-01-04 13:00:00",
                            "Gender": "Other",
                        },
                        tx=tx,
                    )
                    rides.insert_row(
                        {
                            "RideID": 1,
                            "Host_MemberID": 1,
                            "Start_GeoHash": "dr5ru",
                            "End_GeoHash": "dr5rv",
                            "Departure_Time": "2026-01-04 13:30:00",
                            "Vehicle_Type": "Hatchback",
                            "Max_Capacity": 4,
                            "Available_Seats": 3,
                            "Base_Fare_Per_KM": 10.5,
                            "Ride_Status": "Open",
                            "Created_At": "2026-01-04 13:00:00",
                        },
                        tx=tx,
                    )
                    bookings.insert_row(
                        {
                            "BookingID": 1,
                            "RideID": 1,
                            "Passenger_MemberID": 4,
                            "Booking_Status": "Confirmed",
                            "Pickup_GeoHash": "dr5ru",
                            "Drop_GeoHash": "dr5rv",
                            "Distance_Travelled_KM": 7.5,
                            "Booked_At": "2026-01-04 13:15:00",
                        },
                        tx=tx,
                    )
                    signal.raise_signal(signal.SIGUSR1)
                    members.update_row(1, {"Reputation_Score": 5.0}, tx=tx)
        finally:
            signal.signal(signal.SIGUSR1, previous_handler)

        self.assertIsNone(members.select(4))
        self.assertEqual(members.select(1)["Reputation_Score"], 4.7)
        self.assertIsNone(rides.select(1))
        self.assertIsNone(bookings.select(1))

    # Verifies power-failure style shutdown before commit does not produce any committed WAL operations.
    def test_power_failure_mid_transaction_has_no_committed_operations(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            wal_path = os.path.join(temp_dir, "atomicity_power_failure.wal.jsonl")

            crash_script = """
import os
import sys
from database.db_manager import DatabaseManager

wal_path = sys.argv[1]
db_manager = DatabaseManager()
db = db_manager.create_database("atomicity_crash_db")
db.create_table(
    name="Members",
    columns=["MemberID", "OAUTH_TOKEN", "Email", "Full_Name", "Reputation_Score", "Phone_Number", "Created_At", "Gender"],
    primary_key="MemberID",
    integrity_checks=[
        {"column": "OAUTH_TOKEN", "not_null": True},
        {"column": "Email", "not_null": True, "check": lambda value: value.endswith("@iitgn.ac.in")},
        {"column": "Full_Name", "not_null": True},
        {"column": "Reputation_Score", "not_null": True, "check": lambda value: 0.0 <= value <= 5.0},
        {"column": "Gender", "not_null": True, "check": lambda value: value in {"Male", "Female", "Other"}},
    ],
)

db.create_table(
    name="Rides",
    columns=["RideID", "Host_MemberID", "Start_GeoHash", "End_GeoHash", "Departure_Time", "Vehicle_Type", "Max_Capacity", "Available_Seats", "Base_Fare_Per_KM", "Ride_Status", "Created_At"],
    primary_key="RideID",
    foreign_keys=[
        {
            "column": "Host_MemberID",
            "references_table": "Members",
            "references_column": "MemberID",
        }
    ],
)

db.create_table(
    name="Bookings",
    columns=["BookingID", "RideID", "Passenger_MemberID", "Booking_Status", "Pickup_GeoHash", "Drop_GeoHash", "Distance_Travelled_KM", "Booked_At"],
    primary_key="BookingID",
    foreign_keys=[
        {
            "column": "RideID",
            "references_table": "Rides",
            "references_column": "RideID",
            "on_delete": "CASCADE",
        },
        {
            "column": "Passenger_MemberID",
            "references_table": "Members",
            "references_column": "MemberID",
            "on_delete": "CASCADE",
        },
    ],
)

members = db.get_table("Members")
rides = db.get_table("Rides")
bookings = db.get_table("Bookings")
tx = db.begin_transaction()
tx.wal_path = wal_path
members.insert_row(
    {
        "MemberID": 1,
        "OAUTH_TOKEN": "tok_crash",
        "Email": "crash@iitgn.ac.in",
        "Full_Name": "Crash User",
        "Reputation_Score": 4.0,
        "Phone_Number": "7000000000",
        "Created_At": "2026-01-10 10:00:00",
        "Gender": "Other",
    },
    tx=tx,
)
rides.insert_row(
    {
        "RideID": 1,
        "Host_MemberID": 1,
        "Start_GeoHash": "dr5ru",
        "End_GeoHash": "dr5rv",
        "Departure_Time": "2026-01-10 10:30:00",
        "Vehicle_Type": "Sedan",
        "Max_Capacity": 4,
        "Available_Seats": 3,
        "Base_Fare_Per_KM": 12.0,
        "Ride_Status": "Open",
        "Created_At": "2026-01-10 10:15:00",
    },
    tx=tx,
)
bookings.insert_row(
    {
        "BookingID": 1,
        "RideID": 1,
        "Passenger_MemberID": 1,
        "Booking_Status": "Confirmed",
        "Pickup_GeoHash": "dr5ru",
        "Drop_GeoHash": "dr5rv",
        "Distance_Travelled_KM": 8.0,
        "Booked_At": "2026-01-10 10:20:00",
    },
    tx=tx,
)
os._exit(1)
""".strip()

            env = os.environ.copy()
            env["PYTHONPATH"] = BASE_DIR + os.pathsep + env.get("PYTHONPATH", "")
            subprocess.run(
                [sys.executable, "-c", crash_script, wal_path],
                check=False,
                env=env,
                cwd=BASE_DIR,
            )

            committed_ops = Transaction.committed_operations_from_wal(wal_path)
            self.assertEqual(len(committed_ops), 0)

    def tearDown(self):
        self.db_manager.delete_database("test_integrity_db")


if __name__ == "__main__":
    unittest.main()
