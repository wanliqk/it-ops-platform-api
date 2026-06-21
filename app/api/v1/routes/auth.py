from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse
from app.services.auth_service import AuthService

router = APIRouter()
DBSession = Annotated[Session, Depends(get_db)]
AuthorizationHeader = Annotated[str, Header(alias="Authorization")]


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: DBSession) -> LoginResponse:
    service = AuthService(db)
    user = service.authenticate(payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return LoginResponse(
        access_token=service.create_user_token(user),
        expires_in=settings.access_token_expire_minutes * 60,
        user=user,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(authorization: AuthorizationHeader) -> LogoutResponse:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token or decode_access_token(token) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return LogoutResponse(message="Logout successful. Please clear the local access token.")
