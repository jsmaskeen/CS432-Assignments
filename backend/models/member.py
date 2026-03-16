from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, Enum as SQLEnum, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class MemberGender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class Member(Base):
    __tablename__ = "Members"
    __table_args__ = (
        CheckConstraint("Email like '%@iitgn.ac.in'", name="Members_chk_1"),
        CheckConstraint("Reputation_Score between 0.0 and 5.0", name="Members_chk_2"),
    )

    MemberID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    OAUTH_TOKEN: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    Email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    Full_Name: Mapped[str] = mapped_column(String(100), nullable=False)
    Reputation_Score: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False, default=Decimal("0.0"))
    Phone_Number: Mapped[str | None] = mapped_column(String(15), nullable=True)
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    Gender: Mapped[str] = mapped_column(
        SQLEnum(MemberGender.MALE.value, MemberGender.FEMALE.value, MemberGender.OTHER.value, name="member_gender"),
        nullable=False,
    )
