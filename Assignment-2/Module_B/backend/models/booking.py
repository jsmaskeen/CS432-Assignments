from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum as SQLEnum, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class Booking(Base):
    __tablename__ = "Bookings"
    __table_args__ = (
        UniqueConstraint("RideID", "Passenger_MemberID", name="bookings_ride_passenger_unique"),
        CheckConstraint("Distance_Travelled_KM > 0", name="Bookings_chk_1"),
    )

    BookingID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    RideID: Mapped[int] = mapped_column(ForeignKey("Rides.RideID", ondelete="CASCADE"), nullable=False)
    Passenger_MemberID: Mapped[int] = mapped_column(ForeignKey("Members.MemberID", ondelete="CASCADE"), nullable=False)
    Booking_Status: Mapped[str] = mapped_column(
        SQLEnum("Pending", "Confirmed", "Rejected", "Cancelled", name="booking_status"),
        nullable=False,
        default="Pending",
    )
    Pickup_GeoHash: Mapped[str] = mapped_column(String(20), nullable=False)
    Drop_GeoHash: Mapped[str] = mapped_column(String(20), nullable=False)
    Distance_Travelled_KM: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    Booked_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
