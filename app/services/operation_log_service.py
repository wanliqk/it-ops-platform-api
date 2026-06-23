from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import OperationLog


class OperationLogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        *,
        user_id: int | None = None,
        module_name: str | None = None,
        operation_type: str | None = None,
        operation_result: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[OperationLog], int]:
        stmt = select(OperationLog)
        if user_id is not None:
            stmt = stmt.where(OperationLog.user_id == user_id)
        if module_name:
            stmt = stmt.where(OperationLog.module_name == module_name)
        if operation_type:
            stmt = stmt.where(OperationLog.operation_type == operation_type)
        if operation_result:
            stmt = stmt.where(OperationLog.operation_result == operation_result)
        if start_date:
            stmt = stmt.where(OperationLog.created_at >= datetime.combine(start_date, time.min))
        if end_date:
            stmt = stmt.where(OperationLog.created_at <= datetime.combine(end_date, time.max))
        total = len(list(self.db.scalars(stmt)))
        items = list(
            self.db.scalars(
                stmt.order_by(OperationLog.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total
