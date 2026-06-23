from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SysRole(Base):
    __tablename__ = "sys_role"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    role_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    role_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255), default=None)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user_roles = relationship("SysUserRole", back_populates="role", cascade="all, delete-orphan")
    role_permissions = relationship(
        "SysRolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
    )


class SysPermission(Base):
    __tablename__ = "sys_permission"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    permission_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    permission_name: Mapped[str] = mapped_column(String(100))
    module_name: Mapped[str] = mapped_column(String(100))
    permission_type: Mapped[str] = mapped_column(String(30), default="api")
    api_method: Mapped[str | None] = mapped_column(String(10), default=None)
    api_path: Mapped[str | None] = mapped_column(String(255), default=None)
    description: Mapped[str | None] = mapped_column(String(255), default=None)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    role_permissions = relationship(
        "SysRolePermission",
        back_populates="permission",
        cascade="all, delete-orphan",
    )


class SysUserRole(Base):
    __tablename__ = "sys_user_role"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_role.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="user_roles")
    role = relationship("SysRole", back_populates="user_roles")


class SysRolePermission(Base):
    __tablename__ = "sys_role_permission"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_role.id"))
    permission_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_permission.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    role = relationship("SysRole", back_populates="role_permissions")
    permission = relationship("SysPermission", back_populates="role_permissions")
