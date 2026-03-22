from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class RideChatMessage(Base):
    __tablename__ = "Ride_Chat"

    MessageID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    RideID: Mapped[int] = mapped_column(ForeignKey("Rides.RideID", ondelete="CASCADE"), nullable=False)
    Sender_MemberID: Mapped[int] = mapped_column(ForeignKey("Members.MemberID", ondelete="CASCADE"), nullable=False)
    Message_Body: Mapped[str] = mapped_column(Text, nullable=False)
    Sent_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
