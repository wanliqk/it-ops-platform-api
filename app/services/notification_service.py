from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Notification


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_notification(
        self,
        *,
        user_id: int,
        title: str,
        content: str,
        biz_type: str,
        biz_id: int | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            content=content,
            biz_type=biz_type,
            biz_id=biz_id,
        )
        self.db.add(notification)
        self.db.flush()
        return notification

    def list_current_user_notifications(
        self,
        *,
        user_id: int,
        read_status: int | None = None,
        biz_type: str | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Notification], int]:
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.deleted == 0,
        )
        if read_status is not None:
            stmt = stmt.where(Notification.read_status == read_status)
        if biz_type:
            stmt = stmt.where(Notification.biz_type == biz_type)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(or_(Notification.title.like(like), Notification.content.like(like)))

        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(Notification.created_at.desc(), Notification.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def unread_count(self, user_id: int) -> int:
        return self.db.scalar(
            select(func.count()).where(
                Notification.user_id == user_id,
                Notification.read_status == 0,
                Notification.deleted == 0,
            )
        ) or 0

    def get_current_user_notification(
        self,
        *,
        notification_id: int,
        user_id: int,
    ) -> Notification | None:
        return self.db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.deleted == 0,
            )
        )

    def mark_read(self, *, notification_id: int, user_id: int) -> Notification | None:
        notification = self.get_current_user_notification(
            notification_id=notification_id,
            user_id=user_id,
        )
        if notification is None:
            return None
        if notification.read_status == 0:
            notification.read_status = 1
            notification.read_at = datetime.now(UTC)
        self.db.flush()
        return notification

    def mark_read_batch(self, *, ids: list[int], user_id: int) -> int:
        notifications = self._list_mutable_notifications(ids=ids, user_id=user_id)
        now = datetime.now(UTC)
        processed_count = 0
        for notification in notifications:
            if notification.read_status == 0:
                notification.read_status = 1
                notification.read_at = now
                processed_count += 1
        self.db.flush()
        return processed_count

    def mark_all_read(self, user_id: int) -> int:
        notifications = list(
            self.db.scalars(
                select(Notification).where(
                    Notification.user_id == user_id,
                    Notification.read_status == 0,
                    Notification.deleted == 0,
                )
            )
        )
        now = datetime.now(UTC)
        for notification in notifications:
            notification.read_status = 1
            notification.read_at = now
        self.db.flush()
        return len(notifications)

    def delete_one(self, *, notification_id: int, user_id: int) -> Notification | None:
        notification = self.get_current_user_notification(
            notification_id=notification_id,
            user_id=user_id,
        )
        if notification is None:
            return None
        notification.deleted = 1
        self.db.flush()
        return notification

    def delete_batch(self, *, ids: list[int], user_id: int) -> int:
        notifications = self._list_mutable_notifications(ids=ids, user_id=user_id)
        processed_count = 0
        for notification in notifications:
            if notification.deleted == 0:
                notification.deleted = 1
                processed_count += 1
        self.db.flush()
        return processed_count

    def _list_mutable_notifications(self, *, ids: list[int], user_id: int) -> list[Notification]:
        unique_ids = list(dict.fromkeys(ids))
        if not unique_ids:
            return []
        return list(
            self.db.scalars(
                select(Notification).where(
                    Notification.id.in_(unique_ids),
                    Notification.user_id == user_id,
                    Notification.deleted == 0,
                )
            )
        )


def create_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    content: str,
    biz_type: str,
    biz_id: int | None = None,
) -> Notification:
    return NotificationService(db).create_notification(
        user_id=user_id,
        title=title,
        content=content,
        biz_type=biz_type,
        biz_id=biz_id,
    )