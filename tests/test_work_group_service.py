from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import User, WorkGroupMember
from app.models import __all__ as _model_exports
from app.schemas.work_group_schema import (
    WorkGroupCreate,
    WorkGroupMemberCreate,
    WorkGroupMemberUpdate,
    WorkGroupUpdate,
)
from app.services.work_group_service import (
    WorkGroupConflictError,
    WorkGroupNotFoundError,
    WorkGroupService,
)

_ = _model_exports
DEFAULT_HASH = "md5$e10adc3949ba59abbe56e057f20f883e"


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        session.add_all(
            [
                User(
                    id=1,
                    username="admin",
                    password_hash=DEFAULT_HASH,
                    real_name="管理员",
                    role="admin",
                    status=1,
                ),
                User(
                    id=2,
                    username="it_zhang",
                    password_hash=DEFAULT_HASH,
                    real_name="张工",
                    role="it_staff",
                    phone="13800000002",
                    status=1,
                ),
                User(
                    id=3,
                    username="disabled",
                    password_hash=DEFAULT_HASH,
                    real_name="禁用用户",
                    role="it_staff",
                    status=0,
                ),
            ]
        )
        session.commit()
        yield session
    finally:
        session.close()
        engine.dispose()


def test_create_work_group_validates_unique_code_and_leader(db_session: Session) -> None:
    service = WorkGroupService(db_session)

    group = service.create_work_group(
        WorkGroupCreate(
            group_name="桌面运维组",
            group_code="desktop",
            leader_id=2,
            sort_order=10,
        )
    )
    db_session.commit()

    assert group.id is not None
    assert group.leader_name == "张工"
    assert group.member_count == 0

    with pytest.raises(WorkGroupConflictError):
        service.create_work_group(
            WorkGroupCreate(group_name="重复组", group_code="desktop")
        )

    with pytest.raises(WorkGroupNotFoundError):
        service.create_work_group(
            WorkGroupCreate(group_name="未知组长", group_code="unknown", leader_id=999)
        )


def test_add_member_rejects_duplicate_and_reactivates_disabled_relation(
    db_session: Session,
) -> None:
    service = WorkGroupService(db_session)
    group = service.create_work_group(
        WorkGroupCreate(group_name="网络运维组", group_code="network")
    )

    member = service.add_group_member(
        group_id=group.id,
        payload=WorkGroupMemberCreate(user_id=2, member_role="member"),
    )
    db_session.commit()

    assert member.status == 1

    with pytest.raises(WorkGroupConflictError):
        service.add_group_member(
            group_id=group.id,
            payload=WorkGroupMemberCreate(user_id=2, member_role="leader"),
        )

    service.remove_group_member(group_id=group.id, user_id=2)
    reactivated = service.add_group_member(
        group_id=group.id,
        payload=WorkGroupMemberCreate(user_id=2, member_role="leader"),
    )
    db_session.commit()

    assert reactivated.id == member.id
    assert reactivated.status == 1
    assert reactivated.member_role == "leader"
    assert db_session.query(WorkGroupMember).count() == 1


def test_add_member_requires_enabled_group_and_enabled_user(db_session: Session) -> None:
    service = WorkGroupService(db_session)
    group = service.create_work_group(
        WorkGroupCreate(group_name="账号组", group_code="account", status=0)
    )

    with pytest.raises(WorkGroupNotFoundError):
        service.add_group_member(
            group_id=group.id,
            payload=WorkGroupMemberCreate(user_id=2),
        )

    enabled_group = service.create_work_group(
        WorkGroupCreate(group_name="打印机组", group_code="printer")
    )
    with pytest.raises(WorkGroupNotFoundError):
        service.add_group_member(
            group_id=enabled_group.id,
            payload=WorkGroupMemberCreate(user_id=3),
        )


def test_disabling_group_disables_active_members(db_session: Session) -> None:
    service = WorkGroupService(db_session)
    group = service.create_work_group(
        WorkGroupCreate(group_name="网络运维组", group_code="network")
    )
    member = service.add_group_member(
        group_id=group.id,
        payload=WorkGroupMemberCreate(user_id=2),
    )

    service.update_work_group(group.id, WorkGroupUpdate(status=0))
    db_session.commit()

    db_session.refresh(group)
    db_session.refresh(member)
    assert group.status == 0
    assert member.status == 0


def test_remove_leader_member_clears_group_leader(db_session: Session) -> None:
    service = WorkGroupService(db_session)
    group = service.create_work_group(
        WorkGroupCreate(group_name="网络运维组", group_code="network", leader_id=2)
    )
    member = service.add_group_member(
        group_id=group.id,
        payload=WorkGroupMemberCreate(user_id=2, member_role="leader"),
    )

    removed = service.remove_group_member(group_id=group.id, user_id=2)
    db_session.commit()

    db_session.refresh(group)
    db_session.refresh(member)
    assert removed is True
    assert group.leader_id is None
    assert member.status == 0


def test_list_members_defaults_to_enabled_and_supports_keyword(
    db_session: Session,
) -> None:
    service = WorkGroupService(db_session)
    group = service.create_work_group(
        WorkGroupCreate(group_name="网络运维组", group_code="network")
    )
    service.add_group_member(
        group_id=group.id,
        payload=WorkGroupMemberCreate(user_id=2, member_role="leader"),
    )
    db_session.add(
        WorkGroupMember(group_id=group.id, user_id=1, member_role="member", status=0)
    )
    db_session.commit()

    items, total = service.list_group_members(group_id=group.id, keyword="张")

    assert total == 1
    assert len(items) == 1
    assert items[0].user.username == "it_zhang"


def test_update_member_validates_existing_relation(db_session: Session) -> None:
    service = WorkGroupService(db_session)
    group = service.create_work_group(
        WorkGroupCreate(group_name="网络运维组", group_code="network")
    )

    assert (
        service.update_group_member(
            group_id=group.id,
            user_id=999,
            payload=WorkGroupMemberUpdate(status=0),
        )
        is None
    )
