from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.v1.deps import DBSession, require_roles
from app.api.v1.routes._serializers import user_dict
from app.core.responses import APIException, success
from app.models import User
from app.schemas.common import page_data
from app.schemas.user import UserCreate, UserPasswordReset, UserStatusUpdate, UserUpdate
from app.services.log_service import LogService
from app.services.user_service import UserService

router = APIRouter()
AdminUser = Annotated[User, Depends(require_roles("admin"))]


@router.get("")
def list_users(
    db: DBSession,
    _: AdminUser,
    keyword: str | None = None,
    role: str | None = None,
    status_value: Annotated[int | None, Query(alias="status")] = None,
    department: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    items, total = UserService(db).list(
        keyword=keyword,
        role=role,
        status=status_value,
        department=department,
        page=page,
        page_size=page_size,
    )
    return success(page_data([user_dict(item) for item in items], total, page, page_size))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: DBSession,
    request: Request,
    current_user: AdminUser,
) -> dict:
    service = UserService(db)
    if service.get_by_username(payload.username):
        raise APIException("用户名已存在", status.HTTP_409_CONFLICT, 40900)
    user = service.create(payload)
    LogService(db).record(
        user_id=current_user.id,
        module_name="用户管理",
        operation_type="create",
        business_id=user.id,
        request=request,
    )
    db.commit()
    return success(user_dict(user), "用户创建成功")


@router.get("/{user_id}")
def get_user(user_id: int, db: DBSession, _: AdminUser) -> dict:
    user = UserService(db).get(user_id)
    if user is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    return success(user_dict(user))


@router.put("/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: DBSession,
    request: Request,
    current_user: AdminUser,
) -> dict:
    user = UserService(db).update(user_id, payload)
    if user is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="用户管理",
        operation_type="update",
        business_id=user_id,
        request=request,
    )
    db.commit()
    return success(None, "用户修改成功")


@router.patch("/{user_id}/status")
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: DBSession,
    request: Request,
    current_user: AdminUser,
) -> dict:
    if payload.status not in {0, 1}:
        raise APIException("status 只能为 1 或 0", status.HTTP_400_BAD_REQUEST, 40000)
    if user_id == current_user.id and payload.status == 0:
        raise APIException("不允许禁用当前登录用户", status.HTTP_409_CONFLICT, 40900)
    user = UserService(db).update_status(user_id, payload.status)
    if user is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="用户管理",
        operation_type="update_status",
        business_id=user_id,
        request=request,
    )
    db.commit()
    return success(None, "用户状态修改成功")


@router.patch("/{user_id}/password")
def reset_user_password(
    user_id: int,
    payload: UserPasswordReset,
    db: DBSession,
    request: Request,
    current_user: AdminUser,
) -> dict:
    if len(payload.new_password) < 6:
        raise APIException("新密码长度至少 6 位", status.HTTP_400_BAD_REQUEST, 40000)
    user = UserService(db).reset_password(user_id, payload.new_password)
    if user is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="用户管理",
        operation_type="reset_password",
        business_id=user_id,
        request=request,
    )
    db.commit()
    return success(None, "密码重置成功")


@router.delete("/{user_id}")
def delete_user(user_id: int, db: DBSession, request: Request, current_user: AdminUser) -> dict:
    service = UserService(db)
    if user_id == current_user.id:
        raise APIException("不允许删除当前登录用户", status.HTTP_409_CONFLICT, 40900)
    if service.get(user_id) is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    if service.has_related_data(user_id):
        raise APIException("用户已关联业务数据，建议禁用用户", status.HTTP_409_CONFLICT, 40900)
    service.delete(user_id)
    LogService(db).record(
        user_id=current_user.id,
        module_name="用户管理",
        operation_type="delete",
        business_id=user_id,
        request=request,
    )
    db.commit()
    return success(None, "用户删除成功")
