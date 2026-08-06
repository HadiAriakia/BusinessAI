from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80, examples=["hugh"])
    email: EmailStr = Field(examples=["hugh@example.com"])
    password: str = Field(min_length=8, examples=["correct-horse-battery"])

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        return value.strip()


class LoginRequest(BaseModel):
    email: EmailStr = Field(examples=["hugh@example.com"])
    password: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str


class AuthResponse(BaseModel):
    user: UserResponse
    token: str
