from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.v1.deps import DBSession, require_permissions
from app.api.v1.routes._serializers import work_group_dict, work_group_member_dict
from app.core.responses import APIException, success
from app.models import User
from app.schemas.common import page_data
from app.schemas.work_group_schema import (
    WorkGroupCreate,
    WorkGroupMemberCreate,
    WorkGroupMemberUpdate,
    WorkGroupUpdate,
)
from app.services.log_service import LogService
from app.services.work_group_service import (
    WorkGroupConflictError,
    WorkGroupNotFoundError,
    WorkGroupService,
)

router = APIRouter()
WorkGroupReader = Annotated[User, Depends(require_permissions("work_group:list"))]
WorkGroupCreator = Annotated[User, Depends(require_permissions("work_group:create"))]
WorkGroupUpdater = Annotated[User, Depends(require_permissions("work_group:update"))]
WorkGroupDeleter = Annotated[User, Depends(require_permissions("work_group:delete"))]
MemberReader = Annotated[User, Depends(require_permissions("work_group:member:list"))]
MemberAdder = Annotated[User, Depends(require_permissions("work_group:member:add"))]
MemberUpdater = Annotated[User, Depends(require_permissions("work_group:member:update"))]
MemberDeleter = Annotated[User, Depends(require_permissions("work_group:member:delete"))]


@router.get("")
def list_work_groups(
    db: DBSession,
    _: WorkGroupReader,
    keyword: str | None = None,
    status_value: Annotated[int | None, Query(alias="status", ge=0, le=1)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    items, total = WorkGroupService(db).list_work_groups(
        keyword=keyword,
        status=status_value,
        page=page,
        page_size=page_size,
    )
    return success(page_data([work_group_dict(item) for item in items], total, page, page_size))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_work_group(
    payload: WorkGroupCreate,
    db: DBSession,
    request: Request,
    current_user: WorkGroupCreator,
) -> dict:
    try:
        group = WorkGroupService(db).create_work_group(payload)
    except WorkGroupConflictError as exc:
        raise APIException("运维组编码已存在", status.HTTP_409_CONFLICT, 40900) from exc
    except WorkGroupNotFoundError as exc:
        raise APIException("组长用户不存在", status.HTTP_404_NOT_FOUND, 40400) from exc
    LogService(db).record(
        user_id=current_user.id,
        module_name="运维组",
        operation_type="create",
        business_id=group.id,
        request=request,
    )
    db.commit()
    return success(work_group_dict(group), "运维组创建成功")


@router.get("/{group_id}")
def get_work_group(group_id: int, db: DBSession, _: WorkGroupReader) -> dict:
    group = WorkGroupService(db).get_work_group_detail(group_id)
    if group is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    return success(work_group_dict(group))


@router.put("/{group_id}")
def update_work_group(
    group_id: int,
    payload: WorkGroupUpdate,
    db: DBSession,
    request: Request,
    current_user: WorkGroupUpdater,
) -> dict:
    try:
        group = WorkGroupService(db).update_work_group(group_id, payload)
    except WorkGroupConflictError as exc:
        raise APIException("运维组编码已存在", status.HTTP_409_CONFLICT, 40900) from exc
    except WorkGroupNotFoundError as exc:
        raise APIException("组长用户不存在", status.HTTP_404_NOT_FOUND, 40400) from exc
    if group is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="运维组",
        operation_type="update",
        business_id=group_id,
        request=request,
    )
    db.commit()
    return success(work_group_dict(group), "运维组修改成功")


@router.delete("/{group_id}")
def delete_work_group(
    group_id: int,
    db: DBSession,
    request: Request,
    current_user: WorkGroupDeleter,
) -> dict:
    deleted = WorkGroupService(db).delete_work_group(group_id)
    if not deleted:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="运维组",
        operation_type="delete",
        business_id=group_id,
        request=request,
    )
    db.commit()
    return success(None, "运维组删除成功")


@router.get("/{group_id}/members")
def list_work_group_members(
    group_id: int,
    db: DBSession,
    _: MemberReader,
    keyword: str | None = None,
    status_value: Annotated[int | None, Query(alias="status", ge=0, le=1)] = 1,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    try:
        items, total = WorkGroupService(db).list_group_members(
            group_id=group_id,
            keyword=keyword,
            status=status_value,
            page=page,
            page_size=page_size,
        )
    except WorkGroupNotFoundError as exc:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400) from exc
    return success(
        page_data([work_group_member_dict(item) for item in items], total, page, page_size)
    )


@router.post("/{group_id}/members", status_code=status.HTTP_201_CREATED)
def add_work_group_member(
    group_id: int,
    payload: WorkGroupMemberCreate,
    db: DBSession,
    request: Request,
    current_user: MemberAdder,
) -> dict:
    try:
        member = WorkGroupService(db).add_group_member(group_id=group_id, payload=payload)
    except WorkGroupNotFoundError as exc:
        raise APIException("运维组或用户不存在或未启用", status.HTTP_404_NOT_FOUND, 40400) from exc
    except WorkGroupConflictError as exc:
        raise APIException("用户已在该运维组中", status.HTTP_409_CONFLICT, 40900) from exc
    LogService(db).record(
        user_id=current_user.id,
        module_name="运维组成员",
        operation_type="create",
        business_id=member.id,
        request=request,
    )
    db.commit()
    return success(work_group_member_dict(member), "成员添加成功")


@router.put("/{group_id}/members/{user_id}")
def update_work_group_member(
    group_id: int,
    user_id: int,
    payload: WorkGroupMemberUpdate,
    db: DBSession,
    request: Request,
    current_user: MemberUpdater,
) -> dict:
    member = WorkGroupService(db).update_group_member(
        group_id=group_id,
        user_id=user_id,
        payload=payload,
    )
    if member is None:
        raise APIException("成员关系不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="运维组成员",
        operation_type="update",
        business_id=member.id,
        request=request,
    )
    db.commit()
    return success(work_group_member_dict(member), "成员修改成功")


@router.delete("/{group_id}/members/{user_id}")
def delete_work_group_member(
    group_id: int,
    user_id: int,
    db: DBSession,
    request: Request,
    current_user: MemberDeleter,
) -> dict:
    removed = WorkGroupService(db).remove_group_member(group_id=group_id, user_id=user_id)
    if not removed:
        raise APIException("成员关系不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="运维组成员",
        operation_type="delete",
        business_id=group_id,
        request=request,
    )
    db.commit()
    return success(None, "成员移除成功")
