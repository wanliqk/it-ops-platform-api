from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import DBSession, get_current_user
from app.core.responses import APIException, success
from app.models import User
from app.schemas.common import page_data
from app.schemas.notification_schema import NotificationBatchRequest, NotificationRead
from app.services.notification_service import NotificationService

router = APIRouter()
CurrentUser = Annotated[User, Depends(get_current_user)]


def notification_dict(notification: object) -> dict:
    return NotificationRead.model_validate(notification).model_dump()


@router.get("")
def list_notifications(
    db: DBSession,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    read_status: Annotated[int | None, Query(ge=0, le=1)] = None,
    biz_type: str | None = None,
    keyword: str | None = None,
) -> dict:
    items, total = NotificationService(db).list_current_user_notifications(
        user_id=current_user.id,
        read_status=read_status,
        biz_type=biz_type,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return success(page_data([notification_dict(item) for item in items], total, page, page_size))


@router.get("/unread-count")
def unread_count(db: DBSession, current_user: CurrentUser) -> dict:
    return success({"unread_count": NotificationService(db).unread_count(current_user.id)})


@router.put("/read-batch")
def mark_notifications_read_batch(
    payload: NotificationBatchRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> dict:
    processed_count = NotificationService(db).mark_read_batch(
        ids=payload.ids,
        user_id=current_user.id,
    )
    db.commit()
    return success({"processed_count": processed_count}, "批量标记已读成功")


@router.put("/read-all")
def mark_all_notifications_read(db: DBSession, current_user: CurrentUser) -> dict:
    processed_count = NotificationService(db).mark_all_read(current_user.id)
    db.commit()
    return success({"processed_count": processed_count}, "全部标记已读成功")


@router.delete("/batch")
def delete_notifications_batch(
    payload: NotificationBatchRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> dict:
    processed_count = NotificationService(db).delete_batch(
        ids=payload.ids,
        user_id=current_user.id,
    )
    db.commit()
    return success({"processed_count": processed_count}, "批量删除成功")


@router.put("/{notification_id}/read")
def mark_notification_read(notification_id: int, db: DBSession, current_user: CurrentUser) -> dict:
    notification = NotificationService(db).mark_read(
        notification_id=notification_id,
        user_id=current_user.id,
    )
    if notification is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    db.commit()
    return success(notification_dict(notification), "标记已读成功")


@router.delete("/{notification_id}")
def delete_notification(notification_id: int, db: DBSession, current_user: CurrentUser) -> dict:
    notification = NotificationService(db).delete_one(
        notification_id=notification_id,
        user_id=current_user.id,
    )
    if notification is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    db.commit()
    return success(None, "通知删除成功")