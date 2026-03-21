import logging
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.dependencies import get_current_member
from core.audit import audit_event
from db.session import get_db_session
from models.booking import Booking
from models.member import Member
from models.review import ReputationReview
from models.ride import Ride
from schemas.review import ReviewCreateRequest, ReviewReadResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])
logger = logging.getLogger("rajak.reviews")


def _update_reputation_score(member_id: int, db: Session) -> None:
    avg_rating = db.scalar(
        select(func.avg(ReputationReview.Rating)).where(ReputationReview.Reviewee_MemberID == member_id)
    )
    if avg_rating is None:
        score = Decimal("0.0")
    else:
        score = Decimal(str(avg_rating)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    member = db.scalar(select(Member).where(Member.MemberID == member_id))
    if member is not None:
        member.Reputation_Score = score


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
    db: Session = Depends(get_db_session),
) -> ReputationReview:
    ride = db.scalar(select(Ride).where(Ride.RideID == payload.ride_id))
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if ride.Ride_Status != "Completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reviews are allowed only for completed rides")

    participants = _ride_participant_member_ids(payload.ride_id, db)
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
    db.add(review)
    db.flush()
    _update_reputation_score(payload.reviewee_member_id, db)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Review already exists for this reviewer-reviewee pair") from exc

    db.refresh(review)
    audit_event(
        action="reviews.create",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"review_id": review.ReviewID, "ride_id": payload.ride_id},
    )
    return review


@router.get("/ride/{ride_id}", response_model=list[ReviewReadResponse])
def list_ride_reviews(
    ride_id: int,
    _: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> list[ReputationReview]:
    stmt = select(ReputationReview).where(ReputationReview.RideID == ride_id).order_by(ReputationReview.Created_At.desc())
    return list(db.scalars(stmt))


@router.get("/member/{member_id}", response_model=list[ReviewReadResponse])
def list_member_reviews(
    member_id: int,
    _: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> list[ReputationReview]:
    stmt = (
        select(ReputationReview)
        .where(
            or_(
                ReputationReview.Reviewer_MemberID == member_id,
                ReputationReview.Reviewee_MemberID == member_id,
            )
        )
        .order_by(ReputationReview.Created_At.desc())
    )
    return list(db.scalars(stmt))


@router.get("/my", response_model=list[ReviewReadResponse])
def list_my_reviews(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> list[ReputationReview]:
    stmt = (
        select(ReputationReview)
        .where(ReputationReview.Reviewer_MemberID == current_member.MemberID)
        .order_by(ReputationReview.Created_At.desc())
    )
    return list(db.scalars(stmt))


@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> dict[str, str]:
    review = db.scalar(select(ReputationReview).where(ReputationReview.ReviewID == review_id))
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.Reviewer_MemberID != current_member.MemberID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the reviewer can delete this review")

    reviewee_id = review.Reviewee_MemberID
    db.delete(review)
    db.flush()
    _update_reputation_score(reviewee_id, db)
    db.commit()
    audit_event(
        action="reviews.delete",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"review_id": review_id},
    )
    return {"message": "Review deleted"}
