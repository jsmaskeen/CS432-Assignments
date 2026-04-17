import logging
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.dependencies import get_current_member
from core.audit import audit_event
from core.sharding import delete_review_shard_id, get_review_shard_id, get_ride_shard_id, upsert_review_shard_id
from db.session import get_db_session
from db.sharding import SHARD_SESSION_MAKERS
from models.booking import Booking
from models.member import Member
from models.review import ReputationReview
from models.ride import Ride
from schemas.review import ReviewCreateRequest, ReviewParticipantResponse, ReviewReadResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])
logger = logging.getLogger("rajak.reviews")


def _resolve_review_shard_id(review_id: int, primary_db: Session) -> int | None:
    mapped_shard_id = get_review_shard_id(review_id, primary_db)
    if mapped_shard_id is not None:
        return mapped_shard_id

    # Legacy fallback: if an older review does not yet have a directory row, discover and backfill it.
    for shard_id in sorted(SHARD_SESSION_MAKERS.keys()):
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            found = shard_db.scalar(select(ReputationReview.ReviewID).where(ReputationReview.ReviewID == review_id))
            if found is not None:
                try:
                    upsert_review_shard_id(review_id, shard_id, primary_db)
                    primary_db.commit()
                except Exception:
                    primary_db.rollback()
                    logger.exception("reviews.directory.backfill_failed review_id=%s shard_id=%s", review_id, shard_id)
                return shard_id
        finally:
            shard_db.close()

    return None


