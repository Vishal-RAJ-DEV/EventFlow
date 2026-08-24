from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_refresh_token_expires_at,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
    ) -> None:
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository

    def register_user(self, *, email: str, password: str, name: str) -> User:
        normalized_email = email.strip().lower()

        existing_user = self.user_repository.get_by_email(normalized_email)
        if existing_user is not None:
            raise EmailAlreadyRegisteredError

        password_hash = hash_password(password)
        try:
            return self.user_repository.create(
                email=normalized_email,
                password_hash=password_hash,
                name=name.strip(),
            )
        except IntegrityError as exc:
            raise EmailAlreadyRegisteredError from exc

    def login_user(
        self,
        *,
        email: str,
        password: str,
        device_id: str | None = None,
    ) -> TokenPair:
        normalized_email = email.strip().lower()
        user = self.user_repository.get_by_email(normalized_email)

        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError

        return self._issue_token_pair(user=user, device_id=device_id)

    def refresh_access_token(self, *, refresh_token: str) -> TokenPair:
        token_hash = hash_refresh_token(refresh_token)
        stored_token = self.refresh_token_repository.get_by_token_hash(token_hash)

        if stored_token is None or self._is_expired(stored_token.expires_at):
            raise InvalidRefreshTokenError

        user = self.user_repository.get_by_id(stored_token.user_id)
        if user is None:
            raise InvalidRefreshTokenError

        device_id = stored_token.device_id
        self.refresh_token_repository.delete(stored_token)
        return self._issue_token_pair(user=user, device_id=device_id)

    def logout_user(self, *, refresh_token: str) -> None:
        token_hash = hash_refresh_token(refresh_token)
        self.refresh_token_repository.delete_by_token_hash(token_hash)

    def _issue_token_pair(self, *, user: User, device_id: str | None) -> TokenPair:
        refresh_token = create_refresh_token()
        self.refresh_token_repository.create(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            device_id=device_id,
            expires_at=get_refresh_token_expires_at(),
        )

        access_token = create_access_token(user_id=user.id, email=user.email)
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def _is_expired(self, expires_at: datetime) -> bool:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at <= datetime.now(timezone.utc)
