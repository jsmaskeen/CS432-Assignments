from collections.abc import Generator
from uuid import uuid4

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import settings
from core.request_context import get_request_context


class Base(DeclarativeBase):
    pass

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    ctx = get_request_context()
    request_id = ctx.request_id or str(uuid4())
    actor_member_id = ctx.actor_member_id
    actor_username = ctx.actor_username
    actor_role = ctx.actor_role

    if actor_member_id is not None and (actor_username is None or actor_role is None):
        from models.auth_credential import AuthCredential

        credential = db.scalar(select(AuthCredential).where(AuthCredential.MemberID == actor_member_id))
        if credential is not None:
            actor_username = credential.Username
            actor_role = credential.Role

    db.execute(
        text(
            """
            SET
                @app_request_id = :request_id,
                @app_actor_member_id = :actor_member_id,
                @app_actor_username = :actor_username,
                @app_actor_role = :actor_role,
                @app_source = 'api'
            """
        ),
        {
            "request_id": request_id,
            "actor_member_id": actor_member_id,
            "actor_username": actor_username,
            "actor_role": actor_role,
        },
    )

    try:
        yield db
    finally:
        try:
            db.execute(
                text(
                    """
                    SET
                        @app_request_id = NULL,
                        @app_actor_member_id = NULL,
                        @app_actor_username = NULL,
                        @app_actor_role = NULL,
                        @app_source = NULL
                    """
                )
            )
        except Exception:
            pass
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
                text(
                    """
                    SET
                        @app_request_id = :request_id,
                        @app_actor_member_id = NULL,
                        @app_actor_username = :actor_username,
                        @app_actor_role = :actor_role,
                        @app_source = 'api'
                    """
                ),
                {
                    "request_id": "bootstrap-admin-sync",
                    "actor_username": "system_bootstrap",
                    "actor_role": "system",
                },
            )
            conn.execute(
                text("UPDATE Auth_Credentials SET Role='admin' WHERE Username=:username"),
                {"username": bootstrap_username},
            )
            conn.execute(
                text(
                    """
                    SET
                        @app_request_id = NULL,
                        @app_actor_member_id = NULL,
                        @app_actor_username = NULL,
                        @app_actor_role = NULL,
                        @app_source = NULL
                    """
                )
            )
