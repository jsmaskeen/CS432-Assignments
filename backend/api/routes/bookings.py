import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.dependencies import get_current_member
from core.audit import audit_event
from core.routing import calculate_booking_distance_km, recalculate_ride_route_and_distances
from db.session import get_db_session
from models.booking import Booking
from models.member import Member
from models.ride import Ride
from models.ride_participant import RideParticipant
from schemas.ride import BookingCreateRequest, BookingReadResponse, BookingStopReadResponse

router = APIRouter(prefix="/rides", tags=["bookings"])
logger = logging.getLogger("rajak.bookings")


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
        audit_event(
            action="bookings.create",
            status="failed",
            actor_member_id=current_member.MemberID,
            actor_username=None,
            details={"reason": "ride_not_found", "ride_id": ride_id},
        )
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
        audit_event(
            action="bookings.create",
            status="failed",
            actor_member_id=current_member.MemberID,
            actor_username=None,
            details={"reason": "duplicate", "ride_id": ride_id},
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already booked this ride")

    try:
        booking_distance_km = calculate_booking_distance_km(
            payload.pickup_geohash,
            payload.drop_geohash,
        )
    except ValueError as exc:
        logger.warning(
            "bookings.create.invalid_distance ride_id=%s member_id=%s reason=%s",
            ride_id,
            current_member.MemberID,
            exc,
        )
        audit_event(
            action="bookings.create",
            status="failed",
            actor_member_id=current_member.MemberID,
            actor_username=None,
            details={"reason": "invalid_distance", "ride_id": ride_id, "error": str(exc)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "bookings.create.distance_calc_failed ride_id=%s member_id=%s",
            ride_id,
            current_member.MemberID,
        )
        audit_event(
            action="bookings.create",
            status="failed",
            actor_member_id=current_member.MemberID,
            actor_username=None,
            details={"reason": "distance_calculation_failed", "ride_id": ride_id},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not calculate booking distance right now",
        ) from exc

    booking = Booking(
        RideID=ride_id,
        Passenger_MemberID=current_member.MemberID,
        Booking_Status="Pending",
        Pickup_GeoHash=payload.pickup_geohash,
        Drop_GeoHash=payload.drop_geohash,
        Distance_Travelled_KM=booking_distance_km,
    )
    db.add(booking)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.exception("bookings.create.db_conflict ride_id=%s member_id=%s", ride_id, current_member.MemberID)
        audit_event(
            action="bookings.create",
            status="failed",
            actor_member_id=current_member.MemberID,
            actor_username=None,
            details={"reason": "db_conflict", "ride_id": ride_id},
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking failed due to conflict") from exc

    db.refresh(booking)
    logger.info("bookings.create.success booking_id=%s ride_id=%s member_id=%s", booking.BookingID, ride_id, current_member.MemberID)
    audit_event(
        action="bookings.create",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"booking_id": booking.BookingID, "ride_id": ride_id},
    )
    return booking


@router.get("/my/bookings", response_model=list[BookingReadResponse])
def my_bookings(current_member: Member = Depends(get_current_member), db: Session = Depends(get_db_session)) -> list[Booking]:
    logger.info("bookings.my.list member_id=%s", current_member.MemberID)
    stmt = select(Booking).where(Booking.Passenger_MemberID == current_member.MemberID).order_by(Booking.Booked_At.desc())
    return list(db.scalars(stmt))


@router.get("/{ride_id}/bookings/pending", response_model=list[BookingReadResponse])
def list_pending_bookings(
    ride_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> list[Booking]:
    ride = db.scalar(select(Ride).where(Ride.RideID == ride_id))
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if ride.Host_MemberID != current_member.MemberID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can view pending bookings")

    stmt = (
        select(Booking)
        .where(
            Booking.RideID == ride_id,
            Booking.Booking_Status == "Pending",
        )
        .order_by(Booking.Booked_At.desc())
    )
    bookings = list(db.scalars(stmt))
    member_ids = {booking.Passenger_MemberID for booking in bookings}
    members = {
        member.MemberID: member
        for member in db.scalars(select(Member).where(Member.MemberID.in_(member_ids)))
    }
    response = []
    for booking in bookings:
        member = members.get(booking.Passenger_MemberID)
        response.append(
            {
                "BookingID": booking.BookingID,
                "RideID": booking.RideID,
                "Passenger_MemberID": booking.Passenger_MemberID,
                "Booking_Status": booking.Booking_Status,
                "Pickup_GeoHash": booking.Pickup_GeoHash,
                "Drop_GeoHash": booking.Drop_GeoHash,
                "Distance_Travelled_KM": booking.Distance_Travelled_KM,
                "Booked_At": booking.Booked_At,
                "Passenger_Name": member.Full_Name if member else None,
                "Passenger_Rating": member.Reputation_Score if member else None,
            }
        )
    return response


@router.get("/{ride_id}/bookings/confirmed-stops", response_model=list[BookingStopReadResponse])
def list_confirmed_booking_stops(
    ride_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> list[Booking]:
    ride = db.scalar(select(Ride).where(Ride.RideID == ride_id))
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")

    stmt = (
        select(Booking)
        .where(
            Booking.RideID == ride_id,
            Booking.Booking_Status == "Confirmed",
        )
        .order_by(Booking.Booked_At.asc())
    )
    bookings = list(db.scalars(stmt))
    member_ids = {booking.Passenger_MemberID for booking in bookings}
    members = {
        member.MemberID: member
        for member in db.scalars(select(Member).where(Member.MemberID.in_(member_ids)))
    }
    response = []
    for booking in bookings:
        member = members.get(booking.Passenger_MemberID)
        response.append(
            {
                "BookingID": booking.BookingID,
                "Pickup_GeoHash": booking.Pickup_GeoHash,
                "Drop_GeoHash": booking.Drop_GeoHash,
                "Booked_At": booking.Booked_At,
                "Passenger_Name": member.Full_Name if member else None,
                "Passenger_Rating": member.Reputation_Score if member else None,
            }
        )
    return response


@router.delete("/bookings/{booking_id}")
def delete_booking(
    booking_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> dict[str, str]:
    booking = db.scalar(select(Booking).where(Booking.BookingID == booking_id))
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.Passenger_MemberID != current_member.MemberID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own booking")

    ride = db.scalar(select(Ride).where(Ride.RideID == booking.RideID))
    if ride is not None and ride.Host_MemberID == booking.Passenger_MemberID:
        if ride.Ride_Status in {"Started", "Completed"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a ride that has started or completed",
            )
        db.delete(ride)
        db.commit()
        audit_event(
            action="rides.delete",
            status="success",
            actor_member_id=current_member.MemberID,
            actor_username=None,
            details={"ride_id": ride.RideID, "trigger": "host_booking_delete"},
        )
        return {"message": "Ride deleted"}

    participant = db.scalar(
        select(RideParticipant).where(
            RideParticipant.RideID == booking.RideID,
            RideParticipant.MemberID == booking.Passenger_MemberID,
            RideParticipant.Role == "Passenger",
        )
    )
    db.delete(booking)
    if participant is not None:
        db.delete(participant)
    if ride is not None:
        ride.Available_Seats += 1
        if ride.Ride_Status == "Full":
            ride.Ride_Status = "Open"

    db.commit()
    audit_event(
        action="bookings.delete",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"booking_id": booking_id, "ride_id": booking.RideID},
    )
    return {"message": "Booking deleted"}


@router.post("/bookings/{booking_id}/accept", response_model=BookingReadResponse)
def accept_booking(
    booking_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> Booking:
    booking = db.scalar(select(Booking).where(Booking.BookingID == booking_id))
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    ride = db.scalar(select(Ride).where(Ride.RideID == booking.RideID))
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if ride.Host_MemberID != current_member.MemberID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can accept bookings")
    if booking.Booking_Status != "Pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking is not pending")
    if ride.Ride_Status != "Open":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ride is not open for booking")
    if ride.Available_Seats <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No seats available")

    booking.Booking_Status = "Confirmed"
    ride.Available_Seats -= 1
    if ride.Available_Seats == 0:
        ride.Ride_Status = "Full"

    participant = db.scalar(
        select(RideParticipant).where(
            RideParticipant.RideID == ride.RideID,
            RideParticipant.MemberID == booking.Passenger_MemberID,
        )
    )
    if participant is None:
        participant = RideParticipant(
            RideID=ride.RideID,
            MemberID=booking.Passenger_MemberID,
            Role="Passenger",
        )
        db.add(participant)

    db.flush()
    try:
        updated = recalculate_ride_route_and_distances(ride, db)
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    db.commit()
    db.refresh(booking)
    audit_event(
        action="bookings.accept",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"booking_id": booking.BookingID, "ride_id": ride.RideID, "distances_updated": updated},
    )
    return booking


@router.post("/bookings/{booking_id}/reject", response_model=BookingReadResponse)
def reject_booking(
    booking_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> Booking:
    booking = db.scalar(select(Booking).where(Booking.BookingID == booking_id))
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    ride = db.scalar(select(Ride).where(Ride.RideID == booking.RideID))
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if ride.Host_MemberID != current_member.MemberID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can reject bookings")
    if booking.Booking_Status != "Pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking is not pending")

    booking.Booking_Status = "Rejected"
    db.commit()
    db.refresh(booking)
    audit_event(
        action="bookings.reject",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"booking_id": booking.BookingID, "ride_id": ride.RideID},
    )
    return booking
