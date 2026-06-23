from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.v1.deps import DBSession, require_permissions
from app.core.responses import APIException, success
from app.models import SysPermission, SysRole, User
from app.schemas.common import page_data
from app.schemas.rbac_schema import (
    PermissionRead,
    RoleCreate,
    RolePermissionAssign,
    RoleRead,
    RoleStatusUpdate,
    RoleUpdate,
    UserRoleAssign,
)
from app.services.log_service import LogService
from app.services.rbac_service import RbacService

router = APIRouter()
RoleReader = Annotated[User, Depends(require_permissions("role:view"))]
RoleCreator = Annotated[User, Depends(require_permissions("role:create"))]
RoleUpdater = Annotated[User, Depends(require_permissions("role:update"))]
RoleDeleter = Annotated[User, Depends(require_permissions("role:delete"))]
PermissionReader = Annotated[User, Depends(require_permissions("permission:view"))]
RolePermissionAssigner = Annotated[User, Depends(require_permissions("role:assign_permission"))]
UserRoleReader = Annotated[
    User,
    Depends(require_permissions("user:view", "user:assign_role", require_all=False)),
]
UserRoleAssigner = Annotated[User, Depends(require_permissions("user:assign_role"))]


def record_rbac_log(
    db: DBSession,
    *,
    user_id: int,
    operation_type: str,
    request: Request,
    business_id: int | None = None,
) -> None:
    LogService(db).record(
        user_id=user_id,
        module_name="角色权限管理",
        operation_type=operation_type,
        business_id=business_id,
        request=request,
    )
    db.commit()


def role_dict(role: SysRole) -> dict:
    return RoleRead.model_validate(role).model_dump()


def permission_dict(permission: SysPermission) -> dict:
    return PermissionRead.model_validate(permission).model_dump()


@router.get("/roles")
def list_roles(
    db: DBSession,
    current_user: RoleReader,
    request: Request,
    keyword: str | None = None,
    status_value: Annotated[int | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 100,
) -> dict:
    roles, total = RbacService(db).list_roles(
        keyword=keyword,
        status=status_value,
        page=page,
        page_size=page_size,
    )
    record_rbac_log(db, user_id=current_user.id, operation_type="list_roles", request=request)
    return success(page_data([role_dict(role) for role in roles], total, page, page_size))


@router.post("/roles", status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    db: DBSession,
    request: Request,
    current_user: RoleCreator,
) -> dict:
    service = RbacService(db)
    if service.get_role_by_code(payload.role_code):
        raise APIException("角色编码已存在", status.HTTP_409_CONFLICT, 40900)
    role = service.create_role(payload)
    LogService(db).record(
        user_id=current_user.id,
        module_name="角色权限管理",
        operation_type="create_role",
        business_id=role.id,
        request=request,
    )
    db.commit()
    return success(role_dict(role), "角色创建成功")


@router.get("/roles/{role_id}")
def get_role(role_id: int, db: DBSession, current_user: RoleReader, request: Request) -> dict:
    role = RbacService(db).get_role(role_id)
    if role is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    record_rbac_log(
        db,
        user_id=current_user.id,
        operation_type="get_role",
        business_id=role_id,
        request=request,
    )
    return success(role_dict(role))


@router.put("/roles/{role_id}")
def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: DBSession,
    request: Request,
    current_user: RoleUpdater,
) -> dict:
    service = RbacService(db)
    if payload.role_code:
        exists = service.get_role_by_code(payload.role_code)
        if exists and exists.id != role_id:
            raise APIException("角色编码已存在", status.HTTP_409_CONFLICT, 40900)
    role = service.update_role(role_id, payload)
    if role is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="角色权限管理",
        operation_type="update_role",
        business_id=role_id,
        request=request,
    )
    db.commit()
    return success(role_dict(role), "角色修改成功")


@router.patch("/roles/{role_id}/status")
def update_role_status(
    role_id: int,
    payload: RoleStatusUpdate,
    db: DBSession,
    request: Request,
    current_user: RoleUpdater,
) -> dict:
    if payload.status not in {0, 1}:
        raise APIException("status 只能为 1 或 0", status.HTTP_400_BAD_REQUEST, 40000)
    role = RbacService(db).update_role_status(role_id, payload.status)
    if role is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="角色权限管理",
        operation_type="update_role_status",
        business_id=role_id,
        request=request,
    )
    db.commit()
    return success(None, "角色状态修改成功")


