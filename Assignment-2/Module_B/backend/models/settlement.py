from __future__ import annotations

from decimal import Decimal

from sqlalchemy import CheckConstraint, Enum as SQLEnum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class CostSettlement(Base):
    __tablename__ = "Cost_Settlements"
    __table_args__ = (CheckConstraint("Calculated_Cost >= 0", name="Cost_Settlements_chk_1"),)

    SettlementID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    BookingID: Mapped[int] = mapped_column(ForeignKey("Bookings.BookingID", ondelete="CASCADE"), nullable=False, unique=True)
    Calculated_Cost: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    Payment_Status: Mapped[str] = mapped_column(
        SQLEnum("Unpaid", "Settled", name="payment_status"),
        nullable=False,
        default="Unpaid",
    )
