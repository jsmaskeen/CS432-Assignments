from pydantic import BaseModel, ConfigDict, Field


class LocationCreateRequest(BaseModel):
    location_name: str = Field(min_length=1, max_length=100)
    location_type: str = Field(min_length=1, max_length=20)
    geohash: str | None = Field(default=None, min_length=4, max_length=20)


class LocationReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    LocationID: int
    Location_Name: str
    Location_Type: str
    GeoHash: str | None
