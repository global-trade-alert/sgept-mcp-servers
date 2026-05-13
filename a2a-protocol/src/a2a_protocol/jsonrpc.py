"""JSON-RPC 2.0 dispatcher.

Single POST endpoint dispatches to A2A method handlers by `method` field.

Methods implemented (Layer 2):
- message/send  — submit new task OR continue existing task (if params.message.taskId set)
- tasks/get
- tasks/cancel

Added in Layer 4 (SSE):
- message/stream  — same dispatch as message/send but returns SSE
- tasks/resubscribe

Each handler:
1. Parses params via Pydantic
2. Calls into the backend
3. Returns an A2A Task (or void) for serialization

The Bearer auth dependency runs before dispatch.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .auth import make_bearer_dependency
from .backend import AgentBackend, AuthContext, TaskContext
from .errors import A2AError, JSONRPCErrorCode
from .models import Message, TaskID, new_context_id

logger = logging.getLogger(__name__)


def build_jsonrpc_router(backend: AgentBackend) -> APIRouter:
    router = APIRouter()
    require_auth = make_bearer_dependency(backend)

    @router.post("/v1/jsonrpc")
    async def jsonrpc_endpoint(
        request: Request,
        auth: AuthContext = Depends(require_auth),
    ) -> JSONResponse:
        # 1. Parse envelope
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                A2AError(JSONRPCErrorCode.PARSE_ERROR, "invalid JSON body").to_jsonrpc(None),
                status_code=200,  # JSON-RPC spec: HTTP 200 with error in body
            )

        if not isinstance(body, dict):
            return JSONResponse(
                A2AError(JSONRPCErrorCode.INVALID_REQUEST, "envelope must be an object").to_jsonrpc(None),
                status_code=200,
            )

        request_id = body.get("id")
        method = body.get("method")
        params = body.get("params") or {}

        if body.get("jsonrpc") != "2.0":
            return JSONResponse(
                A2AError(
                    JSONRPCErrorCode.INVALID_REQUEST,
                    "jsonrpc field must equal '2.0'",
                ).to_jsonrpc(request_id),
                status_code=200,
            )

        if not isinstance(method, str):
            return JSONResponse(
                A2AError(JSONRPCErrorCode.INVALID_REQUEST, "method must be a string").to_jsonrpc(request_id),
                status_code=200,
            )

        # 2. Dispatch
        try:
            if method == "message/send":
                result = await _handle_message_send(backend, params, auth, request)
            elif method == "tasks/get":
                result = await _handle_tasks_get(backend, params)
            elif method == "tasks/cancel":
                result = await _handle_tasks_cancel(backend, params)
            else:
                raise A2AError(
                    JSONRPCErrorCode.METHOD_NOT_FOUND,
                    f"method '{method}' is not supported",
                )
        except A2AError as e:
            logger.info("JSON-RPC error: %s on method=%s", e, method)
            return JSONResponse(e.to_jsonrpc(request_id), status_code=200)
        except ValidationError as e:
            return JSONResponse(
                A2AError(
                    JSONRPCErrorCode.INVALID_PARAMS,
                    "params validation failed",
                    data={"errors": e.errors()},
                ).to_jsonrpc(request_id),
                status_code=200,
            )
        except Exception as e:
            logger.exception("JSON-RPC internal error on method=%s", method)
            return JSONResponse(
                A2AError(JSONRPCErrorCode.INTERNAL_ERROR, f"internal error: {type(e).__name__}").to_jsonrpc(request_id),
                status_code=200,
            )

        return JSONResponse(
            {"jsonrpc": "2.0", "id": request_id, "result": result},
            status_code=200,
        )

    return router


# ── Method handlers ──────────────────────────────────────────────────────────


async def _handle_message_send(
    backend: AgentBackend,
    params: dict[str, Any],
    auth: AuthContext,
    request: Request,
) -> dict[str, Any]:
    """`message/send` — new task or continuation."""
    # Params shape: {"message": <Message>, "configuration": {...}?}
    raw_message = params.get("message")
    if raw_message is None:
        raise A2AError(JSONRPCErrorCode.INVALID_PARAMS, "params.message is required")

    message = Message.model_validate(raw_message)
    is_continuation = message.task_id is not None

    if is_continuation:
        # Resume an existing task.
        existing = await backend.get_task(message.task_id)
        if existing is None:
            raise A2AError(
                JSONRPCErrorCode.TASK_NOT_FOUND,
                f"task {message.task_id} not found",
            )
        handle = await backend.continue_task(
            task_id=message.task_id,
            message=message,
            history=existing.history,
        )
    else:
        # New task.
        from .models import new_task_id
        task_id: TaskID = new_task_id()
        context_id = message.context_id or new_context_id()
        ctx = TaskContext(
            auth=auth,
            context_id=context_id,
            client_ip=request.client.host if request.client else None,
            request_id=str(params.get("requestId") or ""),
        )
        handle = await backend.submit_task(message=message, task_id=task_id, context=ctx)

    return handle.task.model_dump(mode="json", by_alias=True, exclude_none=True)


async def _handle_tasks_get(
    backend: AgentBackend, params: dict[str, Any],
) -> dict[str, Any]:
    task_id = params.get("id") or params.get("taskId")
    if not task_id:
        raise A2AError(JSONRPCErrorCode.INVALID_PARAMS, "params.id (taskId) is required")
    task = await backend.get_task(task_id)
    if task is None:
        raise A2AError(JSONRPCErrorCode.TASK_NOT_FOUND, f"task {task_id} not found")
    return task.model_dump(mode="json", by_alias=True, exclude_none=True)


async def _handle_tasks_cancel(
    backend: AgentBackend, params: dict[str, Any],
) -> dict[str, Any]:
    task_id = params.get("id") or params.get("taskId")
    if not task_id:
        raise A2AError(JSONRPCErrorCode.INVALID_PARAMS, "params.id (taskId) is required")
    task = await backend.get_task(task_id)
    if task is None:
        raise A2AError(JSONRPCErrorCode.TASK_NOT_FOUND, f"task {task_id} not found")
    from .lifecycle import is_terminal
    if is_terminal(task.status.state):
        raise A2AError(
            JSONRPCErrorCode.TASK_NOT_CANCELABLE,
            f"task {task_id} already in terminal state {task.status.state.value}",
        )
    final = await backend.cancel_task(task_id)
    return final.model_dump(mode="json", by_alias=True, exclude_none=True)
