import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import MetaData, Table, delete, insert, inspect, select, update
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


def _get_table(table_name: str, db: Session) -> Table:
    inspector = inspect(db.bind)
    table_names = inspector.get_table_names()
    if table_name not in table_names:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
    return Table(table_name, MetaData(), autoload_with=db.bind)


def _get_single_pk_column(table: Table) -> str:
    pk_columns = [col.name for col in table.primary_key.columns]
    if len(pk_columns) != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Table must have a single primary key")
    return pk_columns[0]


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


@router.get("/tables")
def list_tables(
    _: AuthCredential = Depends(get_current_admin_credential),
    db: Session = Depends(get_db_session),
) -> list[str]:
    inspector = inspect(db.bind)
    return sorted(inspector.get_table_names())


@router.get("/tables/{table_name}")
def read_table(
    table_name: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _: AuthCredential = Depends(get_current_admin_credential),
    db: Session = Depends(get_db_session),
) -> list[dict[str, Any]]:
    table = _get_table(table_name, db)
    stmt = select(table).limit(limit).offset(offset)
    return list(db.execute(stmt).mappings().all())


@router.post("/tables/{table_name}")
def insert_row(
    table_name: str,
    payload: dict[str, Any] = Body(...),
    admin_credential: AuthCredential = Depends(get_current_admin_credential),
    db: Session = Depends(get_db_session),
) -> dict[str, Any]:
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload is required")
    table = _get_table(table_name, db)
    stmt = insert(table).values(**payload)
    result = db.execute(stmt)
    db.commit()
    audit_event(
        action="admin.table.insert",
        status="success",
        actor_member_id=admin_credential.MemberID,
        actor_username=admin_credential.Username,
        details={"table": table_name, "rowcount": result.rowcount},
    )
    return {"inserted": result.rowcount, "id": result.lastrowid}


@router.patch("/tables/{table_name}/{pk}")
def update_row(
    table_name: str,
    pk: str,
    payload: dict[str, Any] = Body(...),
    admin_credential: AuthCredential = Depends(get_current_admin_credential),
    db: Session = Depends(get_db_session),
) -> dict[str, Any]:
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload is required")
    table = _get_table(table_name, db)
    pk_column_name = _get_single_pk_column(table)
    if pk_column_name in payload:
        payload = {key: value for key, value in payload.items() if key != pk_column_name}
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No updatable fields provided")

    pk_column = table.c[pk_column_name]
    stmt = update(table).where(pk_column == pk).values(**payload)
    result = db.execute(stmt)
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Row not found")

    db.commit()
    audit_event(
        action="admin.table.update",
        status="success",
        actor_member_id=admin_credential.MemberID,
        actor_username=admin_credential.Username,
        details={"table": table_name, "rowcount": result.rowcount},
    )
    return {"updated": result.rowcount}


@router.delete("/tables/{table_name}/{pk}")
def delete_row(
    table_name: str,
    pk: str,
    admin_credential: AuthCredential = Depends(get_current_admin_credential),
    db: Session = Depends(get_db_session),
) -> dict[str, Any]:
    table = _get_table(table_name, db)
    pk_column_name = _get_single_pk_column(table)
    pk_column = table.c[pk_column_name]
    stmt = delete(table).where(pk_column == pk)
    result = db.execute(stmt)
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Row not found")

    db.commit()
    audit_event(
        action="admin.table.delete",
        status="success",
        actor_member_id=admin_credential.MemberID,
        actor_username=admin_credential.Username,
        details={"table": table_name, "rowcount": result.rowcount},
    )
    return {"deleted": result.rowcount}
