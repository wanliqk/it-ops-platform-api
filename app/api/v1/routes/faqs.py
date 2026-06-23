from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.v1.deps import DBSession, get_current_user, require_roles
from app.api.v1.routes._serializers import faq_dict
from app.core.responses import APIException, success
from app.models import FaqCategory, User
from app.schemas.common import page_data
from app.schemas.faq import FaqCreate, FaqStatusUpdate, FaqUpdate
from app.services.faq_service import FaqService
from app.services.log_service import LogService

router = APIRouter()
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_roles("admin"))]


def _validate_status(status_value: int | None) -> None:
    if status_value is not None and status_value not in {0, 1}:
        raise APIException("status 只能为 1 或 0", status.HTTP_400_BAD_REQUEST, 40000)


@router.get("")
def list_faqs(
    db: DBSession,
    current_user: CurrentUser,
    keyword: str | None = None,
    category: FaqCategory | None = None,
    status_value: Annotated[int | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    _validate_status(status_value)
    items, total = FaqService(db).list(
        current_user=current_user,
        keyword=keyword,
        category=category,
        status=status_value,
        page=page,
        page_size=page_size,
    )
    return success(
        page_data(
            [faq_dict(item, include_content=False) for item in items],
            total,
            page,
            page_size,
        )
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_faq(
    payload: FaqCreate,
    db: DBSession,
    request: Request,
    current_user: AdminUser,
) -> dict:
    _validate_status(payload.status)
    faq = FaqService(db).create(payload)
    LogService(db).record(
        user_id=current_user.id,
        module_name="FAQ管理",
        operation_type="create",
        business_id=faq.id,
        request=request,
    )
    db.commit()
    return success({"id": faq.id}, "FAQ 创建成功")


@router.get("/category-stats")
def category_stats(db: DBSession, current_user: CurrentUser) -> dict:
    return success(FaqService(db).category_stats(current_user))


@router.get("/{faq_id}")
def get_faq(faq_id: int, db: DBSession, current_user: CurrentUser) -> dict:
    faq = FaqService(db).detail(faq_id, current_user)
    if faq is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    return success(faq_dict(faq))


@router.put("/{faq_id}")
def update_faq(
    faq_id: int,
    payload: FaqUpdate,
    db: DBSession,
    request: Request,
    current_user: AdminUser,
) -> dict:
    _validate_status(payload.status)
    faq = FaqService(db).update(faq_id, payload)
    if faq is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="FAQ管理",
        operation_type="update",
        business_id=faq_id,
        request=request,
    )
    db.commit()
    return success(None, "FAQ 修改成功")


@router.patch("/{faq_id}/status")
def update_faq_status(
    faq_id: int,
    payload: FaqStatusUpdate,
    db: DBSession,
    request: Request,
    current_user: AdminUser,
) -> dict:
    _validate_status(payload.status)
    faq = FaqService(db).update_status(faq_id, payload.status)
    if faq is None:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="FAQ管理",
        operation_type="update_status",
        business_id=faq_id,
        request=request,
    )
    db.commit()
    return success(None, "FAQ 状态修改成功")


@router.delete("/{faq_id}")
def delete_faq(faq_id: int, db: DBSession, request: Request, current_user: AdminUser) -> dict:
    deleted = FaqService(db).delete(faq_id)
    if not deleted:
        raise APIException("资源不存在", status.HTTP_404_NOT_FOUND, 40400)
    LogService(db).record(
        user_id=current_user.id,
        module_name="FAQ管理",
        operation_type="delete",
        business_id=faq_id,
        request=request,
    )
    db.commit()
    return success(None, "FAQ 删除成功")
