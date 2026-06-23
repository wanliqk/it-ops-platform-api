from fastapi import Request
from sqlalchemy.orm import Session

from app.models import OperationLog, OperationResult


class LogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        user_id: int | None,
        module_name: str,
        operation_type: str,
        business_id: int | None = None,
        request: Request | None = None,
        operation_result: OperationResult = OperationResult.SUCCESS,
        error_message: str | None = None,
    ) -> None:
        self.db.add(
            OperationLog(
                user_id=user_id,
                module_name=module_name,
                operation_type=operation_type,
                business_id=business_id,
                request_method=request.method if request else None,
                request_url=str(request.url.path) if request else None,
                request_ip=request.client.host if request and request.client else None,
                operation_result=operation_result,
                error_message=error_message,
            )
        )
