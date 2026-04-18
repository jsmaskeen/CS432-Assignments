from __future__ import annotations

import asyncio
import json
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from fastapi import WebSocketDisconnect
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from api.routes import chat as chat_route
from models.booking import Booking
from models.chat_message import RideChatMessage
from models.member import Member
from models.ride import Ride


def _make_sessionmaker() -> sessionmaker:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Member.__table__.create(bind=engine, checkfirst=True)
    Ride.__table__.create(bind=engine, checkfirst=True)
    Booking.__table__.create(bind=engine, checkfirst=True)
    RideChatMessage.__table__.create(bind=engine, checkfirst=True)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _insert_member(db, member_id: int, full_name: str) -> None:
    db.add(
        Member(
            MemberID=member_id,
            OAUTH_TOKEN=f"oauth_{member_id}",
            Email=f"member_{member_id}@iitgn.ac.in",
            Full_Name=full_name,
            Reputation_Score=Decimal("5.0"),
            Phone_Number=f"{member_id:010d}"[-10:],
            Gender="Other",
        )
    )


def _insert_ride(db, *, ride_id: int, host_member_id: int) -> None:
    db.add(
        Ride(
            RideID=ride_id,
            Host_MemberID=host_member_id,
            Start_GeoHash="u09tun",
            End_GeoHash="u09tvw",
            Departure_Time=datetime(2026, 1, 1, 10, 0, 0),
            Vehicle_Type="Sedan",
            Max_Capacity=4,
            Available_Seats=3,
            Base_Fare_Per_KM=Decimal("10.00"),
            Ride_Status="Open",
        )
    )


class _FakeWebSocket:
    def __init__(self, incoming_messages: list[str]) -> None:
        self.query_params = {"token": "valid-token"}
        self._incoming_messages = list(incoming_messages)
        self.sent_texts: list[str] = []
        self.closed_codes: list[int] = []

    async def receive_text(self) -> str:
        if self._incoming_messages:
            return self._incoming_messages.pop(0)
        raise WebSocketDisconnect(code=1000)

    async def send_text(self, payload: str) -> None:
        self.sent_texts.append(payload)

    async def close(self, code: int) -> None:
        self.closed_codes.append(code)


class _FakeConnectionManager:
    def __init__(self) -> None:
        self.connected: list[tuple[int, _FakeWebSocket]] = []
        self.disconnected: list[tuple[int, _FakeWebSocket]] = []
        self.broadcasts: list[tuple[int, dict[str, object]]] = []

    async def connect(self, ride_id: int, websocket: _FakeWebSocket) -> None:
        self.connected.append((ride_id, websocket))

    def disconnect(self, ride_id: int, websocket: _FakeWebSocket) -> None:
        self.disconnected.append((ride_id, websocket))

    async def broadcast(self, ride_id: int, payload: dict[str, object]) -> None:
        self.broadcasts.append((ride_id, payload))


def test_list_chat_messages_reads_from_shard_and_member_names_from_primary() -> None:
    primary_maker = _make_sessionmaker()
    shard_maker = _make_sessionmaker()

    with primary_maker() as primary_db:
        _insert_member(primary_db, 1, "Primary Host")
        primary_db.commit()

    with shard_maker() as shard_db:
        _insert_member(shard_db, 1, "Shard Host")
        _insert_ride(shard_db, ride_id=7, host_member_id=1)
        shard_db.flush()
        shard_db.add_all(
            [
                RideChatMessage(RideID=7, Sender_MemberID=1, Message_Body="message one"),
                RideChatMessage(RideID=7, Sender_MemberID=1, Message_Body="message two"),
            ]
        )
        shard_db.commit()

    with shard_maker() as shard_db, primary_maker() as primary_db:
        response = chat_route.list_chat_messages(
            ride_id=7,
            current_member=SimpleNamespace(MemberID=1),
            db=shard_db,
            primary_db=primary_db,
        )

    assert len(response) == 2
    assert {message["Message_Body"] for message in response} == {"message one", "message two"}
    assert {message["Sender_Name"] for message in response} == {"Primary Host"}


def test_ride_chat_ws_writes_message_to_resolved_shard(monkeypatch) -> None:
    primary_maker = _make_sessionmaker()
    shard_maker = _make_sessionmaker()

    with primary_maker() as primary_db:
        _insert_member(primary_db, 1, "Primary Sender")
        primary_db.commit()

    with shard_maker() as shard_db:
        _insert_member(shard_db, 1, "Shard Sender")
        _insert_ride(shard_db, ride_id=9, host_member_id=1)
        shard_db.commit()

    fake_manager = _FakeConnectionManager()
    fake_websocket = _FakeWebSocket([json.dumps({"message_body": "hello from shard"})])

    monkeypatch.setattr(chat_route, "SessionLocal", lambda: primary_maker())
    monkeypatch.setattr(chat_route, "SHARD_SESSION_MAKERS", {1: shard_maker})
    monkeypatch.setattr(chat_route, "get_ride_shard_id", lambda _ride_id, _db: 1)
    monkeypatch.setattr(chat_route, "decode_access_token", lambda _token: "1")
    monkeypatch.setattr(chat_route, "audit_event", lambda **_kwargs: None)
    monkeypatch.setattr(chat_route, "connection_manager", fake_manager)

    asyncio.run(chat_route.ride_chat_ws(websocket=fake_websocket, ride_id=9))

    assert len(fake_manager.connected) == 1
    assert len(fake_manager.broadcasts) == 1
    broadcast_ride_id, broadcast_payload = fake_manager.broadcasts[0]
    assert broadcast_ride_id == 9
    assert broadcast_payload["RideID"] == 9
    assert broadcast_payload["Sender_MemberID"] == 1
    assert broadcast_payload["Sender_Name"] == "Primary Sender"
    assert broadcast_payload["Message_Body"] == "hello from shard"
    assert fake_websocket.closed_codes == []

    with shard_maker() as shard_db:
        shard_message = shard_db.scalar(select(RideChatMessage).where(RideChatMessage.RideID == 9))
        assert shard_message is not None
        assert shard_message.Message_Body == "hello from shard"

    with primary_maker() as primary_db:
        primary_message = primary_db.scalar(select(RideChatMessage).where(RideChatMessage.RideID == 9))
        assert primary_message is None