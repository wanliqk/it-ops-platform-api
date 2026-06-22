from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.mobile.deps import DBSession, get_current_mobile_user
from app.core.responses import success_response
from app.models import User
from app.schemas.mobile import MobileAssetOption, MobileResponse
from app.services.mobile_service import MobileAssetService

router = APIRouter()
CurrentUser = Annotated[User, Depends(get_current_mobile_user)]


@router.get("/options", response_model=MobileResponse[list[MobileAssetOption]])
def asset_options(
    current_user: CurrentUser,
    db: DBSession,
    keyword: str | None = Query(default=None),
) -> dict:
    assets = MobileAssetService(db).options(current_user, keyword)
    return success_response(assets)
