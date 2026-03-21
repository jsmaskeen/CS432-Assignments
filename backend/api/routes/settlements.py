import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from api.dependencies import get_current_member
from core.audit import audit_event
from db.session import get_db_session
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


@router.patch("/{settlement_id}/status", response_model=SettlementReadResponse)
def update_settlement_status(
    settlement_id: int,
    payload: SettlementStatusUpdateRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> CostSettlement:
    settlement = db.scalar(select(CostSettlement).where(CostSettlement.SettlementID == settlement_id))
    if settlement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settlement not found")

    _authorized_booking(settlement.BookingID, current_member.MemberID, db)

    settlement.Payment_Status = payload.payment_status
    db.commit()
    db.refresh(settlement)
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
    db: Session = Depends(get_db_session),
) -> CostSettlement | None:
    _authorized_booking(booking_id, current_member.MemberID, db)
    return db.scalar(select(CostSettlement).where(CostSettlement.BookingID == booking_id))


@router.get("/my", response_model=list[SettlementReadResponse])
def my_settlements(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> list[CostSettlement]:
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
    return list(db.scalars(stmt))
