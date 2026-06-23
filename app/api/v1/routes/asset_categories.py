from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.v1.deps import DBSession, require_roles
from app.api.v1.routes._serializers import category_dict
from app.core.responses import APIException, success
from app.models import User
from app.schemas.asset import AssetCategoryCreate, AssetCategoryUpdate
from app.services.asset_service import AssetCategoryService
from app.services.log_service import LogService

router = APIRouter()
AssetReader = Annotated[User, Depends(require_roles("admin", "it_staff"))]
AdminUser = Annotated[User, Depends(require_roles("admin"))]


@router.get("")
def list_asset_categories(
    db: DBSession,
    _: AssetReader,
    keyword: str | None = None,
    status_value: Annotated[int | None, Query(alias="status")] = None,
) -> dict:
    categories = AssetCategoryService(db).list(keyword=keyword, status=status_value)
    return success([category_dict(category) for category in categories])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_asset_category(
    payload: AssetCategoryCreate,
    db: DBSession,
    request: Request,
    current_user: AdminUser,
) -> dict:
    service = AssetCategoryService(db)
    if service.get_by_code(payload.category_code):
        raise APIException("分类编码已存在", status.HTTP_409_CONFLICT, 40900)
    category = service.create(payload)
    LogService(db).record(
        user_id=current_user.id,
        module_name="资产分类",
        operation_type="create",
        business_id=category.id,
        request=request,
    )
    db.commit()
    return success({"id": category.id}, "资产分类创建成功")


@router.get("/{category_id}")
def get_asset_category(category_id: int, db: DBSession, _: AssetReader) -> dict:
    category = AssetCategoryService(db).get(category_id)
    if category is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    return success(category_dict(category))


@router.put("/{category_id}")
def update_asset_category(
    category_id: int,
    payload: AssetCategoryUpdate,
    db: DBSession,
    request: Request,
    current_user: AdminUser,
) -> dict:
    category = AssetCategoryService(db).update(category_id, payload)
    if category is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="资产分类",
        operation_type="update",
        business_id=category_id,
        request=request,
    )
    db.commit()
    return success(None, "资产分类修改成功")


@router.delete("/{category_id}")
def delete_asset_category(
    category_id: int,
    db: DBSession,
    request: Request,
    current_user: AdminUser,
) -> dict:
    service = AssetCategoryService(db)
    if service.get(category_id) is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    if service.has_assets(category_id):
        raise APIException("该分类已被资产使用", status.HTTP_409_CONFLICT, 40900)
    service.delete(category_id)
    LogService(db).record(
        user_id=current_user.id,
        module_name="资产分类",
        operation_type="delete",
        business_id=category_id,
        request=request,
    )
    db.commit()
    return success(None, "资产分类删除成功")
