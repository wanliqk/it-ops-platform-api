from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.mobile.deps import DBSession, get_current_mobile_user
from app.core.responses import success_response
from app.models import FaqCategory, User
from app.schemas.mobile import FaqDetail, FaqListItem, MobileResponse, OptionItem, PageData
from app.services.mobile_service import MobileFaqService

router = APIRouter()
CurrentUser = Annotated[User, Depends(get_current_mobile_user)]


@router.get("/categories", response_model=MobileResponse[list[OptionItem]])
def categories(current_user: CurrentUser) -> dict:
    _ = current_user
    return success_response(
        [
            OptionItem(value=FaqCategory.COMPUTER, label="电脑问题"),
            OptionItem(value=FaqCategory.NETWORK, label="网络问题"),
            OptionItem(value=FaqCategory.PRINTER, label="打印机问题"),
            OptionItem(value=FaqCategory.ACCOUNT, label="账号系统"),
            OptionItem(value=FaqCategory.OTHER, label="其他问题"),
        ]
    )


@router.get("", response_model=MobileResponse[PageData[FaqListItem]])
def list_faqs(
    current_user: CurrentUser,
    db: DBSession,
    category: Annotated[FaqCategory | None, Query()] = None,
    keyword: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    _ = current_user
    items, total = MobileFaqService(db).list(page, page_size, category, keyword)
    return success_response(
        PageData[FaqListItem](
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/{faq_id}", response_model=MobileResponse[FaqDetail])
def faq_detail(faq_id: int, current_user: CurrentUser, db: DBSession) -> dict:
    _ = current_user
    return success_response(MobileFaqService(db).detail(faq_id))
