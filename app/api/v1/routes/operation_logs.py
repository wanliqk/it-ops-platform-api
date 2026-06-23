from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import DBSession, require_roles
from app.api.v1.routes._serializers import operation_log_dict
from app.core.responses import success
from app.models import User
from app.schemas.common import page_data
from app.services.operation_log_service import OperationLogService

router = APIRouter()
AdminUser = Annotated[User, Depends(require_roles("admin"))]


@router.get("")
def list_operation_logs(
    db: DBSession,
    _: AdminUser,
    user_id: int | None = None,
    module_name: str | None = None,
    operation_type: str | None = None,
    operation_result: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    items, total = OperationLogService(db).list(
        user_id=user_id,
        module_name=module_name,
        operation_type=operation_type,
        operation_result=operation_result,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return success(page_data([operation_log_dict(item) for item in items], total, page, page_size))
