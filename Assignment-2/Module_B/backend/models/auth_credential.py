from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class AuthCredential(Base):
    __tablename__ = "Auth_Credentials"

    CredentialID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    MemberID: Mapped[int] = mapped_column(ForeignKey("Members.MemberID", ondelete="CASCADE"), unique=True, nullable=False)
    Username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    Password_Hash: Mapped[str] = mapped_column(String(255), nullable=False)
    Role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    Created_At: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
