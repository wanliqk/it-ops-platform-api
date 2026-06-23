from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.responses import APIException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import SysPermission, SysRole, SysRolePermission, SysUserRole, User

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


def get_user_role_codes(db: Session, user_id: int) -> set[str]:
    stmt = (
        select(SysRole.role_code)
        .join(SysUserRole, SysUserRole.role_id == SysRole.id)
        .where(SysUserRole.user_id == user_id, SysRole.status == 1)
    )
    return set(db.scalars(stmt))


def get_user_permission_codes(db: Session, user_id: int) -> set[str]:
    stmt = (
        select(SysPermission.permission_code)
        .join(SysRolePermission, SysRolePermission.permission_id == SysPermission.id)
        .join(SysRole, SysRole.id == SysRolePermission.role_id)
        .join(SysUserRole, SysUserRole.role_id == SysRole.id)
        .where(
            SysUserRole.user_id == user_id,
            SysRole.status == 1,
            SysPermission.status == 1,
        )
    )
    return set(db.scalars(stmt))


def require_permissions(
    *permission_codes: str,
    require_all: bool = True,
) -> Callable[[Session, User], User]:
    def dependency(
        db: DBSession,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        user_permissions = get_user_permission_codes(db, current_user.id)
        required = set(permission_codes)
        allowed = (
            required.issubset(user_permissions)
            if require_all
            else bool(required & user_permissions)
        )
        if not allowed:
            raise APIException("无权限操作", status.HTTP_403_FORBIDDEN, 40300)
        return current_user

    return dependency


def require_roles(*role_codes: str) -> Callable[[Session, User], User]:
    def dependency(
        db: DBSession,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if not set(role_codes) & get_user_role_codes(db, current_user.id):
            raise APIException("无权限操作", status.HTTP_403_FORBIDDEN, 40300)
        return current_user

    return dependency
