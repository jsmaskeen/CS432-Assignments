import logging
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.dependencies import get_current_member
from db.session import get_db_session
from models.booking import Booking
from models.member import Member
from models.ride import Ride
from schemas.ride import BookingCreateRequest, BookingReadResponse, RideCreateRequest, RideReadResponse

router = APIRouter(prefix="/rides", tags=["rides"])
logger = logging.getLogger("rajak.rides")


@router.get("", response_model=list[RideReadResponse])
def list_rides(
    only_open: bool = Query(default=True),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db_session),
) -> list[Ride]:
    logger.info("rides.list only_open=%s limit=%s", only_open, limit)
    stmt = select(Ride).order_by(Ride.Departure_Time.asc()).limit(limit)
    if only_open:
        stmt = stmt.where(Ride.Ride_Status == "Open")
    return list(db.scalars(stmt))


@router.post("", response_model=RideReadResponse, status_code=status.HTTP_201_CREATED)
def create_ride(
    payload: RideCreateRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> Ride:
    logger.info("rides.create.attempt host_member_id=%s", current_member.MemberID)
    if payload.start_geohash == payload.end_geohash:
        logger.warning("rides.create.invalid_route host_member_id=%s", current_member.MemberID)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start and end geohash cannot be same")

    ride = Ride(
        Host_MemberID=current_member.MemberID,
        Start_GeoHash=payload.start_geohash,
        End_GeoHash=payload.end_geohash,
        Departure_Time=payload.departure_time,
        Vehicle_Type=payload.vehicle_type,
        Max_Capacity=payload.max_capacity,
        Available_Seats=payload.max_capacity,
        Base_Fare_Per_KM=payload.base_fare_per_km,
        Ride_Status="Open",
    )
    db.add(ride)
    db.commit()
    db.refresh(ride)
    logger.info("rides.create.success ride_id=%s host_member_id=%s", ride.RideID, current_member.MemberID)
    return ride


@router.post("/{ride_id}/book", response_model=BookingReadResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    ride_id: int,
    payload: BookingCreateRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> Booking:
    logger.info("bookings.create.attempt ride_id=%s member_id=%s", ride_id, current_member.MemberID)
    ride = db.scalar(select(Ride).where(Ride.RideID == ride_id))
    if ride is None:
        logger.warning("bookings.create.ride_not_found ride_id=%s member_id=%s", ride_id, current_member.MemberID)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if ride.Ride_Status != "Open":
        logger.warning("bookings.create.ride_not_open ride_id=%s status=%s", ride_id, ride.Ride_Status)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ride is not open for booking")
    if ride.Host_MemberID == current_member.MemberID:
        logger.warning("bookings.create.host_self_book ride_id=%s member_id=%s", ride_id, current_member.MemberID)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Host cannot book own ride")
    if ride.Available_Seats <= 0:
        logger.warning("bookings.create.no_seats ride_id=%s", ride_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No seats available")

    existing = db.scalar(
        select(Booking).where(
            and_(
                Booking.RideID == ride_id,
                Booking.Passenger_MemberID == current_member.MemberID,
            )
        )
    )
    if existing is not None:
        logger.warning("bookings.create.duplicate ride_id=%s member_id=%s", ride_id, current_member.MemberID)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already booked this ride")

    booking = Booking(
        RideID=ride_id,
        Passenger_MemberID=current_member.MemberID,
        Booking_Status="Confirmed",
        Pickup_GeoHash=payload.pickup_geohash,
        Drop_GeoHash=payload.drop_geohash,
        Distance_Travelled_KM=Decimal(payload.distance_travelled_km),
    )
    db.add(booking)

    ride.Available_Seats -= 1
    if ride.Available_Seats == 0:
        ride.Ride_Status = "Full"

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.exception("bookings.create.db_conflict ride_id=%s member_id=%s", ride_id, current_member.MemberID)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking failed due to conflict") from exc

    db.refresh(booking)
    logger.info("bookings.create.success booking_id=%s ride_id=%s member_id=%s", booking.BookingID, ride_id, current_member.MemberID)
    return booking


@router.get("/my/bookings", response_model=list[BookingReadResponse])
def my_bookings(current_member: Member = Depends(get_current_member), db: Session = Depends(get_db_session)) -> list[Booking]:
    logger.info("bookings.my.list member_id=%s", current_member.MemberID)
    stmt = select(Booking).where(Booking.Passenger_MemberID == current_member.MemberID).order_by(Booking.Booked_At.desc())
    return list(db.scalars(stmt))
