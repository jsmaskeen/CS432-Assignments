from __future__ import annotations

from sqlalchemy import Boolean, Enum as SQLEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class UserPreference(Base):
    __tablename__ = "User_Preferences"

    PreferenceID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    MemberID: Mapped[int] = mapped_column(ForeignKey("Members.MemberID", ondelete="CASCADE"), nullable=False, unique=True)
    Gender_Preference: Mapped[str] = mapped_column(
        SQLEnum("Any", "Same-Gender Only", name="gender_preference"),
        nullable=False,
        default="Any",
    )
    Notify_On_New_Ride: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    Music_Preference: Mapped[str | None] = mapped_column(String(100), nullable=True)
