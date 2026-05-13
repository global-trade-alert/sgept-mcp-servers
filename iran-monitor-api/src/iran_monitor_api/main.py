"""FastAPI entry point.

Run with: `iran-monitor-api` (uvicorn under the hood).
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from a2a_protocol import create_app as create_a2a_app
from a2a_protocol.card import build_card_router
from a2a_protocol.jsonrpc import build_jsonrpc_router
from a2a_protocol.sse import build_sse_router

from . import db
from .api.routes import router
from .backend import IranMonitorBackend
from .config import get_settings
from .errors import APIError

# Process-wide backend instance so the worker can publish events to the same
# event bus the SSE endpoint subscribes against.
_backend: IranMonitorBackend | None = None


def get_backend() -> IranMonitorBackend:
    global _backend
    if _backend is None:
        _backend = IranMonitorBackend()
    return _backend


def create_app() -> FastAPI:
    settings = get_settings()
    db.init_db()

    backend = get_backend()

    app = FastAPI(
        title="Iran Monitor Inference API",
        version="0.1.0",
        description=(
            "Queryable inference for novel scenarios. A2A-native + REST. "
            "See ONBOARDING.md and design doc."
        ),
    )

    # Existing REST routes (back-compat for the named pilot buyer)
    app.include_router(router)

    # A2A protocol surface — agent card, JSON-RPC dispatcher, SSE streaming
    app.include_router(build_card_router(backend.agent_card))
    app.include_router(build_jsonrpc_router(backend))
    app.include_router(build_sse_router(backend))

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
