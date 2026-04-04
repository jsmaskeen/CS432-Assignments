import unittest
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager


class TestIntegrityChecks(unittest.TestCase):
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

    # Verifies the end-to-end success path in a single transaction by creating a host member, a ride, and a booking.
    def test_insert_valid_members_rides_bookings_chain(self):
        tx = self.db.begin_transaction()
        members = self.db.get_table("Members")
        members.insert_row(
            {
                "MemberID": 10,
                "OAUTH_TOKEN": "tok_host_10",
                "Email": "host10@iitgn.ac.in",
                "Full_Name": "Host Ten",
                "Reputation_Score": 4.5,
                "Phone_Number": "7777000010",
                "Created_At": "2026-04-05 08:10:00",
                "Gender": "Other",
            },
            tx=tx,
        )

        rides = self.db.get_table("Rides")
        rides.insert_row(
            {
                "RideID": 10,
                "Host_MemberID": 10,
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

        bookings = self.db.get_table("Bookings")
        bookings.insert_row(
            {
                "BookingID": 100,
                "RideID": 10,
                "Passenger_MemberID": 2,
                "Booking_Status": "Confirmed",
                "Pickup_GeoHash": "dr5ru",
                "Drop_GeoHash": "dr5rv",
                "Distance_Travelled_KM": 8.4,
                "Booked_At": "2026-04-05 08:45:00",
            },
            tx=tx,
        )
        self.db.commit(tx)
        self.assertIsNotNone(bookings.select(100))

    # Verifies member-level constraints by rejecting a non-IITGN email and a NULL full name.
    def test_members_not_null_and_domain_checks(self):
        members = self.db.get_table("Members")

        with self.assertRaises(ValueError):
            members.insert_row(
                {
                    "MemberID": 3,
                    "OAUTH_TOKEN": "tok_charlie",
                    "Email": "charlie@gmail.com",
                    "Full_Name": "Charlie",
                    "Reputation_Score": 4.1,
                    "Phone_Number": "7777777777",
                    "Created_At": "2026-01-03 12:00:00",
                    "Gender": "Other",
                }
            )

        with self.assertRaises(ValueError):
            members.insert_row(
                {
                    "MemberID": 4,
                    "OAUTH_TOKEN": "tok_dana",
                    "Email": "dana@iitgn.ac.in",
                    "Full_Name": None,
                    "Reputation_Score": 4.8,
                    "Phone_Number": "6666666666",
                    "Created_At": "2026-01-04 13:00:00",
                    "Gender": "Female",
                }
            )

    # Verifies update-time validation by rejecting reputation values outside the allowed range.
    def test_members_update_reputation_range_check(self):
        members = self.db.get_table("Members")

        with self.assertRaises(ValueError):
            members.update_row(1, {"Reputation_Score": 7.5})

    # Verifies cross-column ride constraints: start and end geohashes must differ, and seats cannot exceed capacity.
    def test_rides_cross_column_checks(self):
        rides = self.db.get_table("Rides")

        with self.assertRaises(ValueError):
            rides.insert_row(
                {
                    "RideID": 20,
                    "Host_MemberID": 1,
                    "Start_GeoHash": "dr5ru",
                    "End_GeoHash": "dr5ru",
                    "Departure_Time": "2026-04-05 09:30:00",
                    "Vehicle_Type": "SUV",
                    "Max_Capacity": 4,
                    "Available_Seats": 2,
                    "Base_Fare_Per_KM": 15.0,
                    "Ride_Status": "Open",
                    "Created_At": "2026-04-05 08:30:00",
                }
            )

        with self.assertRaises(ValueError):
            rides.insert_row(
                {
                    "RideID": 21,
                    "Host_MemberID": 1,
                    "Start_GeoHash": "dr5ru",
                    "End_GeoHash": "dr5rv",
                    "Departure_Time": "2026-04-05 09:30:00",
                    "Vehicle_Type": "SUV",
                    "Max_Capacity": 3,
                    "Available_Seats": 5,
                    "Base_Fare_Per_KM": 15.0,
                    "Ride_Status": "Open",
                    "Created_At": "2026-04-05 08:30:00",
                }
            )

    # Verifies foreign key enforcement by rejecting rides whose host member does not exist.
    def test_rides_fk_host_member_enforced(self):
        rides = self.db.get_table("Rides")
        with self.assertRaises(ValueError):
            rides.insert_row(
                {
                    "RideID": 22,
                    "Host_MemberID": 999,
                    "Start_GeoHash": "dr5ru",
                    "End_GeoHash": "dr5rv",
                    "Departure_Time": "2026-04-05 09:30:00",
                    "Vehicle_Type": "Sedan",
                    "Max_Capacity": 4,
                    "Available_Seats": 2,
                    "Base_Fare_Per_KM": 12.0,
                    "Ride_Status": "Open",
                    "Created_At": "2026-04-05 08:30:00",
                }
            )

    # Verifies booking constraints: distance must be positive and RideID must reference an existing ride.
    def test_bookings_distance_check_and_fk(self):
        self._insert_valid_ride(30)
        bookings = self.db.get_table("Bookings")

        with self.assertRaises(ValueError):
            bookings.insert_row(
                {
                    "BookingID": 301,
                    "RideID": 30,
                    "Passenger_MemberID": 2,
                    "Booking_Status": "Pending",
                    "Pickup_GeoHash": "dr5ru",
                    "Drop_GeoHash": "dr5rv",
                    "Distance_Travelled_KM": 0,
                    "Booked_At": "2026-04-05 08:45:00",
                }
            )

        with self.assertRaises(ValueError):
            bookings.insert_row(
                {
                    "BookingID": 302,
                    "RideID": 999,
                    "Passenger_MemberID": 2,
                    "Booking_Status": "Pending",
                    "Pickup_GeoHash": "dr5ru",
                    "Drop_GeoHash": "dr5rv",
                    "Distance_Travelled_KM": 6.5,
                    "Booked_At": "2026-04-05 08:46:00",
                }
            )

    # Verifies ON DELETE CASCADE behavior by deleting a ride and confirming dependent bookings are removed.
    def test_cascade_delete_from_rides_to_bookings(self):
        tx = self.db.begin_transaction()
        self._insert_valid_ride(40, tx=tx)
        bookings = self.db.get_table("Bookings")
        rides = self.db.get_table("Rides")

        bookings.insert_row(
            {
                "BookingID": 401,
                "RideID": 40,
                "Passenger_MemberID": 2,
                "Booking_Status": "Confirmed",
                "Pickup_GeoHash": "dr5ru",
                "Drop_GeoHash": "dr5rv",
                "Distance_Travelled_KM": 10.0,
                "Booked_At": "2026-04-05 08:50:00",
            },
            tx=tx,
        )
        self.db.commit(tx)
        self.assertIsNotNone(bookings.select(401))

        rides.delete_row(40)
        self.assertIsNone(bookings.select(401))

    # Verifies transactional behavior: constraints apply to staged writes and rollback discards uncommitted changes.
    def test_transaction_enforces_checks(self):
        rides = self.db.get_table("Rides")
        tx = self.db.begin_transaction()

        rides.insert_row(
            {
                "RideID": 50,
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

        with self.assertRaises(ValueError):
            rides.update_row(50, {"Available_Seats": 8}, tx=tx)

        self.db.rollback(tx)
        self.assertIsNone(rides.select(50))

    # Verifies schema validation by ensuring table creation fails when a constraint references a missing column.
    def test_invalid_integrity_configuration(self):
        with self.assertRaises(ValueError):
            self.db.create_table(
                name="bad_table",
                columns=["id", "value"],
                primary_key="id",
                integrity_checks=[{"column": "missing_col", "not_null": True}],
            )

    def tearDown(self):
        self.db_manager.delete_database("test_integrity_db")


if __name__ == "__main__":
    unittest.main()
