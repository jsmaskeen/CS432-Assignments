from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.session import get_db_session
from models.member import Member
from schemas.member import MemberCreate, MemberRead

router = APIRouter(tags=["testing"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/testing/db")
def database_ping(db: Session = Depends(get_db_session)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"database": "connected"}


@router.post("/testing/members", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def create_member(payload: MemberCreate, db: Session = Depends(get_db_session)) -> Member:
    member = Member(
        OAUTH_TOKEN=payload.oauth_token,
        Email=payload.email,
        Full_Name=payload.full_name.strip(),
        Phone_Number=payload.phone_number.strip() if payload.phone_number else None,
        Gender=payload.gender,
    )
    db.add(member)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member already exists or violates constraints") from exc

    db.refresh(member)
    return member


@router.get("/testing/members/{member_id}", response_model=MemberRead)
def get_member(member_id: int, db: Session = Depends(get_db_session)) -> Member:
    member = db.scalar(select(Member).where(Member.MemberID == member_id))
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return member


@router.get("/testing/members", response_model=list[MemberRead])
def list_members(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db_session)) -> list[Member]:
    return list(db.scalars(select(Member).order_by(Member.MemberID).limit(limit)))


@router.get("/testing/members-count")
def members_count(db: Session = Depends(get_db_session)) -> dict[str, int]:
    total = db.scalar(select(func.count(Member.MemberID)))
    return {"count": int(total or 0)}
