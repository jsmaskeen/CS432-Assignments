import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.dependencies import get_current_member
from core.audit import audit_event
from db.session import get_db_session
from models.location import Location
from models.member import Member
from models.saved_address import SavedAddress
from schemas.saved_address import (
    SavedAddressCreateRequest,
    SavedAddressReadResponse,
    SavedAddressUpdateRequest,
)

router = APIRouter(prefix="/saved-addresses", tags=["saved-addresses"])
logger = logging.getLogger("rajak.saved_addresses")


@router.get("", response_model=list[SavedAddressReadResponse])
def list_saved_addresses(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> list[SavedAddress]:
    stmt = select(SavedAddress).where(SavedAddress.MemberID == current_member.MemberID).order_by(SavedAddress.AddressID.asc())
    return list(db.scalars(stmt))


@router.post("", response_model=SavedAddressReadResponse, status_code=status.HTTP_201_CREATED)
def create_saved_address(
    payload: SavedAddressCreateRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> SavedAddress:
    location = db.scalar(select(Location).where(Location.LocationID == payload.location_id))
    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    address = SavedAddress(
        MemberID=current_member.MemberID,
        Label=payload.label.strip(),
        LocationID=payload.location_id,
    )
    db.add(address)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Saved address already exists") from exc

    db.refresh(address)
    audit_event(
        action="saved_addresses.create",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"address_id": address.AddressID},
    )
    return address


@router.patch("/{address_id}", response_model=SavedAddressReadResponse)
def update_saved_address(
    address_id: int,
    payload: SavedAddressUpdateRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> SavedAddress:
    address = db.scalar(select(SavedAddress).where(SavedAddress.AddressID == address_id))
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved address not found")
    if address.MemberID != current_member.MemberID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this address")

    if payload.location_id is not None:
        location = db.scalar(select(Location).where(Location.LocationID == payload.location_id))
        if location is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
        address.LocationID = payload.location_id

    if payload.label is not None:
        address.Label = payload.label.strip()

    db.commit()
    db.refresh(address)
    audit_event(
        action="saved_addresses.update",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"address_id": address.AddressID},
    )
    return address


@router.delete("/{address_id}")
def delete_saved_address(
    address_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db_session),
) -> dict[str, str]:
    address = db.scalar(select(SavedAddress).where(SavedAddress.AddressID == address_id))
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved address not found")
    if address.MemberID != current_member.MemberID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this address")

    db.delete(address)
    db.commit()
    audit_event(
        action="saved_addresses.delete",
        status="success",
        actor_member_id=current_member.MemberID,
        actor_username=None,
        details={"address_id": address_id},
    )
    return {"message": "Saved address deleted"}
