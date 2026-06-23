from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, status
from sqlalchemy.orm import Session

from app.core.responses import APIException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User

DBSession = Annotated[Session, Depends(get_db)]
AuthorizationHeader = Annotated[str | None, Header(alias="Authorization")] 


def get_current_user(
    db: DBSession,
    authorization: AuthorizationHeader = None,
) -> User:
    if not authorization:
        raise APIException("未登录或 Token 无效", status.HTTP_401_UNAUTHORIZED, 40100)

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise APIException("未登录或 Token 无效", status.HTTP_401_UNAUTHORIZED, 40100)

    payload = decode_access_token(token)
    if payload is None or payload.get("sub") is None:
        raise APIException("未登录或 Token 无效", status.HTTP_401_UNAUTHORIZED, 40100)

    user = db.get(User, int(payload["sub"]))
    if user is None or user.status != 1:
        raise APIException("未登录或 Token 无效", status.HTTP_401_UNAUTHORIZED, 40100)
    return user


def require_roles(*roles: str) -> Callable[[User], User]:
    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if str(current_user.role) not in roles:
            raise APIException("无权限操作", status.HTTP_403_FORBIDDEN, 40300)
        return current_user

    return dependency
