import logging
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from api.dependencies import get_current_member
from core.audit import audit_event
from core.sharding import get_ride_shard_id
from db.session import get_db_session
from db.sharding import SHARD_SESSION_MAKERS
from models.booking import Booking
from models.member import Member
from models.ride import Ride
from models.settlement import CostSettlement
from schemas.settlement import SettlementReadResponse, SettlementStatusUpdateRequest

router = APIRouter(prefix="/settlements", tags=["settlements"])
logger = logging.getLogger("rajak.settlements")


def _authorized_booking(
    booking_id: int,
    actor_member_id: int,
    db: Session,
) -> tuple[Booking, Ride]:
    booking = db.scalar(select(Booking).where(Booking.BookingID == booking_id))
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    ride = db.scalar(select(Ride).where(Ride.RideID == booking.RideID))
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")

    if actor_member_id not in {booking.Passenger_MemberID, ride.Host_MemberID}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this booking settlement")

    return booking, ride


def _ensure_settlement_for_booking(booking: Booking, ride: Ride, db: Session) -> CostSettlement | None:
    existing = db.scalar(select(CostSettlement).where(CostSettlement.BookingID == booking.BookingID))
    if existing is not None:
        return existing

    if booking.Booking_Status != "Confirmed" or ride.Ride_Status != "Completed":
        return None

    calculated_cost = (Decimal(booking.Distance_Travelled_KM) * Decimal(ride.Base_Fare_Per_KM)).quantize(Decimal("0.01"))
    settlement = CostSettlement(
        BookingID=booking.BookingID,
        Calculated_Cost=calculated_cost,
        Payment_Status="Unpaid",
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement


def _resolve_booking_shard_id(booking_id: int, primary_db: Session) -> int | None:
    booking = primary_db.scalar(select(Booking).where(Booking.BookingID == booking_id))
    if booking is not None:
        return get_ride_shard_id(booking.RideID, primary_db)

    for shard_id in sorted(SHARD_SESSION_MAKERS.keys()):
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            found = shard_db.scalar(select(Booking.BookingID).where(Booking.BookingID == booking_id))
            if found is not None:
                return shard_id
        finally:
            shard_db.close()

    return None


def _resolve_settlement_shard_id(settlement_id: int) -> int | None:
    for shard_id in sorted(SHARD_SESSION_MAKERS.keys()):
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            found = shard_db.scalar(select(CostSettlement.SettlementID).where(CostSettlement.SettlementID == settlement_id))
            if found is not None:
                return shard_id
        finally:
            shard_db.close()

    return None


@router.patch("/{settlement_id}/status", response_model=SettlementReadResponse)
def update_settlement_status(
    settlement_id: int,
    payload: SettlementStatusUpdateRequest,
    current_member: Member = Depends(get_current_member),
) -> CostSettlement:
    shard_id = _resolve_settlement_shard_id(settlement_id)
    if shard_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settlement not found")

    shard_db = SHARD_SESSION_MAKERS[shard_id]()
    try:
        settlement = shard_db.scalar(select(CostSettlement).where(CostSettlement.SettlementID == settlement_id))
        if settlement is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settlement not found")

        _authorized_booking(settlement.BookingID, current_member.MemberID, shard_db)

        settlement.Payment_Status = payload.payment_status
        shard_db.commit()
        shard_db.refresh(settlement)
    finally:
        shard_db.close()

    audit_event(
        action="settlements.update_status",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"settlement_id": settlement_id, "payment_status": payload.payment_status},
    )
    return settlement


@router.get("/booking/{booking_id}", response_model=SettlementReadResponse | None)
def get_booking_settlement(
    booking_id: int,
    current_member: Member = Depends(get_current_member),
    primary_db: Session = Depends(get_db_session),
) -> CostSettlement | None:
    shard_id = _resolve_booking_shard_id(booking_id, primary_db)
    if shard_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    shard_db = SHARD_SESSION_MAKERS[shard_id]()
    try:
        booking, ride = _authorized_booking(booking_id, current_member.MemberID, shard_db)
        settlement = _ensure_settlement_for_booking(booking, ride, shard_db)
        if settlement is not None:
            audit_event(
                action="settlements.auto_generate",
                status="success",
                actor_member_id=current_member.MemberID,
                actor_username=None,
                details={"booking_id": booking.BookingID, "settlement_id": settlement.SettlementID},
            )
            return settlement

        return shard_db.scalar(select(CostSettlement).where(CostSettlement.BookingID == booking_id))
    finally:
        shard_db.close()


@router.get("/my", response_model=list[SettlementReadResponse])
def my_settlements(
    current_member: Member = Depends(get_current_member),
) -> list[CostSettlement]:
    settlements: list[CostSettlement] = []
    created_count = 0

    for shard_id in sorted(SHARD_SESSION_MAKERS.keys()):
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            missing_stmt = (
                select(Booking, Ride)
                .join(Ride, Ride.RideID == Booking.RideID)
                .outerjoin(CostSettlement, CostSettlement.BookingID == Booking.BookingID)
                .where(
                    CostSettlement.SettlementID.is_(None),
                    Booking.Booking_Status == "Confirmed",
                    Ride.Ride_Status == "Completed",
                    or_(
                        Booking.Passenger_MemberID == current_member.MemberID,
                        Ride.Host_MemberID == current_member.MemberID,
                    ),
                )
            )
            missing = list(shard_db.execute(missing_stmt).all())
            for booking, ride in missing:
                settlement = _ensure_settlement_for_booking(booking, ride, shard_db)
                if settlement is not None:
                    created_count += 1

            stmt = (
                select(CostSettlement)
                .join(Booking, Booking.BookingID == CostSettlement.BookingID)
                .join(Ride, Ride.RideID == Booking.RideID)
                .where(
                    or_(
                        Booking.Passenger_MemberID == current_member.MemberID,
                        Ride.Host_MemberID == current_member.MemberID,
                    )
                )
                .order_by(CostSettlement.SettlementID.desc())
            )
            settlements.extend(list(shard_db.scalars(stmt)))
        finally:
            shard_db.close()

    if created_count > 0:
        audit_event(
            action="settlements.auto_generate.bulk",
            status="success",
            actor_member_id=current_member.MemberID,
            actor_username=None,
            details={"created": created_count},
        )

    settlements.sort(key=lambda settlement: settlement.SettlementID, reverse=True)
    return settlements
