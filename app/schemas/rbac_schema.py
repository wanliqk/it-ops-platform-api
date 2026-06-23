from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RoleBase(BaseModel):
    role_code: str
    role_name: str
    description: str | None = None
    sort_order: int = 0
    status: int = 1


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    role_code: str | None = None
    role_name: str | None = None
    description: str | None = None
    sort_order: int | None = None
    status: int | None = None


class RoleStatusUpdate(BaseModel):
    status: int


class RoleRead(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PermissionRead(BaseModel):
    id: int
    permission_code: str
    permission_name: str
    module_name: str
    permission_type: str
    api_method: str | None = None
    api_path: str | None = None
    description: str | None = None
    sort_order: int
    status: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PermissionGroup(BaseModel):
    module_name: str
    permissions: list[PermissionRead]


class RolePermissionAssign(BaseModel):
    permission_ids: list[int]


class UserRoleAssign(BaseModel):
    role_ids: list[int]
