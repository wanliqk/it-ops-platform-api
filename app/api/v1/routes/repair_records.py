from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.v1.deps import DBSession, require_roles
from app.api.v1.routes._serializers import repair_record_dict
from app.core.responses import APIException, success
from app.models import User
from app.schemas.common import page_data
from app.schemas.ticket import RepairRecordUpdate
from app.services.log_service import LogService
from app.services.repair_service import RepairService

router = APIRouter()
RepairReader = Annotated[User, Depends(require_roles("admin", "it_staff"))]
AdminUser = Annotated[User, Depends(require_roles("admin"))]


@router.get("")
def list_repair_records(
    db: DBSession,
    _: RepairReader,
    asset_id: int | None = None,
    ticket_id: int | None = None,
    repair_user_id: int | None = None,
    repair_result: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    items, total = RepairService(db).list(
        asset_id=asset_id,
        ticket_id=ticket_id,
        repair_user_id=repair_user_id,
        repair_result=repair_result,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return success(page_data([repair_record_dict(item) for item in items], total, page, page_size))


@router.get("/{record_id}")
def get_repair_record(record_id: int, db: DBSession, _: RepairReader) -> dict:
    record = RepairService(db).get(record_id)
    if record is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    return success(repair_record_dict(record))


@router.put("/{record_id}")
def update_repair_record(
    record_id: int,
    payload: RepairRecordUpdate,
    db: DBSession,
    request: Request,
    current_user: AdminUser,
) -> dict:
    record = RepairService(db).update(record_id, payload)
    if record is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="维修记录",
        operation_type="update",
        business_id=record_id,
        request=request,
    )
    db.commit()
    return success(None, "维修记录修改成功")