def _compute_reputation_score_across_shards(member_id: int) -> Decimal:
    total_reviews = 0
    total_rating = Decimal("0")

    for shard_id in sorted(SHARD_SESSION_MAKERS.keys()):
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            rating_sum, review_count = shard_db.execute(
                select(
                    func.coalesce(func.sum(ReputationReview.Rating), 0),
                    func.count(ReputationReview.ReviewID),
                ).where(ReputationReview.Reviewee_MemberID == member_id)
            ).one()

            if isinstance(rating_sum, Decimal):
                total_rating += rating_sum
            else:
                total_rating += Decimal(str(rating_sum or 0))
            total_reviews += int(review_count or 0)
        finally:
            shard_db.close()

    if total_reviews == 0:
        return Decimal("5.0")

    return (total_rating / Decimal(total_reviews)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _sync_reputation_score(member_id: int, primary_db: Session) -> None:
    score = _compute_reputation_score_across_shards(member_id)

    primary_member = primary_db.scalar(select(Member).where(Member.MemberID == member_id))
    if primary_member is not None:
        primary_member.Reputation_Score = score
        primary_db.commit()

    for shard_id in sorted(SHARD_SESSION_MAKERS.keys()):
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            shard_member = shard_db.scalar(select(Member).where(Member.MemberID == member_id))
            if shard_member is not None:
                shard_member.Reputation_Score = score
                shard_db.commit()
        finally:
            shard_db.close()


def _member_map(member_ids: set[int], primary_db: Session) -> dict[int, Member]:
    if not member_ids:
        return {}

    return {
        member.MemberID: member
        for member in primary_db.scalars(select(Member).where(Member.MemberID.in_(member_ids)))
    }


def _to_review_response(reviews: list[ReputationReview], members: dict[int, Member]) -> list[dict[str, object]]:
    response = []
    for review in reviews:
        reviewer = members.get(review.Reviewer_MemberID)
        reviewee = members.get(review.Reviewee_MemberID)
        response.append(
            {
                "ReviewID": review.ReviewID,
                "RideID": review.RideID,
                "Reviewer_MemberID": review.Reviewer_MemberID,
                "Reviewer_Name": reviewer.Full_Name if reviewer else None,
                "Reviewee_MemberID": review.Reviewee_MemberID,
                "Reviewee_Name": reviewee.Full_Name if reviewee else None,
                "Rating": review.Rating,
                "Comments": review.Comments,
                "Created_At": review.Created_At,
            }
        )
    return response


def _reviews_for_member_across_shards(member_id: int, *, include_as_reviewee: bool) -> list[ReputationReview]:
    reviews: list[ReputationReview] = []

    for shard_id in sorted(SHARD_SESSION_MAKERS.keys()):
        shard_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            stmt = select(ReputationReview)
            if include_as_reviewee:
                stmt = stmt.where(
                    or_(
                        ReputationReview.Reviewer_MemberID == member_id,
                        ReputationReview.Reviewee_MemberID == member_id,
                    )
                )
            else:
                stmt = stmt.where(ReputationReview.Reviewer_MemberID == member_id)

            stmt = stmt.order_by(ReputationReview.Created_At.desc(), ReputationReview.ReviewID.desc())
            reviews.extend(list(shard_db.scalars(stmt)))
        finally:
            shard_db.close()

    reviews.sort(key=lambda review: (review.Created_At, review.ReviewID), reverse=True)
    return reviews


def _ride_participant_member_ids(ride_id: int, db: Session) -> set[int]:
    ride = db.scalar(select(Ride).where(Ride.RideID == ride_id))
    if ride is None:
        return set()

    participants = {ride.Host_MemberID}
    confirmed_passengers = db.scalars(
        select(Booking.Passenger_MemberID).where(
            and_(
                Booking.RideID == ride_id,
                Booking.Booking_Status == "Confirmed",
            )
        )
    )
    participants.update(confirmed_passengers)
    return participants


@router.post("", response_model=ReviewReadResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreateRequest,
    current_member: Member = Depends(get_current_member),
    primary_db: Session = Depends(get_db_session),
) -> ReputationReview:
    shard_id = get_ride_shard_id(payload.ride_id, primary_db)
    review: ReputationReview | None = None
    shard_db = SHARD_SESSION_MAKERS[shard_id]()
    try:
        ride = shard_db.scalar(select(Ride).where(Ride.RideID == payload.ride_id))
        if ride is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
        if ride.Ride_Status != "Completed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reviews are allowed only for completed rides")

        participants = _ride_participant_member_ids(payload.ride_id, shard_db)
        if current_member.MemberID not in participants:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only ride participants can review")
        if payload.reviewee_member_id not in participants:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reviewee is not a participant of this ride")
        if payload.reviewee_member_id == current_member.MemberID:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot review yourself")

        review = ReputationReview(
            RideID=payload.ride_id,
            Reviewer_MemberID=current_member.MemberID,
            Reviewee_MemberID=payload.reviewee_member_id,
            Rating=payload.rating,
            Comments=payload.comments,
        )
        shard_db.add(review)
        try:
            shard_db.commit()
        except IntegrityError as exc:
            shard_db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Review already exists for this reviewer-reviewee pair") from exc

        shard_db.refresh(review)
    finally:
        shard_db.close()

    assert review is not None
    try:
        upsert_review_shard_id(review.ReviewID, shard_id, primary_db)
        primary_db.commit()
    except Exception as exc:
        primary_db.rollback()
        logger.exception("reviews.directory.write_failed review_id=%s shard_id=%s", review.ReviewID, shard_id)

        cleanup_db = SHARD_SESSION_MAKERS[shard_id]()
        try:
            persisted_review = cleanup_db.scalar(select(ReputationReview).where(ReputationReview.ReviewID == review.ReviewID))
            if persisted_review is not None:
                cleanup_db.delete(persisted_review)
                cleanup_db.commit()
        except Exception:
            cleanup_db.rollback()
            logger.exception("reviews.directory.compensation_failed review_id=%s shard_id=%s", review.ReviewID, shard_id)
        finally:
            cleanup_db.close()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Review creation failed to persist shard mapping",
        ) from exc

    try:
        _sync_reputation_score(payload.reviewee_member_id, primary_db)
    except Exception:
        logger.exception("reviews.reputation_score_sync_failed reviewee_member_id=%s", payload.reviewee_member_id)

    audit_event(
        action="reviews.create",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"review_id": review.ReviewID, "ride_id": payload.ride_id, "shard_id": shard_id},
    )
    return review


