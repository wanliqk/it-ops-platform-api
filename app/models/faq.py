from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FaqCategory(StrEnum):
    COMPUTER = "computer"
    NETWORK = "network"
    PRINTER = "printer"
    ACCOUNT = "account"
    OTHER = "other"


class Faq(Base):
    __tablename__ = "it_faq"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[FaqCategory] = mapped_column(String(50))
    summary: Mapped[str | None] = mapped_column(String(255), default=None)
    content: Mapped[str] = mapped_column(Text)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
