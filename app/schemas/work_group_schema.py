from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

MemberRole = Literal["leader", "member"]


class WorkGroupBase(BaseModel):
    group_name: str
    group_code: str
    description: str | None = None
    leader_id: int | None = None
    status: int = 1
    sort_order: int = 0

    @field_validator("group_name", "group_code")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("字段不能为空")
        return value.strip()

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: int) -> int:
        if value not in {0, 1}:
            raise ValueError("status 只能为 1 或 0")
        return value


class WorkGroupCreate(WorkGroupBase):
    pass


class WorkGroupUpdate(BaseModel):
    group_name: str | None = None
    group_code: str | None = None
    description: str | None = None
    leader_id: int | None = None
    status: int | None = None
    sort_order: int | None = None

    @field_validator("group_name", "group_code")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("字段不能为空")
        return value.strip() if value is not None else value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: int | None) -> int | None:
        if value is not None and value not in {0, 1}:
            raise ValueError("status 只能为 1 或 0")
        return value


class WorkGroupQuery(BaseModel):
    keyword: str | None = None
    status: int | None = None


class WorkGroupResponse(BaseModel):
    id: int
    group_name: str
    group_code: str
    description: str | None = None
    leader_id: int | None = None
    leader_name: str | None = None
    status: int
    sort_order: int
    member_count: int
    created_at: datetime
    updated_at: datetime


class WorkGroupDetailResponse(WorkGroupResponse):
    pass


class WorkGroupMemberCreate(BaseModel):
    user_id: int
    member_role: MemberRole = "member"


class WorkGroupMemberUpdate(BaseModel):
    member_role: MemberRole | None = None
    status: int | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: int | None) -> int | None:
        if value is not None and value not in {0, 1}:
            raise ValueError("status 只能为 1 或 0")
        return value


class WorkGroupMemberQuery(BaseModel):
    keyword: str | None = None
    status: int | None = 1


class WorkGroupMemberResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    username: str
    real_name: str
    phone: str | None = None
    member_role: str
    status: int
    joined_at: datetime
    created_at: datetime
    updated_at: datetime
