from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreateRequest(BaseModel):
    ride_id: int
    reviewee_member_id: int
    rating: int = Field(ge=1, le=5)
    comments: str | None = None


class ReviewUpdateRequest(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comments: str | None = None


class ReviewReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ReviewID: int
    RideID: int
    Reviewer_MemberID: int
    Reviewee_MemberID: int
    Rating: int
    Comments: str | None
    Created_At: datetime
