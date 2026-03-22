from pydantic import BaseModel, ConfigDict, Field


class PreferenceUpsertRequest(BaseModel):
    gender_preference: str = Field(pattern="^(Any|Same-Gender Only)$")
    notify_on_new_ride: bool = False
    music_preference: str | None = Field(default=None, max_length=100)


class PreferenceReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    PreferenceID: int
    MemberID: int
    Gender_Preference: str
    Notify_On_New_Ride: bool
    Music_Preference: str | None
