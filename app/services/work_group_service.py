from __future__ import annotations

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models import User, WorkGroup, WorkGroupMember
from app.schemas.work_group_schema import (
    WorkGroupCreate,
    WorkGroupMemberCreate,
    WorkGroupMemberUpdate,
    WorkGroupUpdate,
)
from app.utils.timezone import local_now


class WorkGroupConflictError(Exception):
    pass


class WorkGroupNotFoundError(Exception):
    pass


class WorkGroupService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_work_groups(
        self,
        *,
        keyword: str | None = None,
        status: int | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[WorkGroup], int]:
        stmt = select(WorkGroup)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                or_(WorkGroup.group_name.like(like), WorkGroup.group_code.like(like))
            )
        if status is not None:
            stmt = stmt.where(WorkGroup.status == status)

        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(WorkGroup.sort_order.asc(), WorkGroup.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        self._attach_group_extra(items)
        return items, total

    def get_work_group_detail(self, group_id: int) -> WorkGroup | None:
        group = self.db.get(WorkGroup, group_id)
        if group is not None:
            self._attach_group_extra([group])
        return group

    def create_work_group(self, payload: WorkGroupCreate) -> WorkGroup:
        self._ensure_unique_code(payload.group_code)
        self._ensure_user_exists(payload.leader_id)
        group = WorkGroup(**payload.model_dump())
        self.db.add(group)
        self.db.flush()
        self._attach_group_extra([group])
        return group

    def update_work_group(self, group_id: int, payload: WorkGroupUpdate) -> WorkGroup | None:
        group = self.db.get(WorkGroup, group_id)
        if group is None:
            return None

        data = payload.model_dump(exclude_unset=True)
        if "group_code" in data and data["group_code"] != group.group_code:
            self._ensure_unique_code(data["group_code"], exclude_group_id=group_id)
        if "leader_id" in data:
            self._ensure_user_exists(data["leader_id"])

        for field, value in data.items():
            setattr(group, field, value)

        if "status" in data and data["status"] == 0:
            for member in self._members(group_id):
                member.status = 0

        self.db.flush()
        self._attach_group_extra([group])
        return group

    def delete_work_group(self, group_id: int) -> bool:
        group = self.db.get(WorkGroup, group_id)
        if group is None:
            return False
        for member in self._members(group_id, include_disabled=True):
            self.db.delete(member)
        self.db.delete(group)
        self.db.flush()
        return True

    def list_group_members(
        self,
        *,
        group_id: int,
        keyword: str | None = None,
        status: int | None = 1,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[WorkGroupMember], int]:
        if self.db.get(WorkGroup, group_id) is None:
            raise WorkGroupNotFoundError

        stmt = (
            select(WorkGroupMember)
            .join(User, User.id == WorkGroupMember.user_id)
            .where(WorkGroupMember.group_id == group_id)
        )
        if status is not None:
            stmt = stmt.where(WorkGroupMember.status == status)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    User.username.like(like),
                    User.real_name.like(like),
                    User.phone.like(like),
                )
            )

        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(
                    case((WorkGroupMember.member_role == "leader", 0), else_=1).asc(),
                    WorkGroupMember.id.desc(),
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def add_group_member(
        self,
        *,
        group_id: int,
        payload: WorkGroupMemberCreate,
    ) -> WorkGroupMember:
        group = self.db.get(WorkGroup, group_id)
        if group is None or group.status != 1:
            raise WorkGroupNotFoundError
        user = self.db.get(User, payload.user_id)
        if user is None or user.status != 1:
            raise WorkGroupNotFoundError

        existing = self.db.scalar(
            select(WorkGroupMember).where(
                WorkGroupMember.group_id == group_id,
                WorkGroupMember.user_id == payload.user_id,
            )
        )
        if existing is not None:
            if existing.status == 1:
                raise WorkGroupConflictError
            existing.status = 1
            existing.member_role = payload.member_role
            existing.joined_at = local_now()
            self.db.flush()
            return existing

        member = WorkGroupMember(
            group_id=group_id,
            user_id=payload.user_id,
            member_role=payload.member_role,
            status=1,
            joined_at=local_now(),
        )
        self.db.add(member)
        self.db.flush()
        return member

    def update_group_member(
        self,
        *,
        group_id: int,
        user_id: int,
        payload: WorkGroupMemberUpdate,
    ) -> WorkGroupMember | None:
        member = self._member(group_id, user_id)
        if member is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(member, field, value)
        self.db.flush()
        return member

    def remove_group_member(self, *, group_id: int, user_id: int) -> bool:
        group = self.db.get(WorkGroup, group_id)
        member = self._member(group_id, user_id)
        if group is None or member is None:
            return False
        member.status = 0
        if group.leader_id == user_id:
            group.leader_id = None
        self.db.flush()
        return True

    def _ensure_unique_code(
        self,
        group_code: str,
        *,
        exclude_group_id: int | None = None,
    ) -> None:
        stmt = select(WorkGroup).where(WorkGroup.group_code == group_code)
        if exclude_group_id is not None:
            stmt = stmt.where(WorkGroup.id != exclude_group_id)
        if self.db.scalar(stmt) is not None:
            raise WorkGroupConflictError

    def _ensure_user_exists(self, user_id: int | None) -> None:
        if user_id is not None and self.db.get(User, user_id) is None:
            raise WorkGroupNotFoundError

    def _members(self, group_id: int, *, include_disabled: bool = False) -> list[WorkGroupMember]:
        stmt = select(WorkGroupMember).where(WorkGroupMember.group_id == group_id)
        if not include_disabled:
            stmt = stmt.where(WorkGroupMember.status == 1)
        return list(self.db.scalars(stmt))

    def _member(self, group_id: int, user_id: int) -> WorkGroupMember | None:
        return self.db.scalar(
            select(WorkGroupMember).where(
                WorkGroupMember.group_id == group_id,
                WorkGroupMember.user_id == user_id,
            )
        )

    def _attach_group_extra(self, groups: list[WorkGroup]) -> None:
        for group in groups:
            group.leader_name = group.leader.real_name if group.leader else None
            group.member_count = self.db.scalar(
                select(func.count()).where(
                    WorkGroupMember.group_id == group.id,
                    WorkGroupMember.status == 1,
                )
            ) or 0
