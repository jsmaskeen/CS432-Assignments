import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.dependencies import get_current_member
from core.audit import audit_event
from db.session import get_db_session
from db.sharding import SHARD_SESSION_MAKERS
from models.member import Member
from models.preference import UserPreference
from schemas.preference import PreferenceReadResponse, PreferenceUpsertRequest

router = APIRouter(prefix="/preferences", tags=["preferences"])
logger = logging.getLogger("rajak.preferences")


def _member_shard_ids(member_id: int) -> list[int]:
    shard_ids: list[int] = []
    for shard_id in sorted(SHARD_SESSION_MAKERS.keys()):
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            exists = shard_db.scalar(select(Member.MemberID).where(Member.MemberID == member_id))
            if exists is not None:
                shard_ids.append(shard_id)
        finally:
            shard_db.close()
    return shard_ids


@router.get("/me", response_model=PreferenceReadResponse | None)
def my_preference(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> UserPreference | None:
    logger.info("preferences.me.get member_id=%s", current_member.MemberID)
    for shard_id in _member_shard_ids(current_member.MemberID):
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            pref = shard_db.scalar(select(UserPreference).where(UserPreference.MemberID == current_member.MemberID))
            if pref is not None:
                return pref
        finally:
            shard_db.close()

    # Fallback keeps legacy users functional before they are replicated to shards.
    return db.scalar(select(UserPreference).where(UserPreference.MemberID == current_member.MemberID))


@router.put("/me", response_model=PreferenceReadResponse)
def upsert_preference(
    payload: PreferenceUpsertRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> UserPreference:
    logger.info("preferences.me.upsert member_id=%s", current_member.MemberID)
    shard_ids = _member_shard_ids(current_member.MemberID)

    pref_to_return: UserPreference | None = None
    if shard_ids:
        for shard_id in shard_ids:
            shard_db = SHARD_SESSION_MAKERS[shard_id]()
            try:
                pref = shard_db.scalar(select(UserPreference).where(UserPreference.MemberID == current_member.MemberID))
                if pref is None:
                    pref = UserPreference(
                        MemberID=current_member.MemberID,
                        Gender_Preference=payload.gender_preference,
                        Notify_On_New_Ride=payload.notify_on_new_ride,
                        Music_Preference=payload.music_preference,
                    )
                    shard_db.add(pref)
                else:
                    pref.Gender_Preference = payload.gender_preference
                    pref.Notify_On_New_Ride = payload.notify_on_new_ride
                    pref.Music_Preference = payload.music_preference

                shard_db.commit()
                shard_db.refresh(pref)
                if pref_to_return is None:
                    pref_to_return = pref
            finally:
                shard_db.close()
    else:
        # Fallback for members that are not mirrored to any shard yet.
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
        pref_to_return = pref

    assert pref_to_return is not None
    audit_event(
        action="preferences.upsert",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"preference_id": pref_to_return.PreferenceID, "shard_ids": shard_ids},
    )
    return pref_to_return
