import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.dependencies import get_current_member
from core.audit import audit_event
from db.session import get_db_session
from models.member import Member
from models.preference import UserPreference
from schemas.preference import PreferenceReadResponse, PreferenceUpsertRequest

router = APIRouter(prefix="/preferences", tags=["preferences"])
logger = logging.getLogger("rajak.preferences")


@router.get("/me", response_model=PreferenceReadResponse | None)
def my_preference(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> UserPreference | None:
    logger.info("preferences.me.get member_id=%s", current_member.MemberID)
    return db.scalar(select(UserPreference).where(UserPreference.MemberID == current_member.MemberID))


@router.put("/me", response_model=PreferenceReadResponse)
def upsert_preference(
    payload: PreferenceUpsertRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> UserPreference:
    logger.info("preferences.me.upsert member_id=%s", current_member.MemberID)
    pref = db.scalar(select(UserPreference).where(UserPreference.MemberID == current_member.MemberID))
    if pref is None:
        pref = UserPreference(
            MemberID=current_member.MemberID,
            Gender_Preference=payload.gender_preference,
            Notify_On_New_Ride=payload.notify_on_new_ride,
            Music_Preference=payload.music_preference,
        )
        db.add(pref)
    else:
        pref.Gender_Preference = payload.gender_preference
        pref.Notify_On_New_Ride = payload.notify_on_new_ride
        pref.Music_Preference = payload.music_preference

    db.commit()
    db.refresh(pref)
    audit_event(
        action="preferences.upsert",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"preference_id": pref.PreferenceID},
    )
    return pref
