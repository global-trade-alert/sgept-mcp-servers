"""FastAPI entry point.

Run with: `iran-monitor-api` (uvicorn under the hood).
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import db
from .api.routes import router
from .config import get_settings
from .errors import APIError


def create_app() -> FastAPI:
    settings = get_settings()
    db.init_db()

    app = FastAPI(
        title="Iran Monitor Inference API",
        version="0.1.0",
        description="Queryable inference for novel scenarios. See README and design doc.",
    )
    app.include_router(router)

    @app.exception_handler(APIError)
    async def _api_error_handler(request: Request, exc: APIError):  # noqa: ARG001
        headers = {}
        if exc.code.value == "rate_limited" and "retry_after" in exc.extra:
            headers["Retry-After"] = str(exc.extra["retry_after"])
        return JSONResponse(exc.to_dict(), status_code=exc.http_status, headers=headers)

    return app


app = create_app()


def run() -> None:
    import uvicorn

    logging.basicConfig(
        level=os.environ.get("IRAN_API_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = get_settings()
    uvicorn.run(
        "iran_monitor_api.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=os.environ.get("IRAN_API_LOG_LEVEL", "info").lower(),
    )
