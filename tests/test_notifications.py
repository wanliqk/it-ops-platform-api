from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import Notification, User
from app.models import __all__ as _model_exports
from app.services.notification_service import NotificationService, create_notification

_ = _model_exports


DEFAULT_HASH = "md5$e10adc3949ba59abbe56e057f20f883e"


def add_user(session: Session, user_id: int, username: str) -> None:
    session.add(
        User(
            id=user_id,
            username=username,
            password_hash=DEFAULT_HASH,
            real_name=username,
            role="employee",
            status=1,
        )
    )


def add_notification(
    session: Session,
    notification_id: int,
    user_id: int,
    title: str,
    read_status: int = 0,
    deleted: int = 0,
) -> None:
    session.add(
        Notification(
            id=notification_id,
            user_id=user_id,
            title=title,
            content=f"{title} content",
            biz_type="system",
            read_status=read_status,
            deleted=deleted,
        )
    )




@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        add_user(session, 1, "user_a")
        add_user(session, 2, "user_b")
        session.commit()
        yield session
    finally:
        session.close()
        engine.dispose()


def test_list_notifications_only_returns_current_user_visible_items(db_session: Session) -> None:
    add_notification(db_session, 1, 1, "my unread")
    add_notification(db_session, 2, 1, "my deleted", deleted=1)
    add_notification(db_session, 3, 2, "other user")
    db_session.commit()

    items, total = NotificationService(db_session).list_current_user_notifications(user_id=1)

    assert total == 1
    assert [item.id for item in items] == [1]


def test_unread_count_ignores_read_deleted_and_other_user_items(db_session: Session) -> None:
    add_notification(db_session, 1, 1, "unread")
    add_notification(db_session, 2, 1, "read", read_status=1)
    add_notification(db_session, 3, 1, "deleted", deleted=1)
    add_notification(db_session, 4, 2, "other")
    db_session.commit()

    assert NotificationService(db_session).unread_count(1) == 1


def test_mark_read_batch_ignores_missing_and_other_user_items(db_session: Session) -> None:
    add_notification(db_session, 1, 1, "mine")
    add_notification(db_session, 2, 2, "other")
    db_session.commit()

    processed_count = NotificationService(db_session).mark_read_batch(ids=[1, 2, 404], user_id=1)
    db_session.commit()

    assert processed_count == 1
    assert db_session.get(Notification, 1).read_status == 1
    assert db_session.get(Notification, 2).read_status == 0


def test_mark_all_read_only_updates_current_user_unread_items(db_session: Session) -> None:
    add_notification(db_session, 1, 1, "mine")
    add_notification(db_session, 2, 1, "already read", read_status=1)
    add_notification(db_session, 3, 2, "other")
    db_session.commit()

    processed_count = NotificationService(db_session).mark_all_read(1)
    db_session.commit()

    assert processed_count == 1
    assert db_session.get(Notification, 1).read_status == 1
    assert db_session.get(Notification, 3).read_status == 0


def test_delete_batch_logically_deletes_current_user_items(db_session: Session) -> None:
    add_notification(db_session, 1, 1, "mine")
    add_notification(db_session, 2, 2, "other")
    db_session.commit()

    processed_count = NotificationService(db_session).delete_batch(ids=[1, 2, 404], user_id=1)
    db_session.commit()

    assert processed_count == 1
    assert db_session.get(Notification, 1).deleted == 1
    assert db_session.get(Notification, 2).deleted == 0


def test_create_notification_helper(db_session: Session) -> None:
    notification = create_notification(
        db_session,
        user_id=1,
        title="helper title",
        content="helper content",
        biz_type="system",
    )
    db_session.commit()

    assert notification.id is not None
    assert notification.user_id == 1
