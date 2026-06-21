from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models import User
from app.services.user_service import UserService


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def authenticate(self, username: str, password: str) -> User | None:
        user = UserService(self.db).get_by_username(username)
        if user is None or user.status != 1:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def create_user_token(self, user: User) -> str:
        return create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
