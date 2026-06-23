from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class UserBase(BaseModel):
    username: str
    real_name: str
    role: UserRole = UserRole.EMPLOYEE
    department: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    status: int = 1


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


class UserStatusUpdate(BaseModel):
    status: int


class UserPasswordReset(BaseModel):
    new_password: str


class UserPasswordChange(BaseModel):
    old_password: str
    new_password: str


class UserRead(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
