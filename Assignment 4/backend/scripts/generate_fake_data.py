from __future__ import annotations

import argparse
import random
import string
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, text

from core.security import hash_password
from db.session import SessionLocal
from models.auth_credential import AuthCredential
from models.booking import Booking
from models.chat_message import RideChatMessage
from models.member import Member
from models.review import ReputationReview
from models.ride import Ride
from models.ride_participant import RideParticipant
from models.settlement import CostSettlement

GEOHASH_CHARS = "0123456789bcdefghjkmnpqrstuvwxyz"


def random_geohash(length: int = 6) -> str:
    return "".join(random.choices(GEOHASH_CHARS, k=length))


def random_phone() -> str:
    return "".join(random.choices(string.digits, k=10))


def random_name(member_id: int) -> str:
    return f"Fake User {member_id}"


def random_gender() -> str:
    return random.choice(["Male", "Female", "Other"])


def ensure_members_and_auth(db, target_members: int) -> list[int]:
    existing_member_ids = [row[0] for row in db.execute(select(Member.MemberID)).all()]
    if len(existing_member_ids) >= target_members:
        return existing_member_ids

    to_create = target_members - len(existing_member_ids)
    now = datetime.now(UTC)
    password_hash = hash_password("password123")

    for _ in range(to_create):
        member = Member(
            OAUTH_TOKEN=f"oauth_fake_{random.randint(100000, 999999)}_{random.randint(1000, 9999)}",
            Email=f"fake_{random.randint(100000, 999999)}_{random.randint(1000, 9999)}@iitgn.ac.in",
            Full_Name="placeholder",
            Reputation_Score=Decimal(str(round(random.uniform(3.0, 5.0), 1))),
            Phone_Number=random_phone(),
            Gender=random_gender(),
            Created_At=now,
        )
        db.add(member)
        db.flush()

        member.Full_Name = random_name(member.MemberID)

        credential = AuthCredential(
            MemberID=member.MemberID,
            Username=f"fake_user_{member.MemberID}",
            Password_Hash=password_hash,
            Role="user",
            Created_At=now,
        )
        db.add(credential)

    db.flush()
    return [row[0] for row in db.execute(select(Member.MemberID)).all()]


def maybe_reset_ride_data(db) -> None:
    reset_sql = [
        "DELETE FROM Cost_Settlements",
        "DELETE FROM Reputation_Reviews",
        "DELETE FROM Ride_Chat",
        "DELETE FROM Ride_Participants",
        "DELETE FROM Bookings",
        "DELETE FROM Rides",
        "DELETE FROM Ride_Shard_Directory",
    ]
    for sql in reset_sql:
        db.execute(text(sql))


