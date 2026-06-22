from fastapi import APIRouter

from app.api.mobile.routes import assets, auth, faqs, home, tickets

mobile_router = APIRouter()
mobile_router.include_router(auth.router, prefix="/auth", tags=["mobile-auth"])
mobile_router.include_router(home.router, prefix="/home", tags=["mobile-home"])
mobile_router.include_router(tickets.router, prefix="/tickets", tags=["mobile-tickets"])
mobile_router.include_router(assets.router, prefix="/assets", tags=["mobile-assets"])
mobile_router.include_router(faqs.router, prefix="/faqs", tags=["mobile-faqs"])
