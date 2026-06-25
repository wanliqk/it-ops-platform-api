from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TodoStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TodoPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TodoType(StrEnum):
    TICKET_ASSIGN = "ticket_assign"
    TICKET_ACCEPT = "ticket_accept"
    TICKET_PROCESS = "ticket_process"
    TICKET_CONFIRM = "ticket_confirm"
    ASSET_APPROVAL = "asset_approval"
    ASSET_INVENTORY = "asset_inventory"


class Todo(Base):
    __tablename__ = "sys_todo"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        index=True,
    )
    todo_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(String(500))
    todo_type: Mapped[TodoType] = mapped_column(String(50), index=True)
    business_type: Mapped[str] = mapped_column(String(50), index=True)
    business_id: Mapped[int] = mapped_column(BigInteger, index=True)
    assignee_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("sys_user.id"),
        default=None,
        index=True,
    )
    assignee_name: Mapped[str | None] = mapped_column(String(50), default=None)
    status: Mapped[TodoStatus] = mapped_column(
        String(30),
        default=TodoStatus.PENDING,
        index=True,
    )
    priority: Mapped[TodoPriority] = mapped_column(
        String(20),
        default=TodoPriority.NORMAL,
        index=True,
    )
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    reminded_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    expire_notice_sent: Mapped[int] = mapped_column(SmallInteger, default=0)
    remark: Mapped[str | None] = mapped_column(Text, default=None)
    created_by: Mapped[int | None] = mapped_column(BigInteger, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0, index=True)

    assignee = relationship("User")
