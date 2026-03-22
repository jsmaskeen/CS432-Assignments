import random
import string
import time
from datetime import datetime, timedelta
from decimal import Decimal
import sys
import os

# Append the current directory so we can import from backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from sqlalchemy import insert
from db.session import SessionLocal

from models.member import Member
from models.auth_credential import AuthCredential
from models.location import Location
from models.ride import Ride
from models.booking import Booking
from models.preference import UserPreference
from models.review import ReputationReview
from models.settlement import CostSettlement
from models.chat_message import RideChatMessage
from models.saved_address import SavedAddress
from models.ride_participant import RideParticipant

from core.security import hash_password

# ==============================================================================
# CONFIGURATION - NUMBER OF RECORDS TO GENERATE
# ==============================================================================
NUM_USERS = 20_000
NUM_LOCATIONS = 1_000
NUM_RIDES = 20_000
NUM_BOOKINGS = 30_000
NUM_REVIEWS = 15_000
NUM_CHATS = 40_000

BATCH_SIZE = 5_000

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def run_massive_seed():
    db: Session = SessionLocal()
    
    print("\n=========================================================")
    print("      INITIALIZING MASSIVE DATABASE PRE-POPULATION       ")
    print("=========================================================\n")
    start_time = time.time()
    
    try:
        # ---------------------------------------------------------
        # 1. MEMBERS & AUTH CREDENTIALS
        # ---------------------------------------------------------
        print(f"-> Generating {NUM_USERS} Users and Passwords...")
        members_data = []
        auth_data = []
        
        # Get latest MemberID to avoid collisions
        max_id = db.query(Member.MemberID).order_by(Member.MemberID.desc()).first()
        start_member_id = (max_id[0] if max_id else 0) + 1
        
        # Fake password hash
        mock_hash = hash_password("password123!")
        
        for i in range(NUM_USERS):
            curr_id = start_member_id + i
            un = f"user_{generate_random_string(6)}_{curr_id}"
            
            members_data.append({
                "MemberID": curr_id,
                "OAUTH_TOKEN": f"local_{un}",
                "Email": f"{un}@iitgn.ac.in",
                "Full_Name": f"Mass Seed {curr_id}",
                "Reputation_Score": Decimal(str(round(random.uniform(1.0, 5.0), 1))),
                "Phone_Number": "".join(random.choices(string.digits, k=10)),
                "Gender": random.choice(["Male", "Female", "Other"]),
                "Created_At": datetime.now()
            })
            
            auth_data.append({
                "MemberID": curr_id,
                "Username": un,
                "Password_Hash": mock_hash,
                "Role": "user",
                "Created_At": datetime.now()
            })
            
        for i in range(0, len(members_data), BATCH_SIZE):
            db.execute(insert(Member), members_data[i:i+BATCH_SIZE])
            db.execute(insert(AuthCredential), auth_data[i:i+BATCH_SIZE])
        db.commit()
        
        # Fetch all available members for next steps
        all_members = [m[0] for m in db.query(Member.MemberID).all()]

        # ---------------------------------------------------------
        # 2. LOCATIONS
        # ---------------------------------------------------------
        print(f"-> Generating {NUM_LOCATIONS} Locations...")
        locations_data = []
        for i in range(NUM_LOCATIONS):
            locations_data.append({
                "Location_Name": f"Loc_{generate_random_string(4)}_{i}",
                "Location_Type": random.choice(["City", "Neighborhood", "Landmark"]),
                "GeoHash": generate_random_string(6)
            })
            
        for i in range(0, len(locations_data), BATCH_SIZE):
            db.execute(insert(Location), locations_data[i:i+BATCH_SIZE])
        db.commit()

        # ---------------------------------------------------------
        # 2.5 USER PREFERENCES & SAVED ADDRESSES
        # ---------------------------------------------------------
        print(f"-> Generating Preferences for users...")
        prefs_data = []
        for m_id in all_members[:NUM_USERS]: 
            prefs_data.append({
                "MemberID": m_id,
                "Gender_Preference": random.choice(["Any", "Same-Gender Only"]),
                "Notify_On_New_Ride": random.choice([True, False]),
                "Music_Preference": random.choice(["Pop", "Rock", "Jazz", None])
            })
        for i in range(0, len(prefs_data), BATCH_SIZE):
            db.execute(insert(UserPreference), prefs_data[i:i+BATCH_SIZE])
        db.commit()

        # ---------------------------------------------------------
        # 3. RIDES
        # ---------------------------------------------------------
        print(f"-> Generating {NUM_RIDES} Rides...")
        rides_data = []
        max_ride = db.query(Ride.RideID).order_by(Ride.RideID.desc()).first()
        start_ride_id = (max_ride[0] if max_ride else 0) + 1
        
        vehicle_types = ["Hatchback", "Sedan", "SUV", "Bike", "Auto"]
        statuses = ["Open", "Full", "Cancelled", "Completed"]
        
        for i in range(NUM_RIDES):
            start_geo = generate_random_string(6)
            end_geo = generate_random_string(6)
            while end_geo == start_geo: end_geo = generate_random_string(6)
                
            rides_data.append({
                "RideID": start_ride_id + i,
                "Host_MemberID": random.choice(all_members),
                "Start_GeoHash": start_geo,
                "End_GeoHash": end_geo,
                "Departure_Time": datetime.now() + timedelta(days=random.randint(-10, 30)),
                "Vehicle_Type": random.choice(vehicle_types),
                "Max_Capacity": 4,
                "Available_Seats": random.randint(1, 4),
                "Base_Fare_Per_KM": Decimal(str(random.randint(10, 50))),
                "Ride_Status": random.choice(statuses),
                "Created_At": datetime.now()
            })
            
        for i in range(0, len(rides_data), BATCH_SIZE):
            db.execute(insert(Ride), rides_data[i:i+BATCH_SIZE])
        db.commit()

        all_rides = [r[0] for r in db.query(Ride.RideID).all()]

        # ---------------------------------------------------------
        # 4. BOOKINGS
        # ---------------------------------------------------------
        print(f"-> Generating {NUM_BOOKINGS} Bookings...")
        bookings_data = []
        b_statuses = ["Pending", "Confirmed", "Rejected", "Cancelled"]
        
        max_book = db.query(Booking.BookingID).order_by(Booking.BookingID.desc()).first()
        start_book_id = (max_book[0] if max_book else 0) + 1

        used_pairs = set()

        for i in range(NUM_BOOKINGS):
            r_id = random.choice(all_rides)
            p_id = random.choice(all_members)
            
            while (r_id, p_id) in used_pairs:
                r_id = random.choice(all_rides)
                p_id = random.choice(all_members)
            
            used_pairs.add((r_id, p_id))

            bookings_data.append({
                "BookingID": start_book_id + i,
                "RideID": r_id,
                "Passenger_MemberID": p_id,
                "Pickup_GeoHash": generate_random_string(6),
                "Drop_GeoHash": generate_random_string(6),
                "Distance_Travelled_KM": Decimal(str(random.randint(1, 40))),
                "Booking_Status": random.choice(b_statuses),
                "Booked_At": datetime.now()
            })
            
        for i in range(0, len(bookings_data), BATCH_SIZE):
            db.execute(insert(Booking), bookings_data[i:i+BATCH_SIZE])
        db.commit()

        # ---------------------------------------------------------
        # 5. REVIEWS & CHAT
        # ---------------------------------------------------------
        print(f"-> Generating {NUM_REVIEWS} Reviews...")
        reviews_data = []
        used_revs = set()
        
        for _ in range(NUM_REVIEWS):
            r_id = random.choice(all_rides)
            rev_er = random.choice(all_members)
            rev_ee = random.choice(all_members)
            
            while rev_ee == rev_er or (r_id, rev_er, rev_ee) in used_revs:
                rev_er = random.choice(all_members)
                rev_ee = random.choice(all_members)
                
            used_revs.add((r_id, rev_er, rev_ee))
            
            reviews_data.append({
                "RideID": r_id,
                "Reviewer_MemberID": rev_er,
                "Reviewee_MemberID": rev_ee,
                "Rating": random.randint(1, 5),
                "Comments": "Mass generated review text!",
                "Created_At": datetime.now()
            })
            
        for i in range(0, len(reviews_data), BATCH_SIZE):
            db.execute(insert(ReputationReview), reviews_data[i:i+BATCH_SIZE])
        db.commit()
        
        print(f"-> Generating {NUM_CHATS} Chat Messages...")
        chats_data = []
        for _ in range(NUM_CHATS):
            chats_data.append({
                "RideID": random.choice(all_rides),
                "Sender_MemberID": random.choice(all_members),
                "Message_Body": f"Hey, where are you? ({generate_random_string(8)})",
                "Sent_At": datetime.now()
            })
            
        for i in range(0, len(chats_data), BATCH_SIZE):
            db.execute(insert(RideChatMessage), chats_data[i:i+BATCH_SIZE])
        db.commit()

        # ---------------------------------------------------------
        # 6. COST SETTLEMENTS
        # ---------------------------------------------------------
        print(f"-> Generating Cost Settlements...")
        existing_settlements = {s[0] for s in db.query(CostSettlement.BookingID).all()}
        all_acc_bookings = [b[0] for b in db.query(Booking.BookingID).where(Booking.Booking_Status == "Confirmed").all() if b[0] not in existing_settlements][:10000]
        settlement_data = []
        
        for b_id in all_acc_bookings:
            settlement_data.append({
                "BookingID": b_id,
                "Calculated_Cost": Decimal(str(random.randint(50, 500))),
                "Payment_Status": random.choice(["Unpaid", "Settled"])
            })
            
        for i in range(0, len(settlement_data), BATCH_SIZE):
            db.execute(insert(CostSettlement), settlement_data[i:i+BATCH_SIZE])
        db.commit()
        
        elapsed = time.time() - start_time
        print(f"\n=========================================================")
        print(f"   SUCCESS! DATABASE MASSIVELY POPULATED IN {elapsed:.2f}s  ")
        print("=========================================================")
       
    except Exception as e:
        print(f"An error occurred during mass seeding: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    run_massive_seed()