"""SSE streaming for `message/stream` and `tasks/resubscribe`.

A2A spec: each event is a `TaskStatusUpdateEvent` or `TaskArtifactUpdateEvent`
serialized as JSON in an SSE `data:` field. The stream ends when a status
update has `final: true`.

We use sse-starlette for the framing (heartbeats, disconnect detection).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from .auth import make_bearer_dependency
from .backend import AgentBackend, AuthContext, TaskContext, TaskEvent
from .errors import A2AError, JSONRPCErrorCode
from .lifecycle import is_terminal
from .models import (
    Message,
    TaskID,
    TaskStatusUpdateEvent,
    new_context_id,
    new_task_id,
)

logger = logging.getLogger(__name__)


def build_sse_router(backend: AgentBackend) -> APIRouter:
    router = APIRouter()
    require_auth = make_bearer_dependency(backend)

    @router.post("/v1/jsonrpc/stream")
    async def jsonrpc_stream(
        request: Request,
        auth: AuthContext = Depends(require_auth),
    ) -> EventSourceResponse:
        """A2A spec routes `message/stream` and `tasks/resubscribe` to a
        streaming endpoint. We expose both via the same path; the JSON-RPC
        method tells us which.
        """
        try:
            body = await request.json()
        except Exception:
            raise A2AError(JSONRPCErrorCode.PARSE_ERROR, "invalid JSON body")

        if body.get("jsonrpc") != "2.0":
            raise A2AError(JSONRPCErrorCode.INVALID_REQUEST, "jsonrpc must be '2.0'")

        method = body.get("method")
        params = body.get("params") or {}
        request_id = body.get("id")

        if method == "message/stream":
            event_iter = await _start_stream_for_send(backend, params, auth, request)
        elif method == "tasks/resubscribe":
            event_iter = await _start_stream_for_resubscribe(backend, params)
        else:
            raise A2AError(
                JSONRPCErrorCode.METHOD_NOT_FOUND,
                f"streaming method '{method}' is not supported on this endpoint",
            )

        return EventSourceResponse(
            _wrap_events_as_jsonrpc(event_iter, request_id),
            ping=30,  # heartbeat every 30s
        )

    return router


async def _start_stream_for_send(
    backend: AgentBackend,
    params: dict[str, Any],
    auth: AuthContext,
    request: Request,
) -> AsyncIterator[TaskEvent]:
    raw_message = params.get("message")
    if raw_message is None:
        raise A2AError(JSONRPCErrorCode.INVALID_PARAMS, "params.message is required")
    message = Message.model_validate(raw_message)

    is_continuation = message.task_id is not None
    if is_continuation:
        existing = await backend.get_task(message.task_id)
        if existing is None:
            raise A2AError(
                JSONRPCErrorCode.TASK_NOT_FOUND, f"task {message.task_id} not found"
            )
        await backend.continue_task(
            task_id=message.task_id, message=message, history=existing.history,
        )
        task_id = message.task_id
    else:
        task_id = new_task_id()
        context_id = message.context_id or new_context_id()
        ctx = TaskContext(
            auth=auth,
            context_id=context_id,
            client_ip=request.client.host if request.client else None,
        )
        await backend.submit_task(message=message, task_id=task_id, context=ctx)

    return backend.stream_events(task_id)


async def _start_stream_for_resubscribe(
    backend: AgentBackend, params: dict[str, Any],
) -> AsyncIterator[TaskEvent]:
    task_id: TaskID | None = params.get("id") or params.get("taskId")
    if not task_id:
        raise A2AError(JSONRPCErrorCode.INVALID_PARAMS, "params.id (taskId) is required")
    task = await backend.get_task(task_id)
    if task is None:
        raise A2AError(JSONRPCErrorCode.TASK_NOT_FOUND, f"task {task_id} not found")
    return backend.stream_events(task_id)


async def _wrap_events_as_jsonrpc(
    events: AsyncIterator[TaskEvent], request_id: Any,
) -> AsyncIterator[dict[str, str]]:
    """Wrap each TaskEvent in a JSON-RPC 2.0 result envelope, encoded as
    SSE `data:` field. A2A spec mandates this envelope shape on the wire."""
    async for ev in events:
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": ev.model_dump(mode="json", by_alias=True, exclude_none=True),
        }
        yield {"event": ev.kind, "data": json.dumps(payload, ensure_ascii=False)}
        if isinstance(ev, TaskStatusUpdateEvent) and ev.final:
            return
