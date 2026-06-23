from fastapi import APIRouter

from app.api.v1.routes import (
    asset_categories,
    assets,
    auth,
    dashboard,
    dicts,
    health,
    operation_logs,
    repair_records,
    tickets,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    asset_categories.router,
    prefix="/asset-categories",
    tags=["asset-categories"],
)
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(repair_records.router, prefix="/repair-records", tags=["repair-records"])
api_router.include_router(operation_logs.router, prefix="/operation-logs", tags=["operation-logs"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(dicts.router, prefix="/dicts", tags=["dicts"])
