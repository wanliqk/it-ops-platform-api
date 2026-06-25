from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkGroupMemberRole(StrEnum):
    LEADER = "leader"
    MEMBER = "member"


class WorkGroup(Base):
    __tablename__ = "it_work_group"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        index=True,
    )
    group_name: Mapped[str] = mapped_column(String(100))
    group_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255), default=None)
    leader_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("sys_user.id"),
        default=None,
        index=True,
    )
    status: Mapped[int] = mapped_column(SmallInteger, default=1, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    leader = relationship("User")
    members = relationship(
        "WorkGroupMember",
        back_populates="group",
        cascade="all, delete-orphan",
    )


class WorkGroupMember(Base):
    __tablename__ = "it_work_group_member"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        index=True,
    )
    group_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("it_work_group.id"),
        index=True,
    )
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), index=True)
    member_role: Mapped[WorkGroupMemberRole] = mapped_column(
        String(30),
        default=WorkGroupMemberRole.MEMBER,
    )
    status: Mapped[int] = mapped_column(SmallInteger, default=1, index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    group = relationship("WorkGroup", back_populates="members")
    user = relationship("User")
