"""FastAPI app factory.

Usage:
    from a2a_protocol import create_app
    from my_asset.backend import MyAssetBackend

    app = create_app(MyAssetBackend())

Mounts:
- GET  /.well-known/agent-card.json
- POST /v1/jsonrpc                  (message/send, tasks/get, tasks/cancel)
- POST /v1/jsonrpc/stream           (message/stream, tasks/resubscribe — SSE)
- GET  /healthz                     (liveness)

The backend supplies the business logic; the protocol package wires the
HTTP surface, error handling, and SSE framing.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from .backend import AgentBackend
from .card import build_card_router
from .errors import A2AError
from .jsonrpc import build_jsonrpc_router
from .sse import build_sse_router

logger = logging.getLogger(__name__)


def create_app(
    backend: AgentBackend,
    *,
    title: str | None = None,
    version: str | None = None,
) -> FastAPI:
    title = title or backend.agent_card.name
    version = version or backend.agent_card.version

    app = FastAPI(
        title=title,
        version=version,
        description=backend.agent_card.description,
        # Swagger doesn't model JSON-RPC well; we expose the agent card instead.
        docs_url=None,
        redoc_url=None,
    )

    app.include_router(build_card_router(backend.agent_card))
    app.include_router(build_jsonrpc_router(backend))
    app.include_router(build_sse_router(backend))

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> PlainTextResponse:
        return PlainTextResponse("ok")

    @app.exception_handler(A2AError)
    async def _a2a_error_handler(request: Request, exc: A2AError):  # noqa: ARG001
        # Reached for errors raised outside the JSON-RPC dispatcher (auth dep,
        # SSE endpoint). Inside the dispatcher we already catch and serialize.
        return JSONResponse(exc.to_jsonrpc(None), status_code=200)

    return app
