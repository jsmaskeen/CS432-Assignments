import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.dependencies import get_current_admin_credential, get_current_member
from core.audit import audit_event
from core.config import settings
from core.security import create_access_token, hash_password, verify_password
from db.session import get_db_session
from models.auth_credential import AuthCredential
from models.member import Member
from schemas.auth import AuthTokenResponse, CurrentUserResponse, LoginRequest, PromoteAdminRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("rajak.auth")


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db_session)) -> AuthTokenResponse:
    logger.info("register.attempt username=%s email=%s", payload.username, payload.email)
    existing_username = db.scalar(select(AuthCredential).where(AuthCredential.Username == payload.username))
    if existing_username is not None:
        logger.warning("register.username_conflict username=%s", payload.username)
        audit_event(action="auth.register", status="failed", actor_member_id=None, actor_username=payload.username, details={"reason": "username_conflict"})
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    existing_email = db.scalar(select(Member).where(Member.Email == payload.email))
    if existing_email is not None:
        logger.warning("register.email_conflict email=%s", payload.email)
        audit_event(action="auth.register", status="failed", actor_member_id=None, actor_username=payload.username, details={"reason": "email_conflict"})
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    member = Member(
        OAUTH_TOKEN=f"local_{payload.username}",
        Email=str(payload.email),
        Full_Name=payload.full_name.strip(),
        Phone_Number=payload.phone_number.strip() if payload.phone_number else None,
        Gender=payload.gender,
    )
    db.add(member)
    db.flush()

    assigned_role = "admin" if settings.ADMIN_BOOTSTRAP_USERNAME and payload.username == settings.ADMIN_BOOTSTRAP_USERNAME else "user"

    credential = AuthCredential(
        MemberID=member.MemberID,
        Username=payload.username,
        Password_Hash=hash_password(payload.password),
        Role=assigned_role,
    )
    db.add(credential)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.exception("register.db_conflict username=%s", payload.username)
        audit_event(action="auth.register", status="failed", actor_member_id=None, actor_username=payload.username, details={"reason": "db_conflict"})
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User registration conflict") from exc

    access_token = create_access_token(str(member.MemberID))
    logger.info("register.success member_id=%s username=%s", member.MemberID, payload.username)
    audit_event(
        action="auth.register",
        status="success",
        actor_member_id=member.MemberID,
        actor_username=payload.username,
        details={"role": assigned_role},
    )
    return AuthTokenResponse(access_token=access_token)


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db_session)) -> AuthTokenResponse:
    logger.info("login.attempt username=%s", payload.username)
    credential = db.scalar(select(AuthCredential).where(AuthCredential.Username == payload.username))
    if credential is None or not verify_password(payload.password, credential.Password_Hash):
        logger.warning("login.failed username=%s", payload.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(str(credential.MemberID))
    logger.info("login.success member_id=%s username=%s", credential.MemberID, payload.username)
    return AuthTokenResponse(access_token=token)


@router.get("/me", response_model=CurrentUserResponse)
def me(current_member: Member = Depends(get_current_member), db: Session = Depends(get_db_session)) -> CurrentUserResponse:
    credential = db.scalar(select(AuthCredential).where(AuthCredential.MemberID == current_member.MemberID))
    if credential is None:
        logger.warning("me.credential_missing member_id=%s", current_member.MemberID)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")

    logger.info("me.success member_id=%s", current_member.MemberID)
    return CurrentUserResponse(
        member_id=current_member.MemberID,
        username=credential.Username,
        role=credential.Role,
        email=current_member.Email,
        full_name=current_member.Full_Name,
    )


@router.post("/admin/promote")
def promote_to_admin(
    payload: PromoteAdminRequest,
    admin_credential: AuthCredential = Depends(get_current_admin_credential),
    db: Session = Depends(get_db_session),
) -> dict[str, str]:
    target = db.scalar(select(AuthCredential).where(AuthCredential.Username == payload.username))
    if target is None:
        audit_event(
            action="auth.promote_admin",
            status="failed",
            actor_member_id=admin_credential.MemberID,
            actor_username=admin_credential.Username,
            details={"reason": "target_not_found", "target_username": payload.username},
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    target.Role = "admin"
    db.commit()
    audit_event(
        action="auth.promote_admin",
        status="success",
        actor_member_id=admin_credential.MemberID,
        actor_username=admin_credential.Username,
        details={"target_username": payload.username},
    )
    return {"message": f"{payload.username} promoted to admin"}
