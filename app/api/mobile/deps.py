from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.responses import MobileAPIException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User

DBSession = Annotated[Session, Depends(get_db)]


def get_current_mobile_user(
    db: DBSession,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> User:
    if not authorization:
        raise MobileAPIException("未登录或登录已过期", status_code=401)

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise MobileAPIException("无效的认证信息", status_code=401)

    payload = decode_access_token(token)
    if payload is None:
        raise MobileAPIException("未登录或登录已过期", status_code=401)

    user_id = payload.get("sub")
    if user_id is None:
        raise MobileAPIException("无效的认证信息", status_code=401)

    user = db.get(User, int(user_id))
    if user is None or user.status != 1:
        raise MobileAPIException("用户不存在或已禁用", status_code=401)
    return user
