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
            integrity_checks=[
                {"column": "Host_MemberID", "not_null": True},
                {"column": "Start_GeoHash", "not_null": True},
                {"column": "End_GeoHash", "not_null": True},
                {"column": "Departure_Time", "not_null": True},
                {"column": "Max_Capacity", "not_null": True, "check": lambda value: value > 0, "message": "Max_Capacity must be > 0"},
                {"column": "Available_Seats", "not_null": True, "check": lambda value: value >= 0, "message": "Available_Seats must be >= 0"},
                {"column": "Available_Seats", "check": lambda value, row: value <= row["Max_Capacity"], "message": "Available_Seats cannot exceed Max_Capacity"},
                {"column": "Start_GeoHash", "check": lambda value, row: value != row["End_GeoHash"], "message": "Start_GeoHash and End_GeoHash must differ"},
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
            integrity_checks=[
                {"column": "RideID", "not_null": True},
                {"column": "Passenger_MemberID", "not_null": True},
                {"column": "Booking_Status", "not_null": True},
                {"column": "Pickup_GeoHash", "not_null": True},
                {"column": "Drop_GeoHash", "not_null": True},
                {"column": "Distance_Travelled_KM", "not_null": True, "check": lambda value: value > 0, "message": "Distance_Travelled_KM must be > 0"},
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

        rides = self.db.get_table("Rides")
        rides.insert_row(
            {
                "RideID": 1,
                "Host_MemberID": 1,
                "Start_GeoHash": "dr5ru",
                "End_GeoHash": "dr5rv",
                "Departure_Time": "2026-01-02 12:00:00",
                "Vehicle_Type": "Sedan",
                "Max_Capacity": 4,
                "Available_Seats": 3,
                "Base_Fare_Per_KM": 12.0,
                "Ride_Status": "Open",
                "Created_At": "2026-01-02 11:30:00",
            }
        )

        bookings = self.db.get_table("Bookings")
        bookings.insert_row(
            {
                "BookingID": 1,
                "RideID": 1,
                "Passenger_MemberID": 2,
                "Booking_Status": "Confirmed",
                "Pickup_GeoHash": "dr5ru",
                "Drop_GeoHash": "dr5rv",
                "Distance_Travelled_KM": 8.0,
                "Booked_At": "2026-01-02 11:45:00",
            }
        )

    # Verifies an uncommitted insert is hidden from non-transactional readers.
    def test_uncommitted_insert_not_visible_outside_transaction(self):
        members = self.db.get_table("Members")
        rides = self.db.get_table("Rides")
        bookings = self.db.get_table("Bookings")
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
        rides.insert_row(
            {
                "RideID": 2,
                "Host_MemberID": 1,
                "Start_GeoHash": "dr5sw",
                "End_GeoHash": "dr5sx",
                "Departure_Time": "2026-01-03 12:30:00",
                "Vehicle_Type": "SUV",
                "Max_Capacity": 4,
                "Available_Seats": 2,
                "Base_Fare_Per_KM": 13.0,
                "Ride_Status": "Open",
                "Created_At": "2026-01-03 12:00:00",
            },
            tx=tx,
        )
        bookings.insert_row(
            {
                "BookingID": 2,
                "RideID": 2,
                "Passenger_MemberID": 2,
                "Booking_Status": "Confirmed",
                "Pickup_GeoHash": "dr5sw",
                "Drop_GeoHash": "dr5sx",
                "Distance_Travelled_KM": 9.1,
                "Booked_At": "2026-01-03 12:15:00",
            },
            tx=tx,
        )

        self.assertIsNone(members.select(3))
        self.assertIsNone(rides.select(2))
        self.assertIsNone(bookings.select(2))
        self.assertIsNotNone(members.select(3, tx=tx))
        self.assertIsNotNone(rides.select(2, tx=tx))
        self.assertIsNotNone(bookings.select(2, tx=tx))

        self.db.rollback(tx)

    # Verifies an uncommitted update is hidden from non-transactional readers.
    def test_uncommitted_update_not_visible_outside_transaction(self):
        members = self.db.get_table("Members")
        rides = self.db.get_table("Rides")
        bookings = self.db.get_table("Bookings")
        tx = self.db.begin_transaction()

        members.update_row(1, {"Reputation_Score": 4.0}, tx=tx)
        rides.update_row(1, {"Ride_Status": "Closed"}, tx=tx)
        bookings.update_row(1, {"Booking_Status": "Cancelled"}, tx=tx)

        self.assertEqual(members.select(1)["Reputation_Score"], 4.7)
        self.assertEqual(rides.select(1)["Ride_Status"], "Open")
        self.assertEqual(bookings.select(1)["Booking_Status"], "Confirmed")
        self.assertEqual(members.select(1, tx=tx)["Reputation_Score"], 4.0)
        self.assertEqual(rides.select(1, tx=tx)["Ride_Status"], "Closed")
        self.assertEqual(bookings.select(1, tx=tx)["Booking_Status"], "Cancelled")

        self.db.rollback(tx)

    # Verifies an uncommitted delete is hidden from non-transactional readers.
    def test_uncommitted_delete_not_visible_outside_transaction(self):
        members = self.db.get_table("Members")
        rides = self.db.get_table("Rides")
        bookings = self.db.get_table("Bookings")
        tx = self.db.begin_transaction()

        members.update_row(1, {"Reputation_Score": 4.0}, tx=tx)
        rides.update_row(1, {"Ride_Status": "Closed"}, tx=tx)
        bookings.delete_row(1, tx=tx)

        self.assertIsNotNone(members.select(1))
        self.assertIsNotNone(rides.select(1))
        self.assertIsNotNone(bookings.select(1))
        self.assertEqual(members.select(1, tx=tx)["Reputation_Score"], 4.0)
        self.assertEqual(rides.select(1, tx=tx)["Ride_Status"], "Closed")
        self.assertIsNone(bookings.select(1, tx=tx))

        self.db.rollback(tx)

    # Verifies transaction-aware range and full-table reads include staged state while external reads remain unchanged.
    def test_tx_select_all_and_range_reflect_staged_state_only(self):
        members = self.db.get_table("Members")
        rides = self.db.get_table("Rides")
        bookings = self.db.get_table("Bookings")
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
        rides.insert_row(
            {
                "RideID": 2,
                "Host_MemberID": 1,
                "Start_GeoHash": "dr5sw",
                "End_GeoHash": "dr5sx",
                "Departure_Time": "2026-01-03 12:30:00",
                "Vehicle_Type": "SUV",
                "Max_Capacity": 4,
                "Available_Seats": 2,
                "Base_Fare_Per_KM": 13.0,
                "Ride_Status": "Open",
                "Created_At": "2026-01-03 12:00:00",
            },
            tx=tx,
        )
        bookings.insert_row(
            {
                "BookingID": 2,
                "RideID": 2,
                "Passenger_MemberID": 2,
                "Booking_Status": "Confirmed",
                "Pickup_GeoHash": "dr5sw",
                "Drop_GeoHash": "dr5sx",
                "Distance_Travelled_KM": 9.1,
                "Booked_At": "2026-01-03 12:15:00",
            },
            tx=tx,
        )
        members.update_row(1, {"Reputation_Score": 4.9}, tx=tx)
        rides.update_row(1, {"Ride_Status": "Closed"}, tx=tx)
        bookings.update_row(1, {"Booking_Status": "Completed"}, tx=tx)

        external_ids = [row["MemberID"] for row in members.select_all()]
        tx_ids = [row["MemberID"] for row in members.select_all(tx=tx)]
        tx_range_ids = [row["MemberID"] for row in members.select_range(1, 3, tx=tx)]
        external_ride_ids = [row["RideID"] for row in rides.select_all()]
        tx_ride_ids = [row["RideID"] for row in rides.select_all(tx=tx)]
        tx_booking_ids = [row["BookingID"] for row in bookings.select_all(tx=tx)]

        self.assertEqual(external_ids, [1, 2])
        self.assertEqual(tx_ids, [1, 2, 3])
        self.assertEqual(tx_range_ids, [1, 2, 3])
        self.assertEqual(external_ride_ids, [1])
        self.assertEqual(tx_ride_ids, [1, 2])
        self.assertEqual(tx_booking_ids, [1, 2])

        self.db.rollback(tx)

    # Verifies a concurrent reader thread only sees committed state while another transaction keeps updates uncommitted.
    def test_concurrent_reader_cannot_see_uncommitted_update(self):
        members = self.db.get_table("Members")
        rides = self.db.get_table("Rides")
        bookings = self.db.get_table("Bookings")
        tx = self.db.begin_transaction()
        members.update_row(1, {"Reputation_Score": 4.0}, tx=tx)
        rides.update_row(1, {"Ride_Status": "Closed"}, tx=tx)
        bookings.update_row(1, {"Booking_Status": "Cancelled"}, tx=tx)

        observed_state = []

        def read_balance_in_thread():
            observed_state.append(
                (
                    members.select(1)["Reputation_Score"],
                    rides.select(1)["Ride_Status"],
                    bookings.select(1)["Booking_Status"],
                )
            )

        worker = threading.Thread(target=read_balance_in_thread)
        worker.start()
        worker.join()

        self.assertEqual(observed_state, [(4.7, "Open", "Confirmed")])
        self.assertEqual(members.select(1, tx=tx)["Reputation_Score"], 4.0)
        self.assertEqual(rides.select(1, tx=tx)["Ride_Status"], "Closed")
        self.assertEqual(bookings.select(1, tx=tx)["Booking_Status"], "Cancelled")

        self.db.rollback(tx)

    # Verifies the implementation rejects starting a second transaction in the same thread.
    def test_second_transaction_in_same_thread_is_rejected(self):
        tx = self.db.begin_transaction()
        members = self.db.get_table("Members")
        rides = self.db.get_table("Rides")
        bookings = self.db.get_table("Bookings")
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
                "RideID": 2,
                "Host_MemberID": 1,
                "Start_GeoHash": "dr5sw",
                "End_GeoHash": "dr5sx",
                "Departure_Time": "2026-01-03 12:30:00",
                "Vehicle_Type": "SUV",
                "Max_Capacity": 4,
                "Available_Seats": 2,
                "Base_Fare_Per_KM": 13.0,
                "Ride_Status": "Open",
                "Created_At": "2026-01-03 12:00:00",
            },
            tx=tx,
        )
        bookings.insert_row(
            {
                "BookingID": 2,
                "RideID": 2,
                "Passenger_MemberID": 2,
                "Booking_Status": "Confirmed",
                "Pickup_GeoHash": "dr5sw",
                "Drop_GeoHash": "dr5sx",
                "Distance_Travelled_KM": 9.1,
                "Booked_At": "2026-01-03 12:15:00",
            },
            tx=tx,
        )
        with self.assertRaises(ValueError):
            self.db.begin_transaction()
        self.db.rollback(tx)

    # Verifies multiple transactions can coexist across threads and commit independently.
    def test_concurrent_transactions_across_threads_can_both_commit(self):
        members = self.db.get_table("Members")
        rides = self.db.get_table("Rides")
        bookings = self.db.get_table("Bookings")
        tx_main = self.db.begin_transaction()
        members.update_row(1, {"Reputation_Score": 4.0}, tx=tx_main)
        rides.update_row(1, {"Ride_Status": "Closed"}, tx=tx_main)
        bookings.update_row(1, {"Booking_Status": "Cancelled"}, tx=tx_main)

        thread_ready = threading.Event()
        allow_thread_commit = threading.Event()
        thread_errors = []

        def worker():
            try:
                tx_thread = self.db.begin_transaction()
                members.insert_row(
                    {
                        "MemberID": 4,
                        "OAUTH_TOKEN": "tok_dana",
                        "Email": "dana@iitgn.ac.in",
                        "Full_Name": "Dana",
                        "Reputation_Score": 3.6,
                        "Phone_Number": "6666666666",
                        "Created_At": "2026-01-04 10:00:00",
                        "Gender": "Female",
                    },
                    tx=tx_thread,
                )
                rides.insert_row(
                    {
                        "RideID": 2,
                        "Host_MemberID": 1,
                        "Start_GeoHash": "dr5sw",
                        "End_GeoHash": "dr5sx",
                        "Departure_Time": "2026-01-04 10:30:00",
                        "Vehicle_Type": "SUV",
                        "Max_Capacity": 4,
                        "Available_Seats": 2,
                        "Base_Fare_Per_KM": 13.0,
                        "Ride_Status": "Open",
                        "Created_At": "2026-01-04 10:00:00",
                    },
                    tx=tx_thread,
                )
                bookings.insert_row(
                    {
                        "BookingID": 2,
                        "RideID": 2,
                        "Passenger_MemberID": 4,
                        "Booking_Status": "Confirmed",
                        "Pickup_GeoHash": "dr5sw",
                        "Drop_GeoHash": "dr5sx",
                        "Distance_Travelled_KM": 6.2,
                        "Booked_At": "2026-01-04 10:15:00",
                    },
                    tx=tx_thread,
                )
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
        self.assertEqual(rides.select(1)["Ride_Status"], "Open")
        self.assertEqual(bookings.select(1)["Booking_Status"], "Confirmed")

        self.db.commit(tx_main)
        allow_thread_commit.set()
        thread.join(timeout=2)

        self.assertEqual(thread_errors, [])
        self.assertEqual(members.select(1)["Reputation_Score"], 4.0)
        self.assertEqual(rides.select(1)["Ride_Status"], "Closed")
        self.assertEqual(bookings.select(1)["Booking_Status"], "Cancelled")
        self.assertEqual(members.select(4)["Reputation_Score"], 3.6)
        self.assertEqual(rides.select(2)["Ride_Status"], "Open")
        self.assertEqual(bookings.select(2)["Booking_Status"], "Confirmed")

    def tearDown(self):
        self.db_manager.delete_database("test_integrity_db")


if __name__ == "__main__":
    unittest.main()
