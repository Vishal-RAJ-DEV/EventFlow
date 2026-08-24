from pydantic import BaseModel, Field


class RegisterUserRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str
    device_id: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
