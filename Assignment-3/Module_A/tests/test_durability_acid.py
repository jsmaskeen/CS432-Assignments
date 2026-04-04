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


class TestDurabilityACID(unittest.TestCase):
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

    # Verifies committed writes remain durable for subsequent transactions in the same running process.
    def test_committed_data_persists_across_follow_up_transactions(self):
        members = self.db.get_table("Members")

        with self.db.begin_transaction() as tx:
            members.insert_row(
                {
                    "MemberID": 2,
                    "OAUTH_TOKEN": "tok_bob",
                    "Email": "bob@iitgn.ac.in",
                    "Full_Name": "Bob",
                    "Reputation_Score": 3.9,
                    "Phone_Number": "8888888888",
                    "Created_At": "2026-01-02 11:00:00",
                    "Gender": "Male",
                },
                tx=tx,
            )
            members.update_row(1, {"Reputation_Score": 4.9}, tx=tx)

        tx = self.db.begin_transaction()
        self.db.rollback(tx)

        self.assertEqual(members.select(1)["Reputation_Score"], 4.9)
        self.assertIsNotNone(members.select(2))

    # Verifies transaction lifecycle writes BEGIN/OP/COMMIT markers to the WAL file on successful commit.
    def test_wal_contains_commit_record_after_successful_commit(self):
        members = self.db.get_table("Members")

        with tempfile.TemporaryDirectory() as temp_dir:
            wal_path = os.path.join(temp_dir, "durability_commit.wal.jsonl")

            tx = self.db.begin_transaction()
            tx.wal_path = wal_path
            members.insert_row(
                {
                    "MemberID": 2,
                    "OAUTH_TOKEN": "tok_bob",
                    "Email": "bob@iitgn.ac.in",
                    "Full_Name": "Bob",
                    "Reputation_Score": 3.9,
                    "Phone_Number": "8888888888",
                    "Created_At": "2026-01-02 11:00:00",
                    "Gender": "Male",
                },
                tx=tx,
            )
            self.db.commit(tx)

            records = Transaction.read_wal_records(wal_path)
            record_types = [record.get("type") for record in records]

            self.assertIn("BEGIN", record_types)
            self.assertIn("OP", record_types)
            self.assertIn("COMMIT", record_types)

    # Verifies crash consistency with os._exit: staged but uncommitted WAL operations are not treated as committed.
    def test_power_failure_before_commit_keeps_wal_uncommitted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            wal_path = os.path.join(temp_dir, "durability_crash.wal.jsonl")

            crash_script = """
import os
import sys
from database.db_manager import DatabaseManager

wal_path = sys.argv[1]
db_manager = DatabaseManager()
db = db_manager.create_database("crash_wal_db")
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

table = db.get_table("Members")
tx = db.begin_transaction()
tx.wal_path = wal_path
table.insert_row({
    "MemberID": 1,
    "OAUTH_TOKEN": "tok_crash",
    "Email": "crash@iitgn.ac.in",
    "Full_Name": "Crash User",
    "Reputation_Score": 4.0,
    "Phone_Number": "7000000000",
    "Created_At": "2026-01-10 10:00:00",
    "Gender": "Other",
}, tx=tx)
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

            records = Transaction.read_wal_records(wal_path)
            record_types = [record.get("type") for record in records]
            committed_ops = Transaction.committed_operations_from_wal(wal_path)

            self.assertIn("BEGIN", record_types)
            self.assertIn("OP", record_types)
            self.assertNotIn("COMMIT", record_types)
            self.assertEqual(len(committed_ops), 0)

    # Verifies power failure after commit preserves durability by retaining committed WAL operations.
    def test_power_failure_after_commit_preserves_committed_wal_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            wal_path = os.path.join(temp_dir, "durability_post_commit_crash.wal.jsonl")

            crash_script = """
import os
import sys
from database.db_manager import DatabaseManager

wal_path = sys.argv[1]
db_manager = DatabaseManager()
db = db_manager.create_database("post_commit_crash_db")
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

table = db.get_table("Members")
tx = db.begin_transaction()
tx.wal_path = wal_path
table.insert_row({
    "MemberID": 1,
    "OAUTH_TOKEN": "tok_committed",
    "Email": "committed@iitgn.ac.in",
    "Full_Name": "Committed User",
    "Reputation_Score": 4.3,
    "Phone_Number": "7111111111",
    "Created_At": "2026-01-11 10:00:00",
    "Gender": "Female",
}, tx=tx)
db.commit(tx)
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

            records = Transaction.read_wal_records(wal_path)
            record_types = [record.get("type") for record in records]
            committed_ops = Transaction.committed_operations_from_wal(wal_path)

            self.assertIn("BEGIN", record_types)
            self.assertIn("OP", record_types)
            self.assertIn("COMMIT", record_types)
            self.assertEqual(len(committed_ops), 1)
            self.assertEqual(committed_ops[0].action, "insert")
            self.assertEqual(committed_ops[0].table_name, "Members")
            self.assertEqual(committed_ops[0].key, 1)

    # Verifies crash-consistency using a process signal: an interrupt inside a transaction rolls back all uncommitted writes.
    def test_sigint_inside_transaction_rolls_back_uncommitted_changes(self):
        members = self.db.get_table("Members")

        def _signal_handler(_signum, _frame):
            raise RuntimeError("Simulated crash signal")

        previous_handler = signal.getsignal(signal.SIGUSR1)
        signal.signal(signal.SIGUSR1, _signal_handler)
        try:
            with self.assertRaises(RuntimeError):
                with self.db.begin_transaction() as tx:
                    members.insert_row(
                        {
                            "MemberID": 3,
                            "OAUTH_TOKEN": "tok_temp",
                            "Email": "temp@iitgn.ac.in",
                            "Full_Name": "Temp User",
                            "Reputation_Score": 4.0,
                            "Phone_Number": "7777777777",
                            "Created_At": "2026-01-03 12:00:00",
                            "Gender": "Other",
                        },
                        tx=tx,
                    )
                    members.update_row(1, {"Reputation_Score": 4.2}, tx=tx)
                    signal.raise_signal(signal.SIGUSR1)
        finally:
            signal.signal(signal.SIGUSR1, previous_handler)

        self.assertIsNone(members.select(3))
        self.assertEqual(members.select(1)["Reputation_Score"], 4.7)

    # Verifies a post-commit signal does not invalidate already committed data.
    def test_sigint_after_commit_preserves_committed_state(self):
        members = self.db.get_table("Members")

        with self.db.begin_transaction() as tx:
            members.insert_row(
                {
                    "MemberID": 4,
                    "OAUTH_TOKEN": "tok_committed",
                    "Email": "committed@iitgn.ac.in",
                    "Full_Name": "Committed User",
                    "Reputation_Score": 4.4,
                    "Phone_Number": "7444444444",
                    "Created_At": "2026-01-04 13:00:00",
                    "Gender": "Female",
                },
                tx=tx,
            )

        def _signal_handler(_signum, _frame):
            raise RuntimeError("Simulated crash signal")

        previous_handler = signal.getsignal(signal.SIGUSR1)
        signal.signal(signal.SIGUSR1, _signal_handler)
        try:
            with self.assertRaises(RuntimeError):
                signal.raise_signal(signal.SIGUSR1)
        finally:
            signal.signal(signal.SIGUSR1, previous_handler)

        self.assertIsNotNone(members.select(4))
        self.assertEqual(members.select(4)["Reputation_Score"], 4.4)

    def tearDown(self):
        self.db_manager.delete_database("test_integrity_db")


if __name__ == "__main__":
    unittest.main()
