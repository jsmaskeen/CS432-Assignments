from pydantic import BaseModel, ConfigDict, Field


class SavedAddressCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=50)
    location_id: int


class SavedAddressUpdateRequest(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=50)
    location_id: int | None = None


class SavedAddressReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    AddressID: int
    MemberID: int
    Label: str
    LocationID: int
