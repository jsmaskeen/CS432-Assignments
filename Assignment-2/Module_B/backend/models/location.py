from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class Location(Base):
    __tablename__ = "Locations"

    LocationID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    Location_Name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    Location_Type: Mapped[str] = mapped_column(String(20), nullable=False)
    GeoHash: Mapped[str | None] = mapped_column(String(20), nullable=True)
