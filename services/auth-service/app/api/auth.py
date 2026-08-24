from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterUserRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services.auth_service import (
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidRefreshTokenError,
    InvalidCredentialsError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(payload: RegisterUserRequest, db: Session = Depends(get_db)) -> UserRead:
    auth_service = AuthService(UserRepository(db), RefreshTokenRepository(db))

    try:
        user = auth_service.register_user(
            email=payload.email,
            password=payload.password,
            name=payload.name,
        )
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        ) from exc

    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    auth_service = AuthService(UserRepository(db), RefreshTokenRepository(db))

    try:
        token_pair = auth_service.login_user(
            email=payload.email,
            password=payload.password,
            device_id=payload.device_id,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        ) from exc

    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    auth_service = AuthService(UserRepository(db), RefreshTokenRepository(db))

    try:
        token_pair = auth_service.refresh_access_token(refresh_token=payload.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        ) from exc

    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(payload: LogoutRequest, db: Session = Depends(get_db)) -> None:
    auth_service = AuthService(UserRepository(db), RefreshTokenRepository(db))
    auth_service.logout_user(refresh_token=payload.refresh_token)