def generate_data(
    rides_count: int,
    max_passengers_per_ride: int,
    chats_per_ride: int,
    reset_ride_data: bool,
    target_members: int,
) -> None:
    db = SessionLocal()
    try:
        if reset_ride_data:
            maybe_reset_ride_data(db)
            db.flush()

        member_ids = ensure_members_and_auth(db, target_members)

        now = datetime.now(UTC)
        created_rides = 0
        created_bookings = 0
        created_participants = 0
        created_chats = 0
        created_reviews = 0
        created_settlements = 0

        for _ in range(rides_count):
            host_id = random.choice(member_ids)
            max_capacity = random.randint(2, 5)
            available_seats = max_capacity - 1
            start_gh = random_geohash()
            end_gh = random_geohash()
            while end_gh == start_gh:
                end_gh = random_geohash()

            ride = Ride(
                Host_MemberID=host_id,
                Start_GeoHash=start_gh,
                End_GeoHash=end_gh,
                Departure_Time=now + timedelta(hours=random.randint(1, 240)),
                Vehicle_Type=random.choice(["Sedan", "SUV", "Hatchback", "Bike"]),
                Max_Capacity=max_capacity,
                Available_Seats=available_seats,
                Base_Fare_Per_KM=Decimal(str(round(random.uniform(8, 35), 2))),
                Ride_Status="Open",
                Created_At=now,
            )
            db.add(ride)
            db.flush()
            created_rides += 1

            host_booking = Booking(
                RideID=ride.RideID,
                Passenger_MemberID=host_id,
                Booking_Status="Confirmed",
                Pickup_GeoHash=ride.Start_GeoHash,
                Drop_GeoHash=ride.End_GeoHash,
                Distance_Travelled_KM=Decimal(str(round(random.uniform(3, 45), 2))),
                Booked_At=now,
            )
            db.add(host_booking)
            created_bookings += 1

            db.add(RideParticipant(RideID=ride.RideID, MemberID=host_id, Role="Host", Joined_At=now))
            created_participants += 1

            eligible_passengers = [m for m in member_ids if m != host_id]
            random.shuffle(eligible_passengers)
            passenger_slots = min(max_passengers_per_ride, available_seats, len(eligible_passengers))
            passenger_count = random.randint(0, passenger_slots) if passenger_slots > 0 else 0
            selected_passengers = eligible_passengers[:passenger_count]

            for passenger_id in selected_passengers:
                booking = Booking(
                    RideID=ride.RideID,
                    Passenger_MemberID=passenger_id,
                    Booking_Status="Confirmed",
                    Pickup_GeoHash=ride.Start_GeoHash,
                    Drop_GeoHash=ride.End_GeoHash,
                    Distance_Travelled_KM=Decimal(str(round(random.uniform(3, 45), 2))),
                    Booked_At=now,
                )
                db.add(booking)
                db.flush()
                created_bookings += 1

                db.add(
                    RideParticipant(
                        RideID=ride.RideID,
                        MemberID=passenger_id,
                        Role="Passenger",
                        Joined_At=now,
                    )
                )
                created_participants += 1

                settlement = CostSettlement(
                    BookingID=booking.BookingID,
                    Calculated_Cost=Decimal(str(round(float(booking.Distance_Travelled_KM) * float(ride.Base_Fare_Per_KM), 2))),
                    Payment_Status=random.choice(["Unpaid", "Settled"]),
                )
                db.add(settlement)
                created_settlements += 1

                if random.random() < 0.65:
                    review = ReputationReview(
                        RideID=ride.RideID,
                        Reviewer_MemberID=passenger_id,
                        Reviewee_MemberID=host_id,
                        Rating=random.randint(3, 5),
                        Comments="Auto-generated review",
                        Created_At=now,
                    )
                    db.add(review)
                    created_reviews += 1

            ride.Available_Seats = max_capacity - 1 - passenger_count
            ride.Ride_Status = "Full" if ride.Available_Seats == 0 else "Open"

            participants_for_chat = [host_id, *selected_passengers]
            for i in range(chats_per_ride):
                sender = random.choice(participants_for_chat)
                chat = RideChatMessage(
                    RideID=ride.RideID,
                    Sender_MemberID=sender,
                    Message_Body=f"Auto fake chat message {i + 1} for ride {ride.RideID}",
                    Sent_At=now,
                )
                db.add(chat)
                created_chats += 1

        db.commit()

        print("Fake data generation complete")
        print(f"rides_created={created_rides}")
        print(f"bookings_created={created_bookings}")
        print(f"participants_created={created_participants}")
        print(f"chats_created={created_chats}")
        print(f"reviews_created={created_reviews}")
        print(f"settlements_created={created_settlements}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate lightweight fake data for sharding demos")
    parser.add_argument("--members", type=int, default=80, help="Target minimum number of members")
    parser.add_argument("--rides", type=int, default=120, help="Number of rides to generate")
    parser.add_argument(
        "--max-passengers-per-ride",
        type=int,
        default=3,
        help="Maximum confirmed passengers per ride (excluding host)",
    )
    parser.add_argument("--chats-per-ride", type=int, default=2, help="Chat messages per ride")
    parser.add_argument(
        "--reset-ride-data",
        action="store_true",
        help="Delete existing ride-centric data before generating fresh fake data",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")

    args = parser.parse_args()
    random.seed(args.seed)

    generate_data(
        rides_count=args.rides,
        max_passengers_per_ride=max(0, args.max_passengers_per_ride),
        chats_per_ride=max(0, args.chats_per_ride),
        reset_ride_data=args.reset_ride_data,
        target_members=max(2, args.members),
    )


if __name__ == "__main__":
    main()