@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    db: DBSession,
    request: Request,
    current_user: RoleDeleter,
) -> dict:
    service = RbacService(db)
    if service.get_role(role_id) is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    if service.role_has_bindings(role_id):
        raise APIException("角色已关联用户或权限，不能删除", status.HTTP_409_CONFLICT, 40900)
    service.delete_role(role_id)
    LogService(db).record(
        user_id=current_user.id,
        module_name="角色权限管理",
        operation_type="delete_role",
        business_id=role_id,
        request=request,
    )
    db.commit()
    return success(None, "角色删除成功")


@router.get("/permissions")
def list_permissions(
    db: DBSession,
    current_user: PermissionReader,
    request: Request,
    keyword: str | None = None,
    module_name: str | None = None,
    status_value: Annotated[int | None, Query(alias="status")] = None,
) -> dict:
    permissions = RbacService(db).list_permissions(
        keyword=keyword,
        module_name=module_name,
        status=status_value,
    )
    record_rbac_log(
        db,
        user_id=current_user.id,
        operation_type="list_permissions",
        request=request,
    )
    return success([permission_dict(permission) for permission in permissions])


@router.get("/permissions/grouped")
def grouped_permissions(db: DBSession, current_user: PermissionReader, request: Request) -> dict:
    grouped = defaultdict(list)
    for permission in RbacService(db).list_permissions():
        grouped[permission.module_name].append(permission_dict(permission))
    record_rbac_log(
        db,
        user_id=current_user.id,
        operation_type="list_permissions_grouped",
        request=request,
    )
    return success(
        [
            {"module_name": module_name, "permissions": permissions}
            for module_name, permissions in grouped.items()
        ]
    )


@router.get("/roles/{role_id}/permissions")
def get_role_permissions(
    role_id: int,
    db: DBSession,
    current_user: RoleReader,
    request: Request,
) -> dict:
    service = RbacService(db)
    if service.get_role(role_id) is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    record_rbac_log(
        db,
        user_id=current_user.id,
        operation_type="get_role_permissions",
        business_id=role_id,
        request=request,
    )
    return success([permission_dict(item) for item in service.get_role_permissions(role_id)])


@router.put("/roles/{role_id}/permissions")
def set_role_permissions(
    role_id: int,
    payload: RolePermissionAssign,
    db: DBSession,
    request: Request,
    current_user: RolePermissionAssigner,
) -> dict:
    service = RbacService(db)
    if service.get_role(role_id) is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    try:
        permissions = service.set_role_permissions(role_id, payload.permission_ids)
    except ValueError as exc:
        raise APIException(str(exc), status.HTTP_404_NOT_FOUND, 40400) from exc
    LogService(db).record(
        user_id=current_user.id,
        module_name="角色权限管理",
        operation_type="assign_role_permissions",
        business_id=role_id,
        request=request,
    )
    db.commit()
    return success([permission_dict(item) for item in permissions], "角色权限分配成功")


@router.get("/users/{user_id}/roles")
def get_user_roles(
    user_id: int,
    db: DBSession,
    current_user: UserRoleReader,
    request: Request,
) -> dict:
    service = RbacService(db)
    if not service.user_exists(user_id):
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    record_rbac_log(
        db,
        user_id=current_user.id,
        operation_type="get_user_roles",
        business_id=user_id,
        request=request,
    )
    return success([role_dict(item) for item in service.get_user_roles(user_id)])


@router.put("/users/{user_id}/roles")
def set_user_roles(
    user_id: int,
    payload: UserRoleAssign,
    db: DBSession,
    request: Request,
    current_user: UserRoleAssigner,
) -> dict:
    service = RbacService(db)
    if not service.user_exists(user_id):
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    try:
        roles = service.set_user_roles(user_id, payload.role_ids)
    except ValueError as exc:
        raise APIException(str(exc), status.HTTP_404_NOT_FOUND, 40400) from exc
    LogService(db).record(
        user_id=current_user.id,
        module_name="角色权限管理",
        operation_type="assign_user_roles",
        business_id=user_id,
        request=request,
    )
    db.commit()
    return success([role_dict(item) for item in roles], "用户角色分配成功")
