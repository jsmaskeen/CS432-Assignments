from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.dependencies import get_current_admin_credential
from core.chaos import enable_failures, reset_failures, snapshot_failures
from db.session import get_db_session
from models.auth_credential import AuthCredential

router = APIRouter(tags=["testing"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/testing/db")
def database_ping(db: Session = Depends(get_db_session)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"database": "connected"}


@router.get("/testing/chaos")
def chaos_status(_: AuthCredential = Depends(get_current_admin_credential)) -> dict[str, dict[str, int]]:
    return {"hooks": snapshot_failures()}


@router.post("/testing/chaos/enable")
def chaos_enable(
    payload: dict,
    _: AuthCredential = Depends(get_current_admin_credential),
) -> dict[str, object]:
    hook = str(payload.get("hook", "")).strip().lower()
    fail_count_raw = payload.get("fail_count", 1)
    try:
        fail_count = int(fail_count_raw)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="fail_count must be an integer") from exc

    try:
        remaining = enable_failures(hook, fail_count)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"hook": hook, "remaining": remaining}


@router.post("/testing/chaos/reset")
def chaos_reset(_: AuthCredential = Depends(get_current_admin_credential)) -> dict[str, str]:
    reset_failures()
    return {"status": "reset"}