@router.get("/ride/{ride_id}", response_model=list[ReviewReadResponse])
def list_ride_reviews(
    ride_id: int,
    _: Member = Depends(get_current_member),
    primary_db: Session = Depends(get_db_session),
) -> list[dict[str, object]]:
    shard_id = get_ride_shard_id(ride_id, primary_db)
    shard_db = SHARD_SESSION_MAKERS[shard_id]()
    try:
        stmt = (
            select(ReputationReview)
            .where(ReputationReview.RideID == ride_id)
            .order_by(ReputationReview.Created_At.desc(), ReputationReview.ReviewID.desc())
        )
        reviews = list(shard_db.scalars(stmt))
    finally:
        shard_db.close()

    member_ids = {review.Reviewer_MemberID for review in reviews} | {review.Reviewee_MemberID for review in reviews}
    members = _member_map(member_ids, primary_db)
    return _to_review_response(reviews, members)


@router.get("/ride/{ride_id}/participants", response_model=list[ReviewParticipantResponse])
def list_review_participants(
    ride_id: int,
    current_member: Member = Depends(get_current_member),
    primary_db: Session = Depends(get_db_session),
) -> list[ReviewParticipantResponse]:
    shard_id = get_ride_shard_id(ride_id, primary_db)
    shard_db = SHARD_SESSION_MAKERS[shard_id]()
    try:
        ride = shard_db.scalar(select(Ride).where(Ride.RideID == ride_id))
        if ride is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
        if ride.Ride_Status != "Completed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ride is not completed")

        participants = _ride_participant_member_ids(ride_id, shard_db)
        if current_member.MemberID not in participants:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only ride participants can view this list")

        members = list(primary_db.scalars(select(Member).where(Member.MemberID.in_(participants))))
        response: list[ReviewParticipantResponse] = []
        for member in members:
            role = "Host" if member.MemberID == ride.Host_MemberID else "Passenger"
            response.append(ReviewParticipantResponse(MemberID=member.MemberID, Full_Name=member.Full_Name, Role=role))
        return response
    finally:
        shard_db.close()


@router.get("/member/{member_id}", response_model=list[ReviewReadResponse])
def list_member_reviews(
    member_id: int,
    _: Member = Depends(get_current_member),
    primary_db: Session = Depends(get_db_session),
) -> list[dict[str, object]]:
    reviews = _reviews_for_member_across_shards(member_id, include_as_reviewee=True)
    member_ids = {review.Reviewer_MemberID for review in reviews} | {review.Reviewee_MemberID for review in reviews}
    members = _member_map(member_ids, primary_db)
    return _to_review_response(reviews, members)


@router.get("/my", response_model=list[ReviewReadResponse])
def list_my_reviews(
    current_member: Member = Depends(get_current_member),
    primary_db: Session = Depends(get_db_session),
) -> list[dict[str, object]]:
    reviews = _reviews_for_member_across_shards(current_member.MemberID, include_as_reviewee=False)
    member_ids = {review.Reviewer_MemberID for review in reviews} | {review.Reviewee_MemberID for review in reviews}
    members = _member_map(member_ids, primary_db)
    return _to_review_response(reviews, members)


@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    current_member: Member = Depends(get_current_member),
    primary_db: Session = Depends(get_db_session),
) -> dict[str, str]:
    shard_id = _resolve_review_shard_id(review_id, primary_db)
    if shard_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    shard_db = SHARD_SESSION_MAKERS[shard_id]()
    try:
        review = shard_db.scalar(select(ReputationReview).where(ReputationReview.ReviewID == review_id))
        if review is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        if review.Reviewer_MemberID != current_member.MemberID:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the reviewer can delete this review")

        reviewee_id = review.Reviewee_MemberID
        shard_db.delete(review)
        shard_db.commit()
    finally:
        shard_db.close()

    try:
        delete_review_shard_id(review_id, primary_db)
        primary_db.commit()
    except Exception:
        primary_db.rollback()
        logger.exception("reviews.directory.delete_failed review_id=%s", review_id)

    try:
        _sync_reputation_score(reviewee_id, primary_db)
    except Exception:
        logger.exception("reviews.reputation_score_sync_failed reviewee_member_id=%s", reviewee_id)

    audit_event(
        action="reviews.delete",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"review_id": review_id},
    )
    return {"message": "Review deleted"}
