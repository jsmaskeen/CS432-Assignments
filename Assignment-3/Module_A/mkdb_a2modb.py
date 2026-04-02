import os
import re
import ast

from database.db_manager import DatabaseManager

def parse_sql_values(sql_string):
    cleaned = sql_string.replace('NULL', 'None')
    matches = re.findall(r'\((.*?)\)', cleaned)
    
    parsed_rows = []
    for match in matches:
        if not match.strip(): continue
        try:
            row_tuple = ast.literal_eval(f"({match})")
            parsed_rows.append(row_tuple)
        except Exception:
            pass
            
    return parsed_rows

db_manager = DatabaseManager()

if "cabSharing" in db_manager.list_databases():
    db_manager.delete_database("cabSharing")
    
db = db_manager.create_database("cabSharing")

db.create_table(
    name="Locations",
    columns=["LocationID", "Location_Name", "Location_Type", "GeoHash"],
    primary_key="LocationID"
)

db.create_table(
    name="Members",
    columns=["MemberID", "OAUTH_TOKEN", "Email", "Full_Name", "Reputation_Score", "Phone_Number", "Created_At", "Gender"],
    primary_key="MemberID"
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
            "on_delete": "RESTRICT"
        }
    ]
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
            "on_delete": "CASCADE"
        },
        {
            "column": "Passenger_MemberID",
            "references_table": "Members",
            "references_column": "MemberID",
            "on_delete": "CASCADE"
        }
    ]
)

dump_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Assignment-2/Module_B/SQL-Dump/dump.sql"))

with open(dump_path, 'r', encoding='utf-8') as f:
    content = f.read()

loc_match = re.search(r"INSERT INTO `Locations` VALUES (.*?);", content, re.DOTALL)
locations_table = db.get_table("Locations")
if loc_match:
    rows = parse_sql_values(loc_match.group(1))
    for row in rows:
        # LocationID, Location_Name, Location_Type, GeoHash
        if len(row) == 4:
            locations_table.insert_row({
                "LocationID": row[0],
                "Location_Name": row[1],
                "Location_Type": row[2],
                "GeoHash": row[3]
            })
    print(f"Populated {len(rows)} Locations.")

mem_match = re.search(r"INSERT INTO `Members` VALUES (.*?);", content, re.DOTALL)
members_table = db.get_table("Members")
if mem_match:
    rows = parse_sql_values(mem_match.group(1))
    for row in rows:
        if len(row) == 8:
            members_table.insert_row({
                "MemberID": row[0], "OAUTH_TOKEN": row[1], "Email": row[2], 
                "Full_Name": row[3], "Reputation_Score": row[4], "Phone_Number": row[5], 
                "Created_At": row[6], "Gender": row[7]
            })
    print(f"Populated {len(rows)} Members.")

rides_match = re.search(r"INSERT INTO `Rides` VALUES (.*?);", content, re.DOTALL)
rides_table = db.get_table("Rides")
if rides_match:
    rows = parse_sql_values(rides_match.group(1))
    for row in rows:
        if len(row) == 11:
            rides_table.insert_row({
                "RideID": row[0], "Host_MemberID": row[1], "Start_GeoHash": row[2], 
                "End_GeoHash": row[3], "Departure_Time": row[4], "Vehicle_Type": row[5], 
                "Max_Capacity": row[6], "Available_Seats": row[7], "Base_Fare_Per_KM": row[8], 
                "Ride_Status": row[9], "Created_At": row[10]
            })
    print(f"Populated {len(rows)} Rides.")

bookings_match = re.search(r"INSERT INTO `Bookings` VALUES (.*?);", content, re.DOTALL)
bookings_table = db.get_table("Bookings")
if bookings_match:
    rows = parse_sql_values(bookings_match.group(1))
    for row in rows:
        if len(row) == 8:
            bookings_table.insert_row({
                "BookingID": row[0], "RideID": row[1], "Passenger_MemberID": row[2], 
                "Booking_Status": row[3], "Pickup_GeoHash": row[4], "Drop_GeoHash": row[5], 
                "Distance_Travelled_KM": row[6], "Booked_At": row[7]
            })
    print(f"Populated {len(rows)} Bookings.")


print(bookings_table.select(1))
