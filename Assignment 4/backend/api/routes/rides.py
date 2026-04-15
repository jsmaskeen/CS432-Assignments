import logging
from collections.abc import Generator
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.dependencies import get_current_admin_credential, get_current_member
from core.audit import audit_event
from core.chaos import consume_failure
from core.routing import calculate_booking_distance_km
from db.session import get_db_session
from db.sharding import SHARD_SESSION_MAKERS, shard_id_for_ride_id
from models.booking import Booking
from models.auth_credential import AuthCredential
from models.ride_participant import RideParticipant
from models.chat_message import RideChatMessage
from models.member import Member
from models.ride import Ride
from models.settlement import CostSettlement
from schemas.ride import RideCreateRequest, RideReadResponse, RideUpdateRequest, RideWithBookingsResponse

router = APIRouter(prefix="/rides", tags=["rides"])
logger = logging.getLogger("rajak.rides")


def get_shard_session_for_ride(ride_id: int):
    shard_id = shard_id_for_ride_id(ride_id)
    db = SHARD_SESSION_MAKERS[shard_id]()
    try:
        yield db
    finally:
        db.close()


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
    else:
        stmt = stmt.where(Ride.Ride_Status.in_(["Open", "Full"]))
    return list(db.scalars(stmt))


@router.get("/{ride_id}", response_model=RideReadResponse)
def get_ride(
    ride_id: int,
    db: Session = Depends(get_shard_session_for_ride),
) -> Ride:
    ride = db.scalar(select(Ride).where(Ride.RideID == ride_id))
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    return ride


@router.post("", response_model=RideReadResponse, status_code=status.HTTP_201_CREATED)
def create_ride(
    payload: RideCreateRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> Ride:
    logger.info("rides.create.attempt host_member_id=%s", current_member.MemberID)
    if payload.start_geohash == payload.end_geohash:
        logger.warning("rides.create.invalid_route host_member_id=%s", current_member.MemberID)
        audit_event(
            action="rides.create",
            status="failed",
            actor_member_id=current_member.MemberID,
            actor_username=None,
            details={"reason": "same_geohash"},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start and end geohash cannot be same")

    available_seats = payload.max_capacity - 1
    if available_seats < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Max capacity must be at least 1")

    try:
        host_booking_distance = calculate_booking_distance_km(
            payload.start_geohash,
            payload.end_geohash,
        )
    except ValueError as exc:
        logger.warning(
            "rides.create.invalid_host_distance host_member_id=%s reason=%s",
            current_member.MemberID,
            exc,
        )
        audit_event(
            action="rides.create",
            status="failed",
            actor_member_id=current_member.MemberID,
            actor_username=None,
            details={"reason": "invalid_host_distance", "error": str(exc)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rides.create.host_distance_calc_failed host_member_id=%s", current_member.MemberID)
        audit_event(
            action="rides.create",
            status="failed",
            actor_member_id=current_member.MemberID,
            actor_username=None,
            details={"reason": "host_distance_calculation_failed"},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not calculate host booking distance right now",
        ) from exc

    ride = Ride(
        Host_MemberID=current_member.MemberID,
        Start_GeoHash=payload.start_geohash,
        End_GeoHash=payload.end_geohash,
        Departure_Time=payload.departure_time,
        Vehicle_Type=payload.vehicle_type,
        Max_Capacity=payload.max_capacity,
        Available_Seats=available_seats,
        Base_Fare_Per_KM=payload.base_fare_per_km,
        Ride_Status="Full" if available_seats == 0 else "Open",
    )
    db.add(ride)
    db.flush()
    host_booking = Booking(
        RideID=ride.RideID,
        Passenger_MemberID=current_member.MemberID,
        Booking_Status="Confirmed",
        Pickup_GeoHash=ride.Start_GeoHash,
        Drop_GeoHash=ride.End_GeoHash,
        Distance_Travelled_KM=host_booking_distance,
    )
    host_participant = RideParticipant(
        RideID=ride.RideID,
        MemberID=current_member.MemberID,
        Role="Host",
    )
    message = RideChatMessage(
        RideID=ride.RideID,
        Sender_MemberID=current_member.MemberID,
        Message_Body="Ride chat created.",
    )
    db.add(host_booking)
    db.add(host_participant)
    db.add(message)
    db.commit()
    db.refresh(ride)
    logger.info("rides.create.success ride_id=%s host_member_id=%s", ride.RideID, current_member.MemberID)
    audit_event(
        action="rides.create",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={
            "ride_id": ride.RideID,
            "chat_message_id": message.MessageID,
            "host_booking_id": host_booking.BookingID,
            "host_participant_id": host_participant.ParticipantID,
        },
    )
    return ride


@router.patch("/{ride_id}", response_model=RideReadResponse)
def update_ride(
    ride_id: int,
    payload: RideUpdateRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_shard_session_for_ride),
) -> Ride:
    ride = db.scalar(select(Ride).where(Ride.RideID == ride_id))
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if ride.Host_MemberID != current_member.MemberID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can update this ride")

    new_start = payload.start_geohash if payload.start_geohash is not None else ride.Start_GeoHash
    new_end = payload.end_geohash if payload.end_geohash is not None else ride.End_GeoHash
    if new_start == new_end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start and end geohash cannot be same")

    if payload.start_geohash is not None:
        ride.Start_GeoHash = payload.start_geohash
    if payload.end_geohash is not None:
        ride.End_GeoHash = payload.end_geohash
    if payload.departure_time is not None:
        ride.Departure_Time = payload.departure_time
    if payload.vehicle_type is not None:
        ride.Vehicle_Type = payload.vehicle_type
    if payload.base_fare_per_km is not None:
        ride.Base_Fare_Per_KM = payload.base_fare_per_km

    confirmed_count = (
        db.scalar(
            select(func.count(Booking.BookingID)).where(
                Booking.RideID == ride.RideID,
                Booking.Booking_Status == "Confirmed",
                Booking.Passenger_MemberID != ride.Host_MemberID,
            )
        )
        or 0
    )

    if payload.filled_seats is not None:
        max_capacity = payload.max_capacity if payload.max_capacity is not None else ride.Max_Capacity
        if payload.filled_seats < confirmed_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filled seats cannot be less than confirmed bookings",
            )
        if payload.filled_seats > max_capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filled seats cannot exceed max capacity",
            )
        ride.Max_Capacity = max_capacity
        ride.Available_Seats = max_capacity - payload.filled_seats
    elif payload.max_capacity is not None:
        booked_seats = ride.Max_Capacity - ride.Available_Seats
        min_booked = max(booked_seats, confirmed_count)
        if payload.max_capacity < min_booked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Max capacity cannot be less than booked seats",
            )
        ride.Max_Capacity = payload.max_capacity
        ride.Available_Seats = payload.max_capacity - min_booked

    db.commit()
    db.refresh(ride)
    audit_event(
        action="rides.update",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"ride_id": ride.RideID},
    )
    return ride


