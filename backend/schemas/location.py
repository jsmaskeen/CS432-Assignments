from pydantic import BaseModel, ConfigDict


class LocationReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    LocationID: int
    Location_Name: str
    Location_Type: str
    GeoHash: str | None
