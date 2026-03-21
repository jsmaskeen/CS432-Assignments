import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.dependencies import get_current_admin_credential
from core.audit import audit_event
from core.config import settings
from db.session import get_db_session
from models.auth_credential import AuthCredential
from models.member import Member
from schemas.admin import (
    AdminMemberReadResponse,
    AdminMemberRoleUpdateRequest,
    AuditLogReadResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger("rajak.admin")


@router.get("/members", response_model=list[AdminMemberReadResponse])
def list_members(
    _: AuthCredential = Depends(get_current_admin_credential),
    db: Session = Depends(get_db_session),
) -> list[AdminMemberReadResponse]:
    stmt = select(Member, AuthCredential).join(AuthCredential, AuthCredential.MemberID == Member.MemberID).order_by(Member.MemberID.asc())
    rows = db.execute(stmt).all()
    return [
        AdminMemberReadResponse(
            member_id=member.MemberID,
            username=credential.Username,
            role=credential.Role,
            email=member.Email,
            full_name=member.Full_Name,
            created_at=member.Created_At,
        )
        for member, credential in rows
    ]


@router.patch("/members/{member_id}/role", response_model=AdminMemberReadResponse)
def update_member_role(
    member_id: int,
    payload: AdminMemberRoleUpdateRequest,
    admin_credential: AuthCredential = Depends(get_current_admin_credential),
    db: Session = Depends(get_db_session),
) -> AdminMemberReadResponse:
    credential = db.scalar(select(AuthCredential).where(AuthCredential.MemberID == member_id))
    member = db.scalar(select(Member).where(Member.MemberID == member_id))
    if credential is None or member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if credential.MemberID == admin_credential.MemberID and payload.role != "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot demote your own admin account")

    credential.Role = payload.role
    db.commit()

    audit_event(
        action="admin.member.role_update",
        status="success",
        actor_member_id=admin_credential.MemberID,
        actor_username=admin_credential.Username,
        details={"target_member_id": member_id, "new_role": payload.role},
    )

    return AdminMemberReadResponse(
        member_id=member.MemberID,
        username=credential.Username,
        role=credential.Role,
        email=member.Email,
        full_name=member.Full_Name,
        created_at=member.Created_At,
    )


@router.get("/audit-logs", response_model=list[AuditLogReadResponse])
def read_audit_logs(
    limit: int = Query(default=200, ge=1, le=2000),
    admin_credential: AuthCredential = Depends(get_current_admin_credential),
) -> list[AuditLogReadResponse]:
    path = Path(settings.AUDIT_LOG_FILE)
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    selected = lines[-limit:]

    parsed: list[AuditLogReadResponse] = []
    for line in reversed(selected):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        parsed.append(
            AuditLogReadResponse(
                ts=str(obj.get("ts", "")),
                action=str(obj.get("action", "unknown")),
                status=str(obj.get("status", "unknown")),
                actor_member_id=obj.get("actor_member_id"),
                actor_username=obj.get("actor_username"),
                details=obj.get("details") if isinstance(obj.get("details"), dict) else {},
            )
        )

    audit_event(
        action="admin.audit.read",
        status="success",
        actor_member_id=admin_credential.MemberID,
        actor_username=admin_credential.Username,
        details={"limit": limit, "returned": len(parsed)},
    )
    return parsed
