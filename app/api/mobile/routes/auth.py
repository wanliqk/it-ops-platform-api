from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.mobile.deps import DBSession, get_current_mobile_user
from app.core.responses import MobileAPIException, success_response
from app.core.security import verify_password
from app.models import User
from app.schemas.mobile import MobileLoginData, MobileLoginRequest, MobileResponse, MobileUserRead
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter()
CurrentUser = Annotated[User, Depends(get_current_mobile_user)]


@router.post("/login", response_model=MobileResponse[MobileLoginData])
def login(payload: MobileLoginRequest, db: DBSession) -> dict:
    user = UserService(db).get_by_username(payload.username)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise MobileAPIException("用户名或密码错误")
    if user.status == 0:
        raise MobileAPIException("账号已禁用")

    token = AuthService(db).create_user_token(user)
    return success_response(
        MobileLoginData(access_token=token, user=MobileUserRead.model_validate(user))
    )


@router.get("/me", response_model=MobileResponse[MobileUserRead])
def me(current_user: CurrentUser) -> dict:
    return success_response(MobileUserRead.model_validate(current_user))
