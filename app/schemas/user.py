from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserBase(BaseModel):
    username: str
    real_name: str
    role: UserRole = UserRole.EMPLOYEE
    department: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    status: int = 1

    @field_validator("department", "phone", "email", mode="before")
    @classmethod
    def empty_date_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value

class UserCreate(UserBase):
    password: str


class UserCreateDB(UserBase):
    password_hash: str


class UserUpdate(BaseModel):
    real_name: str | None = None
    role: UserRole | None = None
    department: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    status: int | None = None

    @field_validator("department", "phone", "email", mode="before")
    @classmethod
    def empty_date_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value


class UserStatusUpdate(BaseModel):
    status: int


class UserPasswordReset(BaseModel):
    new_password: str


class UserPasswordChange(BaseModel):
    old_password: str
    new_password: str


class UserBatchDeleteRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1, max_length=100)


class UserBatchDeleteFailedItem(BaseModel):
    id: int
    reason: str


class UserBatchDeleteResult(BaseModel):
    deleted_count: int
    failed_items: list[UserBatchDeleteFailedItem]


class UserRead(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)