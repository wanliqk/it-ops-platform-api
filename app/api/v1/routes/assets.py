from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.v1.deps import DBSession, require_permissions
from app.api.v1.routes._serializers import asset_dict, repair_record_dict
from app.core.responses import APIException, success
from app.models import User
from app.schemas.asset import AssetCreate, AssetStatusUpdate, AssetUpdate
from app.schemas.common import page_data
from app.services.asset_service import AssetService
from app.services.log_service import LogService
from app.services.repair_service import RepairService

router = APIRouter()
AssetReader = Annotated[User, Depends(require_permissions("asset:view"))]
AssetCreator = Annotated[User, Depends(require_permissions("asset:create"))]
AssetUpdater = Annotated[User, Depends(require_permissions("asset:update"))]
AssetStatusUpdater = Annotated[User, Depends(require_permissions("asset:status"))]
AssetDeleter = Annotated[User, Depends(require_permissions("asset:delete"))]
AssetRepairReader = Annotated[User, Depends(require_permissions("asset:repair_records"))]


@router.get("")
def list_assets(
    db: DBSession,
    _: AssetReader,
    keyword: str | None = None,
    category_id: int | None = None,
    status_value: Annotated[str | None, Query(alias="status")] = None,
    department: str | None = None,
    user_id: int | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    items, total = AssetService(db).list(
        keyword=keyword,
        category_id=category_id,
        status=status_value,
        department=department,
        user_id=user_id,
        page=page,
        page_size=page_size,
    )
    return success(page_data([asset_dict(item) for item in items], total, page, page_size))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate,
    db: DBSession,
    request: Request,
    current_user: AssetCreator,
) -> dict:
    service = AssetService(db)
    if service.get_by_asset_no(payload.asset_no):
        raise APIException("资产编号已存在", status.HTTP_409_CONFLICT, 40900)
    if not service.category_exists(payload.category_id):
        raise APIException("资产分类不存在", status.HTTP_404_NOT_FOUND, 40400)
    if not service.user_exists(payload.user_id):
        raise APIException("使用人不存在", status.HTTP_404_NOT_FOUND, 40400)
    asset = service.create(payload)
    LogService(db).record(
        user_id=current_user.id,
        module_name="资产管理",
        operation_type="create",
        business_id=asset.id,
        request=request,
    )
    db.commit()
    return success({"id": asset.id, "asset_no": asset.asset_no}, "资产创建成功")


@router.get("/{asset_id}")
def get_asset(asset_id: int, db: DBSession, _: AssetReader) -> dict:
    asset = AssetService(db).get(asset_id)
    if asset is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    return success(asset_dict(asset))


@router.put("/{asset_id}")
def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    db: DBSession,
    request: Request,
    current_user: AssetUpdater,
) -> dict:
    service = AssetService(db)
    if payload.category_id is not None and not service.category_exists(payload.category_id):
        raise APIException("资产分类不存在", status.HTTP_404_NOT_FOUND, 40400)
    if not service.user_exists(payload.user_id):
        raise APIException("使用人不存在", status.HTTP_404_NOT_FOUND, 40400)
    asset = service.update(asset_id, payload)
    if asset is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="资产管理",
        operation_type="update",
        business_id=asset_id,
        request=request,
    )
    db.commit()
    return success(None, "资产修改成功")


@router.patch("/{asset_id}/status")
def update_asset_status(
    asset_id: int,
    payload: AssetStatusUpdate,
    db: DBSession,
    request: Request,
    current_user: AssetStatusUpdater,
) -> dict:
    asset = AssetService(db).update_status(asset_id, payload.status, payload.remark)
    if asset is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="资产管理",
        operation_type="update_status",
        business_id=asset_id,
        request=request,
    )
    db.commit()
    return success(None, "资产状态修改成功")


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    db: DBSession,
    request: Request,
    current_user: AssetDeleter,
) -> dict:
    service = AssetService(db)
    if service.get(asset_id) is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    if service.has_tickets_or_repairs(asset_id):
        raise APIException("资产已关联工单或维修记录", status.HTTP_409_CONFLICT, 40900)
    service.delete(asset_id)
    LogService(db).record(
        user_id=current_user.id,
        module_name="资产管理",
        operation_type="delete",
        business_id=asset_id,
        request=request,
    )
    db.commit()
    return success(None, "资产删除成功")


@router.get("/{asset_id}/repair-records")
def asset_repair_records(
    asset_id: int,
    db: DBSession,
    _: AssetRepairReader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    if AssetService(db).get(asset_id) is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    items, total = RepairService(db).list(asset_id=asset_id, page=page, page_size=page_size)
    return success(page_data([repair_record_dict(item) for item in items], total, page, page_size))