@router.post("/{ride_id}/start", response_model=RideReadResponse)
def start_ride(
    ride_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> Ride:
    ride = db.scalar(select(Ride).where(Ride.RideID == ride_id))
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if ride.Host_MemberID != current_member.MemberID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can start this ride")
    if ride.Ride_Status not in {"Open", "Full"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ride cannot be started")

    ride.Ride_Status = "Started"
    db.commit()
    db.refresh(ride)
    audit_event(
        action="rides.start",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"ride_id": ride.RideID},
    )
    return ride


@router.get("/{ride_id}/with-bookings", response_model=RideWithBookingsResponse)
def get_ride_with_bookings(
    ride_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_shard_session_for_ride),
) -> RideWithBookingsResponse:
    ride = db.scalar(select(Ride).where(Ride.RideID == ride_id))
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if ride.Host_MemberID != current_member.MemberID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can view bookings for this ride")

    stmt = select(Booking).where(Booking.RideID == ride_id).order_by(Booking.Booked_At.desc())
    bookings = list(db.scalars(stmt))
    return RideWithBookingsResponse(ride=ride, bookings=bookings)


@router.post("/{ride_id}/end", response_model=RideReadResponse)
def end_ride(
    ride_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> Ride:
    ride = db.scalar(select(Ride).where(Ride.RideID == ride_id))
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if ride.Host_MemberID != current_member.MemberID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can end this ride")
    if ride.Ride_Status != "Started":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ride is not started")

    ride.Ride_Status = "Completed"

    bookings = list(
        db.scalars(
            select(Booking).where(
                Booking.RideID == ride.RideID,
                Booking.Booking_Status == "Confirmed",
                Booking.Passenger_MemberID != ride.Host_MemberID,
            )
        )
    )
    created_settlements = 0
    for booking in bookings:
        existing = db.scalar(select(CostSettlement).where(CostSettlement.BookingID == booking.BookingID))
        if existing is not None:
            continue
        if consume_failure("rides.end.before_settlement_insert"):
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Simulated failure at rides.end.before_settlement_insert",
            )
        calculated_cost = (Decimal(booking.Distance_Travelled_KM) * Decimal(ride.Base_Fare_Per_KM)).quantize(Decimal("0.01"))
        settlement = CostSettlement(
            BookingID=booking.BookingID,
            Calculated_Cost=calculated_cost,
            Payment_Status="Unpaid",
        )
        db.add(settlement)
        created_settlements += 1

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Settlement creation conflict") from exc

    db.refresh(ride)
    audit_event(
        action="rides.end",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"ride_id": ride.RideID, "settlements_created": created_settlements},
    )
    return ride


@router.delete("/{ride_id}")
def delete_ride(
    ride_id: int,
    admin_credential: AuthCredential = Depends(get_current_admin_credential),
    db: Session = Depends(get_db_session),
) -> dict[str, str]:
    ride = db.scalar(select(Ride).where(Ride.RideID == ride_id))
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if ride.Host_MemberID != admin_credential.MemberID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host admin can delete this ride")

    db.delete(ride)
    db.commit()
    audit_event(
        action="rides.delete",
        status="success",
        actor_member_id=admin_credential.MemberID,
        actor_username=admin_credential.Username,
        details={"ride_id": ride_id},
    )
    return {"message": "Ride deleted"}
