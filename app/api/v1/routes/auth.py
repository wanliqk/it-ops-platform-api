from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.api.v1.routes._serializers import user_dict
from app.core.config import settings
from app.core.responses import APIException, success
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, LogoutResponse
from app.schemas.user import UserPasswordChange
from app.services.auth_service import AuthService
from app.services.log_service import LogService
from app.services.user_service import UserService
from app.utils.permissions import get_user_permission_codes, get_user_role_codes

router = APIRouter()
DBSession = Annotated[Session, Depends(get_db)]
AuthorizationHeader = Annotated[str, Header(alias="Authorization")]


@router.post("/login")
def login(payload: LoginRequest, db: DBSession, request: Request) -> dict:
    service = AuthService(db)
    found_user = UserService(db).get_by_username(payload.username)
    if found_user is not None and found_user.status == 0:
        raise APIException("账号已禁用", status.HTTP_403_FORBIDDEN, 40002)
    user = service.authenticate(payload.username, payload.password)
    if user is None:
        raise APIException("用户名或密码错误", status.HTTP_401_UNAUTHORIZED, 40001)

    LogService(db).record(
        user_id=user.id,
        module_name="用户登录",
        operation_type="login",
        request=request,
    )
    db.commit()
    return success(
        {
            "access_token": service.create_user_token(user),
            "token_type": "Bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": user_dict(user),
        }
    )


@router.get("/me")
def me(db: DBSession, current_user: Annotated[User, Depends(get_current_user)]) -> dict:
    data = user_dict(current_user)
    data["roles"] = sorted(get_user_role_codes(db, current_user.id))
    data["permissions"] = sorted(get_user_permission_codes(db, current_user.id))
    return success(data)


@router.put("/password")
def change_password(
    payload: UserPasswordChange,
    db: DBSession,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    if len(payload.new_password) < 6:
        raise APIException("新密码长度至少 6 位", status.HTTP_400_BAD_REQUEST, 40000)
    changed = AuthService(db).change_password(
        current_user,
        payload.old_password,
        payload.new_password,
    )
    if not changed:
        raise APIException("原密码错误", status.HTTP_400_BAD_REQUEST, 40000)
    LogService(db).record(
        user_id=current_user.id,
        module_name="认证",
        operation_type="change_password",
        business_id=current_user.id,
        request=request,
    )
    db.commit()
    return success(None, "密码修改成功")


@router.post("/logout", response_model=LogoutResponse)
def logout(authorization: AuthorizationHeader) -> LogoutResponse:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token or decode_access_token(token) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return LogoutResponse(message="Logout successful. Please clear the local access token.")
