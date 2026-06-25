from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

TodoStatusValue = Literal["pending", "processing", "completed", "cancelled", "expired"]
TodoPriorityValue = Literal["low", "normal", "high", "urgent"]
TodoTypeValue = Literal[
    "ticket_assign",
    "ticket_accept",
    "ticket_process",
    "ticket_confirm",
    "asset_approval",
    "asset_inventory",
]


class TodoCreate(BaseModel):
    title: str
    content: str
    todo_type: TodoTypeValue
    business_type: str
    business_id: int
    assignee_id: int
    priority: TodoPriorityValue = "normal"
    deadline_at: datetime | None = None
    remark: str | None = None
    created_by: int | None = None


class TodoStart(BaseModel):
    remark: str | None = None


class TodoComplete(BaseModel):
    remark: str | None = None


class TodoCancel(BaseModel):
    remark: str | None = None


class TodoRead(BaseModel):
    id: int
    todo_no: str
    title: str
    content: str
    todo_type: str
    business_type: str
    business_id: int
    assignee_id: int | None = None
    assignee_name: str | None = None
    status: str
    priority: str
    deadline_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    remark: str | None = None
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime
    business_title: str | None = None
    business_status: str | None = None


class TodoStatistics(BaseModel):
    pending_count: int
    processing_count: int
    expired_count: int
    today_deadline_count: int
    urgent_count: int


class TodoQuery(BaseModel):
    status: str | None = None
    todo_type: str | None = None
    business_type: str | None = None
    priority: str | None = None
    keyword: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in {
            "pending",
            "processing",
            "completed",
            "cancelled",
            "expired",
        }:
            raise ValueError("待办状态不合法")
        return value
