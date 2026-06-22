from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.mobile.router import mobile_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.responses import MobileAPIException, error_response


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    app.include_router(mobile_router, prefix="/api/mobile")

    @app.exception_handler(MobileAPIException)
    def mobile_api_exception_handler(
        request: Request,
        exc: MobileAPIException,
    ) -> JSONResponse:
        _ = request
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc.message, exc.code),
        )

    return app


app = create_app()
