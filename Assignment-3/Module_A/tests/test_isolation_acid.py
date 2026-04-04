import os
import sys
import threading
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager


class TestIsolationACID(unittest.TestCase):
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
            }
        )

    # Verifies an uncommitted insert is hidden from non-transactional readers.
    def test_uncommitted_insert_not_visible_outside_transaction(self):
        members = self.db.get_table("Members")
        tx = self.db.begin_transaction()

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

        self.assertIsNone(members.select(3))
        self.assertIsNotNone(members.select(3, tx=tx))

        self.db.rollback(tx)

    # Verifies an uncommitted update is hidden from non-transactional readers.
    def test_uncommitted_update_not_visible_outside_transaction(self):
        members = self.db.get_table("Members")
        tx = self.db.begin_transaction()

        members.update_row(1, {"Reputation_Score": 4.0}, tx=tx)

        self.assertEqual(members.select(1)["Reputation_Score"], 4.7)
        self.assertEqual(members.select(1, tx=tx)["Reputation_Score"], 4.0)

        self.db.rollback(tx)

    # Verifies an uncommitted delete is hidden from non-transactional readers.
    def test_uncommitted_delete_not_visible_outside_transaction(self):
        members = self.db.get_table("Members")
        tx = self.db.begin_transaction()

        members.delete_row(2, tx=tx)

        self.assertIsNotNone(members.select(2))
        self.assertIsNone(members.select(2, tx=tx))

        self.db.rollback(tx)

    # Verifies transaction-aware range and full-table reads include staged state while external reads remain unchanged.
    def test_tx_select_all_and_range_reflect_staged_state_only(self):
        members = self.db.get_table("Members")
        tx = self.db.begin_transaction()

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
        members.update_row(1, {"Reputation_Score": 4.9}, tx=tx)

        external_ids = [row["MemberID"] for row in members.select_all()]
        tx_ids = [row["MemberID"] for row in members.select_all(tx=tx)]
        tx_range_ids = [row["MemberID"] for row in members.select_range(1, 3, tx=tx)]

        self.assertEqual(external_ids, [1, 2])
        self.assertEqual(tx_ids, [1, 2, 3])
        self.assertEqual(tx_range_ids, [1, 2, 3])

        self.db.rollback(tx)

    # Verifies a concurrent reader thread only sees committed state while another transaction keeps updates uncommitted.
    def test_concurrent_reader_cannot_see_uncommitted_update(self):
        members = self.db.get_table("Members")
        tx = self.db.begin_transaction()
        members.update_row(1, {"Reputation_Score": 4.0}, tx=tx)

        observed_balances = []

        def read_balance_in_thread():
            row = members.select(1)
            observed_balances.append(row["Reputation_Score"])

        worker = threading.Thread(target=read_balance_in_thread)
        worker.start()
        worker.join()

        self.assertEqual(observed_balances, [4.7])
        self.assertEqual(members.select(1, tx=tx)["Reputation_Score"], 4.0)

        self.db.rollback(tx)

    # Verifies the implementation rejects starting a second transaction in the same thread.
    def test_second_transaction_in_same_thread_is_rejected(self):
        tx = self.db.begin_transaction()
        with self.assertRaises(ValueError):
            self.db.begin_transaction()
        self.db.rollback(tx)

    # Verifies multiple transactions can coexist across threads and commit independently.
    def test_concurrent_transactions_across_threads_can_both_commit(self):
        members = self.db.get_table("Members")
        tx_main = self.db.begin_transaction()
        members.update_row(1, {"Reputation_Score": 4.0}, tx=tx_main)

        thread_ready = threading.Event()
        allow_thread_commit = threading.Event()
        thread_errors = []

        def worker():
            try:
                tx_thread = self.db.begin_transaction()
                members.update_row(2, {"Reputation_Score": 3.0}, tx=tx_thread)
                thread_ready.set()
                allow_thread_commit.wait(timeout=2)
                self.db.commit(tx_thread)
            except Exception as exc:  # noqa: BLE001
                thread_errors.append(exc)
                thread_ready.set()

        thread = threading.Thread(target=worker)
        thread.start()
        thread_ready.wait(timeout=2)

        self.assertEqual(thread_errors, [])
        self.assertEqual(members.select(1)["Reputation_Score"], 4.7)
        self.assertEqual(members.select(2)["Reputation_Score"], 3.9)

        self.db.commit(tx_main)
        allow_thread_commit.set()
        thread.join(timeout=2)

        self.assertEqual(thread_errors, [])
        self.assertEqual(members.select(1)["Reputation_Score"], 4.0)
        self.assertEqual(members.select(2)["Reputation_Score"], 3.0)

    def tearDown(self):
        self.db_manager.delete_database("test_integrity_db")


if __name__ == "__main__":
    unittest.main()
