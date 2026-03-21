import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.session import get_db_session
from models.location import Location
from schemas.location import LocationReadResponse

router = APIRouter(prefix="/locations", tags=["locations"])
logger = logging.getLogger("rajak.locations")


@router.get("", response_model=list[LocationReadResponse])
def list_locations(
    search: str | None = Query(default=None, min_length=1),
    location_type: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=100, ge=1, le=300),
    db: Session = Depends(get_db_session),
) -> list[Location]:
    logger.info("locations.list search=%s location_type=%s limit=%s", search, location_type, limit)
    stmt = select(Location)
    if search:
        stmt = stmt.where(Location.Location_Name.ilike(f"%{search.strip()}%"))
    if location_type:
        stmt = stmt.where(Location.Location_Type == location_type.strip())
    stmt = stmt.order_by(Location.Location_Name.asc()).limit(limit)
    return list(db.scalars(stmt))


@router.get("/{location_id}", response_model=LocationReadResponse)
def get_location(location_id: int, db: Session = Depends(get_db_session)) -> Location:
    location = db.scalar(select(Location).where(Location.LocationID == location_id))
    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return location
