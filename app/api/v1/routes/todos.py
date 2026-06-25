from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.v1.deps import DBSession, get_current_user, require_permissions
from app.api.v1.routes._serializers import todo_dict
from app.core.responses import APIException, success
from app.models import User
from app.schemas.common import page_data
from app.schemas.todo_schema import TodoCancel, TodoComplete, TodoCreate, TodoStart
from app.services.log_service import LogService
from app.services.todo_service import TodoConflictError, TodoService

router = APIRouter()
CurrentUser = Annotated[User, Depends(get_current_user)]
TodoSelfReader = Annotated[User, Depends(require_permissions("todo:view_self"))]
TodoAllReader = Annotated[User, Depends(require_permissions("todo:view_all"))]
TodoCreator = Annotated[User, Depends(require_permissions("todo:create"))]
TodoUpdater = Annotated[User, Depends(require_permissions("todo:update"))]
TodoCanceller = Annotated[User, Depends(require_permissions("todo:cancel"))]


@router.get("/my")
def list_my_todos(
    db: DBSession,
    current_user: TodoSelfReader,
    status_value: Annotated[str | None, Query(alias="status")] = None,
    todo_type: str | None = None,
    business_type: str | None = None,
    priority: str | None = None,
    keyword: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    items, total = TodoService(db).list_my(
        user_id=current_user.id,
        status=status_value,
        todo_type=todo_type,
        business_type=business_type,
        priority=priority,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return success(page_data([todo_dict(item) for item in items], total, page, page_size))


@router.get("/my/statistics")
def my_todo_statistics(db: DBSession, current_user: TodoSelfReader) -> dict:
    return success(TodoService(db).statistics(current_user.id))


@router.get("")
def list_all_todos(
    db: DBSession,
    _: TodoAllReader,
    assignee_id: int | None = None,
    status_value: Annotated[str | None, Query(alias="status")] = None,
    todo_type: str | None = None,
    business_type: str | None = None,
    priority: str | None = None,
    keyword: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    items, total = TodoService(db).list_all(
        assignee_id=assignee_id,
        status=status_value,
        todo_type=todo_type,
        business_type=business_type,
        priority=priority,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return success(page_data([todo_dict(item) for item in items], total, page, page_size))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_todo(
    payload: TodoCreate,
    db: DBSession,
    request: Request,
    current_user: TodoCreator,
) -> dict:
    if payload.created_by is None:
        payload.created_by = current_user.id
    todo = TodoService(db).create(payload)
    LogService(db).record(
        user_id=current_user.id,
        module_name="待办事项",
        operation_type="create",
        business_id=todo.id,
        request=request,
    )
    db.commit()
    return success(todo_dict(todo), "待办创建成功")


@router.get("/{todo_id}")
def get_todo(todo_id: int, db: DBSession, current_user: CurrentUser) -> dict:
    todo = TodoService(db).get(todo_id)
    if todo is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    if not TodoService(db).can_access(todo, current_user):
        raise APIException("无权限操作", status.HTTP_403_FORBIDDEN, 40300)
    return success(todo_dict(todo))


@router.put("/{todo_id}/start")
def start_todo(
    todo_id: int,
    payload: TodoStart,
    db: DBSession,
    request: Request,
    current_user: TodoUpdater,
) -> dict:
    try:
        todo = TodoService(db).start(todo_id, current_user, payload.remark)
    except PermissionError as exc:
        raise APIException("无权限操作", status.HTTP_403_FORBIDDEN, 40300) from exc
    except TodoConflictError as exc:
        raise APIException("当前待办状态不允许执行该操作", status.HTTP_409_CONFLICT, 40900) from exc
    if todo is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="待办事项",
        operation_type="start",
        business_id=todo_id,
        request=request,
    )
    db.commit()
    return success(todo_dict(todo), "待办已开始处理")


@router.put("/{todo_id}/complete")
def complete_todo(
    todo_id: int,
    payload: TodoComplete,
    db: DBSession,
    request: Request,
    current_user: TodoUpdater,
) -> dict:
    try:
        todo = TodoService(db).complete(todo_id, current_user, payload.remark)
    except PermissionError as exc:
        raise APIException("无权限操作", status.HTTP_403_FORBIDDEN, 40300) from exc
    except TodoConflictError as exc:
        raise APIException("当前待办状态不允许执行该操作", status.HTTP_409_CONFLICT, 40900) from exc
    if todo is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="待办事项",
        operation_type="complete",
        business_id=todo_id,
        request=request,
    )
    db.commit()
    return success(todo_dict(todo), "待办已完成")


@router.put("/{todo_id}/cancel")
def cancel_todo(
    todo_id: int,
    payload: TodoCancel,
    db: DBSession,
    request: Request,
    current_user: TodoCanceller,
) -> dict:
    try:
        todo = TodoService(db).cancel(todo_id, current_user, payload.remark)
    except PermissionError as exc:
        raise APIException("无权限操作", status.HTTP_403_FORBIDDEN, 40300) from exc
    except TodoConflictError as exc:
        raise APIException("当前待办状态不允许执行该操作", status.HTTP_409_CONFLICT, 40900) from exc
    if todo is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="待办事项",
        operation_type="cancel",
        business_id=todo_id,
        request=request,
    )
    db.commit()
    return success(todo_dict(todo), "待办已取消")
