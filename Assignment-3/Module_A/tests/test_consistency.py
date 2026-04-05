import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager


class TestConsistency(unittest.TestCase):
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
                {"column": "Email", "not_null": True, "check": lambda value: value.endswith("@iitgn.ac.in"), "message": "Email must be in iitgn.ac.in domain"},
                {"column": "Full_Name", "not_null": True},
                {"column": "Reputation_Score", "not_null": True, "check": lambda value: 0.0 <= value <= 5.0, "message": "Reputation_Score must be between 0.0 and 5.0"},
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
        tx = self.db.begin_transaction()
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
            },
            tx=tx,
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
            },
            tx=tx,
        )
        self.db.commit(tx)

    def _insert_valid_ride(self, ride_id: int = 10, tx=None):
        rides = self.db.get_table("Rides")
        rides.insert_row(
            {
                "RideID": ride_id,
                "Host_MemberID": 1,
                "Start_GeoHash": "dr5ru",
                "End_GeoHash": "dr5rv",
                "Departure_Time": "2026-04-05 09:30:00",
                "Vehicle_Type": "Sedan",
                "Max_Capacity": 4,
                "Available_Seats": 3,
                "Base_Fare_Per_KM": 12.5,
                "Ride_Status": "Open",
                "Created_At": "2026-04-05 08:30:00",
            },
            tx=tx,
        )

    # Verifies valid rows across Members, Rides, and Bookings satisfy all consistency constraints.
    def test_valid_chain_insert_succeeds(self):
        bookings = self.db.get_table("Bookings")
        tx = self.db.begin_transaction()

        self._insert_valid_ride(1, tx=tx)

        bookings.insert_row(
            {
                "BookingID": 1,
                "RideID": 1,
                "Passenger_MemberID": 2,
                "Booking_Status": "Confirmed",
                "Pickup_GeoHash": "dr5ru",
                "Drop_GeoHash": "dr5rv",
                "Distance_Travelled_KM": 8.2,
                "Booked_At": "2026-04-05 08:45:00",
            },
            tx=tx,
        )
        self.db.commit(tx)

        self.assertIsNotNone(bookings.select(1))

    # Verifies NOT NULL and CHECK consistency by rejecting invalid member records.
    def test_member_constraints_reject_invalid_values(self):
        members = self.db.get_table("Members")

        with self.assertRaises(ValueError):
            members.insert_row(
                {
                    "MemberID": 3,
                    "OAUTH_TOKEN": "tok_invalid_domain",
                    "Email": "user@gmail.com",
                    "Full_Name": "Invalid Domain",
                    "Reputation_Score": 4.0,
                    "Phone_Number": "7777777777",
                    "Created_At": "2026-01-03 12:00:00",
                    "Gender": "Other",
                }
            )

        with self.assertRaises(ValueError):
            members.insert_row(
                {
                    "MemberID": 4,
                    "OAUTH_TOKEN": "tok_invalid_score",
                    "Email": "valid@iitgn.ac.in",
                    "Full_Name": "Invalid Score",
                    "Reputation_Score": 7.0,
                    "Phone_Number": "6666666666",
                    "Created_At": "2026-01-04 13:00:00",
                    "Gender": "Female",
                }
            )

    # Verifies cross-column consistency constraints on rides are enforced.
    def test_ride_cross_column_constraints_reject_invalid_values(self):
        rides = self.db.get_table("Rides")

        with self.assertRaises(ValueError):
            rides.insert_row(
                {
                    "RideID": 2,
                    "Host_MemberID": 1,
                    "Start_GeoHash": "dr5ru",
                    "End_GeoHash": "dr5ru",
                    "Departure_Time": "2026-04-05 10:00:00",
                    "Vehicle_Type": "SUV",
                    "Max_Capacity": 4,
                    "Available_Seats": 2,
                    "Base_Fare_Per_KM": 10.0,
                    "Ride_Status": "Open",
                    "Created_At": "2026-04-05 09:00:00",
                }
            )

        with self.assertRaises(ValueError):
            rides.insert_row(
                {
                    "RideID": 3,
                    "Host_MemberID": 1,
                    "Start_GeoHash": "dr5ru",
                    "End_GeoHash": "dr5rv",
                    "Departure_Time": "2026-04-05 11:00:00",
                    "Vehicle_Type": "SUV",
                    "Max_Capacity": 3,
                    "Available_Seats": 5,
                    "Base_Fare_Per_KM": 10.0,
                    "Ride_Status": "Open",
                    "Created_At": "2026-04-05 10:00:00",
                }
            )

    # Verifies foreign-key consistency by rejecting references to non-existent parent rows.
    def test_foreign_key_constraints_reject_missing_references(self):
        rides = self.db.get_table("Rides")
        bookings = self.db.get_table("Bookings")

        with self.assertRaises(ValueError):
            rides.insert_row(
                {
                    "RideID": 4,
                    "Host_MemberID": 999,
                    "Start_GeoHash": "dr5ru",
                    "End_GeoHash": "dr5rv",
                    "Departure_Time": "2026-04-05 12:00:00",
                    "Vehicle_Type": "Sedan",
                    "Max_Capacity": 4,
                    "Available_Seats": 3,
                    "Base_Fare_Per_KM": 11.0,
                    "Ride_Status": "Open",
                    "Created_At": "2026-04-05 11:00:00",
                }
            )

        # Create a valid ride, then validate booking FK failure independently.
        self._insert_valid_ride(5)

        with self.assertRaises(ValueError):
            bookings.insert_row(
                {
                    "BookingID": 2,
                    "RideID": 5,
                    "Passenger_MemberID": 999,
                    "Booking_Status": "Pending",
                    "Pickup_GeoHash": "dr5ru",
                    "Drop_GeoHash": "dr5rv",
                    "Distance_Travelled_KM": 4.0,
                    "Booked_At": "2026-04-05 11:45:00",
                }
            )

    def tearDown(self):
        self.db_manager.delete_database("test_integrity_db")


if __name__ == "__main__":
    unittest.main()
