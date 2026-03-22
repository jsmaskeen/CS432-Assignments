import json
import logging

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from api.dependencies import get_current_member
from core.audit import audit_event
from core.security import decode_access_token
from db.session import get_db_session
from db.session import SessionLocal
from models.booking import Booking
from models.chat_message import RideChatMessage
from models.member import Member
from models.ride import Ride
from schemas.chat import ChatReadResponse

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("rajak.chat")


class _ChatConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}

    async def connect(self, ride_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(ride_id, set()).add(websocket)

    def disconnect(self, ride_id: int, websocket: WebSocket) -> None:
        connections = self._connections.get(ride_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(ride_id, None)

    async def broadcast(self, ride_id: int, payload: dict[str, object]) -> None:
        connections = list(self._connections.get(ride_id, set()))
        if not connections:
            return
        message = json.dumps(payload, ensure_ascii=True)
        for connection in connections:
            await connection.send_text(message)


connection_manager = _ChatConnectionManager()


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
) -> list[dict[str, object]]:
    _ensure_chat_member(ride_id, current_member.MemberID, db)
    stmt = select(RideChatMessage).where(RideChatMessage.RideID == ride_id).order_by(RideChatMessage.Sent_At.asc())
    messages = list(db.scalars(stmt))
    member_ids = {message.Sender_MemberID for message in messages}
    members = {
        member.MemberID: member
        for member in db.scalars(select(Member).where(Member.MemberID.in_(member_ids)))
    }
    response = []
    for message in messages:
        member = members.get(message.Sender_MemberID)
        response.append(
            {
                "MessageID": message.MessageID,
                "RideID": message.RideID,
                "Sender_MemberID": message.Sender_MemberID,
                "Sender_Name": member.Full_Name if member else None,
                "Message_Body": message.Message_Body,
                "Sent_At": message.Sent_At,
            }
        )
    return response


@router.websocket("/ws/ride/{ride_id}")
async def ride_chat_ws(websocket: WebSocket, ride_id: int) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    subject = decode_access_token(token)
    if subject is None or not subject.isdigit():
        await websocket.close(code=1008)
        return

    member_id = int(subject)
    db = SessionLocal()
    try:
        member = db.scalar(select(Member).where(Member.MemberID == member_id))
        sender_name = member.Full_Name if member else None
        _ensure_chat_member(ride_id, member_id, db)
        await connection_manager.connect(ride_id, websocket)
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"message_body": raw}

            message_body = str(payload.get("message_body", "")).strip()
            if not message_body:
                await websocket.send_text(json.dumps({"error": "message_body is required"}, ensure_ascii=True))
                continue

            if len(message_body) > 2000:
                await websocket.send_text(json.dumps({"error": "message_body is too long"}, ensure_ascii=True))
                continue

            message = RideChatMessage(
                RideID=ride_id,
                Sender_MemberID=member_id,
                Message_Body=message_body,
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            audit_event(
                action="chat.create",
                status="success",
                actor_member_id=member_id,
                actor_username=None,
                details={"ride_id": ride_id, "message_id": message.MessageID},
            )

            await connection_manager.broadcast(
                ride_id,
                {
                    "MessageID": message.MessageID,
                    "RideID": message.RideID,
                    "Sender_MemberID": message.Sender_MemberID,
                    "Sender_Name": sender_name,
                    "Message_Body": message.Message_Body,
                    "Sent_At": message.Sent_At.isoformat(),
                },
            )
    except WebSocketDisconnect:
        connection_manager.disconnect(ride_id, websocket)
    except HTTPException:
        await websocket.close(code=1008)
    finally:
        connection_manager.disconnect(ride_id, websocket)
        db.close()
