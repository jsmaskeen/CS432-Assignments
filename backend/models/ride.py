from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum as SQLEnum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class Ride(Base):
    __tablename__ = "Rides"
    __table_args__ = (
        CheckConstraint("Max_Capacity > 0", name="Rides_chk_1"),
        CheckConstraint("Available_Seats >= 0", name="Rides_chk_2"),
        CheckConstraint("Available_Seats <= Max_Capacity", name="Rides_chk_3"),
        CheckConstraint("Start_GeoHash <> End_GeoHash", name="Rides_chk_4"),
    )

    RideID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    Host_MemberID: Mapped[int] = mapped_column(ForeignKey("Members.MemberID"), nullable=False)
    Start_GeoHash: Mapped[str] = mapped_column(String(20), nullable=False)
    End_GeoHash: Mapped[str] = mapped_column(String(20), nullable=False)
    Departure_Time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    Vehicle_Type: Mapped[str] = mapped_column(String(50), nullable=False)
    Max_Capacity: Mapped[int] = mapped_column(nullable=False)
    Available_Seats: Mapped[int] = mapped_column(nullable=False)
    Base_Fare_Per_KM: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    Ride_Status: Mapped[str] = mapped_column(
        SQLEnum("Open", "Full", "Cancelled", "Completed", name="ride_status"),
        nullable=False,
        default="Open",
    )
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
