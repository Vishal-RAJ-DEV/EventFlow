from pydantic import BaseModel, Field


class RegisterUserRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
