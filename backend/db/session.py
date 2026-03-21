from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import settings


class Base(DeclarativeBase):
    pass

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_auth_tables() -> None:
    from models.auth_credential import AuthCredential
    from models.chat_message import RideChatMessage
    from models.location import Location
    from models.preference import UserPreference
    from models.review import ReputationReview
    from models.ride_participant import RideParticipant
    from models.saved_address import SavedAddress
    from models.settlement import CostSettlement

    AuthCredential.__table__.create(bind=engine, checkfirst=True)
    Location.__table__.create(bind=engine, checkfirst=True)
    SavedAddress.__table__.create(bind=engine, checkfirst=True)
    UserPreference.__table__.create(bind=engine, checkfirst=True)
    ReputationReview.__table__.create(bind=engine, checkfirst=True)
    CostSettlement.__table__.create(bind=engine, checkfirst=True)
    RideChatMessage.__table__.create(bind=engine, checkfirst=True)
    RideParticipant.__table__.create(bind=engine, checkfirst=True)

    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("Auth_Credentials")}
    if "Role" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE Auth_Credentials ADD COLUMN Role VARCHAR(20) NOT NULL DEFAULT 'user'"))

    bootstrap_username = settings.ADMIN_BOOTSTRAP_USERNAME.strip()
    if bootstrap_username:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE Auth_Credentials SET Role='admin' WHERE Username=:username"),
                {"username": bootstrap_username},
            )
