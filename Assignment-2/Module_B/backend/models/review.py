from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class ReputationReview(Base):
    __tablename__ = "Reputation_Reviews"
    __table_args__ = (
        UniqueConstraint("RideID", "Reviewer_MemberID", "Reviewee_MemberID", name="reviews_ride_reviewer_reviewee_unique"),
        CheckConstraint("Rating >= 1 AND Rating <= 5", name="Reputation_Reviews_chk_1"),
        CheckConstraint("Reviewer_MemberID <> Reviewee_MemberID", name="Reputation_Reviews_chk_2"),
    )

    ReviewID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    RideID: Mapped[int] = mapped_column(ForeignKey("Rides.RideID", ondelete="CASCADE"), nullable=False)
    Reviewer_MemberID: Mapped[int] = mapped_column(ForeignKey("Members.MemberID", ondelete="CASCADE"), nullable=False)
    Reviewee_MemberID: Mapped[int] = mapped_column(ForeignKey("Members.MemberID", ondelete="CASCADE"), nullable=False)
    Rating: Mapped[int] = mapped_column(Integer, nullable=False)
    Comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
