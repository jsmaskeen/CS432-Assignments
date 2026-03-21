import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from api.dependencies import get_current_member
from core.audit import audit_event
from db.session import get_db_session
from models.booking import Booking
from models.chat_message import RideChatMessage
from models.member import Member
from models.ride import Ride
from schemas.chat import ChatCreateRequest, ChatReadResponse

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("rajak.chat")


def _ensure_chat_member(ride_id: int, member_id: int, db: Session) -> Ride:
    ride = db.scalar(select(Ride).where(Ride.RideID == ride_id))
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")

    if ride.Host_MemberID == member_id:
        return ride

    confirmed = db.scalar(
        select(Booking.BookingID).where(
            and_(
                Booking.RideID == ride_id,
                Booking.Passenger_MemberID == member_id,
                Booking.Booking_Status == "Confirmed",
            )
        )
    )
    if confirmed is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only host and confirmed passengers can access ride chat")
    return ride


@router.get("/ride/{ride_id}", response_model=list[ChatReadResponse])
def list_chat_messages(
    ride_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> list[RideChatMessage]:
    _ensure_chat_member(ride_id, current_member.MemberID, db)
    stmt = select(RideChatMessage).where(RideChatMessage.RideID == ride_id).order_by(RideChatMessage.Sent_At.asc())
    return list(db.scalars(stmt))


@router.post("/ride/{ride_id}", response_model=ChatReadResponse, status_code=status.HTTP_201_CREATED)
def create_chat_message(
    ride_id: int,
    payload: ChatCreateRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> RideChatMessage:
    _ensure_chat_member(ride_id, current_member.MemberID, db)
    message = RideChatMessage(
        RideID=ride_id,
        Sender_MemberID=current_member.MemberID,
        Message_Body=payload.message_body.strip(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    audit_event(
        action="chat.create",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"ride_id": ride_id, "message_id": message.MessageID},
    )
    return message
