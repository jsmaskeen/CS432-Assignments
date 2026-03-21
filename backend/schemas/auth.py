from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=6, max_length=64)
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)
    phone_number: str | None = Field(default=None, max_length=15)
    gender: str = Field(pattern="^(Male|Female|Other)$")

    @field_validator("email")
    @classmethod
    def validate_iitgn_domain(cls, value: EmailStr) -> EmailStr:
        if not str(value).endswith("@iitgn.ac.in"):
            raise ValueError("Only @iitgn.ac.in email addresses are allowed")
        return value


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=64)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    member_id: int
    username: str
    role: str
    email: EmailStr
    full_name: str


