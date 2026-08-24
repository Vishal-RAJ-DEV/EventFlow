from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

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

    def login_user(self, *, email: str, password: str) -> str:
        normalized_email = email.strip().lower()
        user = self.user_repository.get_by_email(normalized_email)

        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError

        return create_access_token(user_id=user.id, email=user.email)
