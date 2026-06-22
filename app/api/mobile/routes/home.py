from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.mobile.deps import DBSession, get_current_mobile_user
from app.core.responses import success_response
from app.models import User
from app.schemas.mobile import MobileResponse, TicketSummaryData
from app.services.mobile_service import MobileTicketService

router = APIRouter()
CurrentUser = Annotated[User, Depends(get_current_mobile_user)]


@router.get("/summary", response_model=MobileResponse[TicketSummaryData])
def summary(current_user: CurrentUser, db: DBSession) -> dict:
    return success_response(MobileTicketService(db).summary(current_user))
