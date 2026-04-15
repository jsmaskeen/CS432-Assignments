from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class RideShardDirectory(Base):
    __tablename__ = "Ride_Shard_Directory"
    __table_args__ = (
        CheckConstraint("ShardID in (0,1,2)", name="Ride_Shard_Directory_chk_1"),
    )

    RideID: Mapped[int] = mapped_column(primary_key=True)
    ShardID: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    Strategy: Mapped[str] = mapped_column(String(50), nullable=False, default="ride_id_mod_3")
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
