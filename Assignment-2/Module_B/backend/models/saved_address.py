from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class SavedAddress(Base):
    __tablename__ = "Saved_Addresses"
    __table_args__ = (
        UniqueConstraint("MemberID", "Label", name="saved_addresses_member_label_unique"),
    )

    AddressID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    MemberID: Mapped[int] = mapped_column(ForeignKey("Members.MemberID", ondelete="CASCADE"), nullable=False)
    Label: Mapped[str] = mapped_column(String(50), nullable=False)
    LocationID: Mapped[int] = mapped_column(ForeignKey("Locations.LocationID", ondelete="CASCADE"), nullable=False)
