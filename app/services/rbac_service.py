from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.models import SysPermission, SysRole, SysRolePermission, SysUserRole, User
from app.schemas.rbac_schema import RoleCreate, RoleUpdate


class RbacService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_roles(
        self,
        *,
        keyword: str | None = None,
        status: int | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[SysRole], int]:
        stmt = select(SysRole)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(or_(SysRole.role_code.like(like), SysRole.role_name.like(like)))
        if status is not None:
            stmt = stmt.where(SysRole.status == status)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        roles = list(
            self.db.scalars(
                stmt.order_by(SysRole.sort_order.asc(), SysRole.id.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return roles, total

    def get_role(self, role_id: int) -> SysRole | None:
        return self.db.get(SysRole, role_id)

    def get_role_by_code(self, role_code: str) -> SysRole | None:
        return self.db.scalar(select(SysRole).where(SysRole.role_code == role_code))

    def create_role(self, payload: RoleCreate) -> SysRole:
        role = SysRole(**payload.model_dump())
        self.db.add(role)
        self.db.flush()
        return role

    def update_role(self, role_id: int, payload: RoleUpdate) -> SysRole | None:
        role = self.get_role(role_id)
        if role is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(role, field, value)
        self.db.flush()
        return role

    def update_role_status(self, role_id: int, status: int) -> SysRole | None:
        role = self.get_role(role_id)
        if role is None:
            return None
        role.status = status
        self.db.flush()
        return role

    def role_has_bindings(self, role_id: int) -> bool:
        user_role = self.db.scalar(
            select(SysUserRole.id).where(SysUserRole.role_id == role_id).limit(1)
        )
        role_permission = self.db.scalar(
            select(SysRolePermission.id).where(SysRolePermission.role_id == role_id).limit(1)
        )
        return user_role is not None or role_permission is not None

    def delete_role(self, role_id: int) -> bool:
        role = self.get_role(role_id)
        if role is None:
            return False
        self.db.delete(role)
        self.db.flush()
        return True

    def list_permissions(
        self,
        *,
        keyword: str | None = None,
        module_name: str | None = None,
        status: int | None = None,
    ) -> list[SysPermission]:
        stmt = select(SysPermission)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    SysPermission.permission_code.like(like),
                    SysPermission.permission_name.like(like),
                )
            )
        if module_name:
            stmt = stmt.where(SysPermission.module_name == module_name)
        if status is not None:
            stmt = stmt.where(SysPermission.status == status)
        return list(
            self.db.scalars(
                stmt.order_by(
                    SysPermission.module_name.asc(),
                    SysPermission.sort_order.asc(),
                    SysPermission.id.asc(),
                )
            )
        )

    def get_role_permissions(self, role_id: int) -> list[SysPermission]:
        stmt = (
            select(SysPermission)
            .join(SysRolePermission, SysRolePermission.permission_id == SysPermission.id)
            .where(SysRolePermission.role_id == role_id)
            .order_by(SysPermission.module_name.asc(), SysPermission.sort_order.asc())
        )
        return list(self.db.scalars(stmt))

    def set_role_permissions(self, role_id: int, permission_ids: list[int]) -> list[SysPermission]:
        ids = sorted(set(permission_ids))
        permissions = list(
            self.db.scalars(select(SysPermission).where(SysPermission.id.in_(ids)))
        ) if ids else []
        if len(permissions) != len(ids):
            raise ValueError("权限不存在")
        self.db.execute(delete(SysRolePermission).where(SysRolePermission.role_id == role_id))
        self.db.add_all(
            [
                SysRolePermission(role_id=role_id, permission_id=permission_id)
                for permission_id in ids
            ]
        )
        self.db.flush()
        return permissions

    def get_user_roles(self, user_id: int) -> list[SysRole]:
        stmt = (
            select(SysRole)
            .join(SysUserRole, SysUserRole.role_id == SysRole.id)
            .where(SysUserRole.user_id == user_id)
            .order_by(SysRole.sort_order.asc(), SysRole.id.asc())
        )
        return list(self.db.scalars(stmt))

    def set_user_roles(self, user_id: int, role_ids: list[int]) -> list[SysRole]:
        ids = sorted(set(role_ids))
        roles = list(self.db.scalars(select(SysRole).where(SysRole.id.in_(ids)))) if ids else []
        if len(roles) != len(ids):
            raise ValueError("角色不存在")
        self.db.execute(delete(SysUserRole).where(SysUserRole.user_id == user_id))
        self.db.add_all([SysUserRole(user_id=user_id, role_id=role_id) for role_id in ids])
        self.db.flush()
        return roles

    def user_exists(self, user_id: int) -> bool:
        return self.db.get(User, user_id) is not None
