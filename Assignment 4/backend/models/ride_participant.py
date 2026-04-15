from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class RideParticipant(Base):
    __tablename__ = "Ride_Participants"
    __table_args__ = (
        UniqueConstraint("RideID", "MemberID", name="ride_participants_ride_member_unique"),
    )

    ParticipantID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    RideID: Mapped[int] = mapped_column(ForeignKey("Rides.RideID", ondelete="CASCADE"), nullable=False)
    MemberID: Mapped[int] = mapped_column(ForeignKey("Members.MemberID", ondelete="CASCADE"), nullable=False)
    Role: Mapped[str] = mapped_column(
        SQLEnum("Host", "Passenger", name="ride_participant_role"),
        nullable=False,
    )
    Joined_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
