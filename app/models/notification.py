from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Notification(Base):
    __tablename__ = "it_notification"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(String(500))
    biz_type: Mapped[str] = mapped_column(String(50), index=True)
    biz_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    read_status: Mapped[int] = mapped_column(SmallInteger, default=0, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    deleted: Mapped[int] = mapped_column(SmallInteger, default=0, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="notifications")