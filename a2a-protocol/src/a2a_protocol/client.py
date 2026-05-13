"""Generic A2A client — JSON-RPC + SSE.

Backend-agnostic. Wraps an A2A endpoint at any URL. Used by:
- Iran-monitor's `A2AClient` (re-exported with iran-monitor-specific helpers)
- Test suites (especially the generalization smoke against MockGTABackend)
- Anyone evaluating an A2A endpoint

The client knows the protocol; the caller knows the domain.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, AsyncIterator
from uuid import uuid4

import httpx

from .card import AgentCard
from .errors import A2AError, JSONRPCErrorCode
from .models import (
    Message,
    MessageRole,
    Task,
    TaskID,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    TextPart,
)


TaskEvent = TaskStatusUpdateEvent | TaskArtifactUpdateEvent


@dataclass
class A2ATransportError(Exception):
    status_code: int
    body: str

    def __str__(self) -> str:
        return f"A2A transport error HTTP {self.status_code}: {self.body[:200]}"


class A2AClient:
    """Thin JSON-RPC + SSE client against an A2A endpoint."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 60.0,
    ):
        if not api_key:
            raise ValueError("api_key is required")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def __aenter__(self) -> "A2AClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()

    # ── Agent card ────────────────────────────────────────────────────────

    async def get_agent_card(self) -> AgentCard:
        r = await self._http.get("/.well-known/agent-card.json")
        if r.status_code != 200:
            raise A2ATransportError(r.status_code, r.text)
        return AgentCard.model_validate(r.json())

    # ── Methods (JSON-RPC) ───────────────────────────────────────────────

    async def send_message(
        self,
        text: str | None = None,
        *,
        message: Message | None = None,
        task_id: TaskID | None = None,
    ) -> Task:
        """`message/send`. Either pass a `text` (single text-part user message)
        or a fully-constructed `message`. If `task_id` is provided, this is a
        continuation."""
        if message is None:
            if text is None:
                raise ValueError("either text or message must be provided")
            message = Message(
                role=MessageRole.USER,
                parts=[TextPart(text=text)],
                task_id=task_id,
            )
        elif task_id is not None:
            message = message.model_copy(update={"task_id": task_id})

        result = await self._call(
            "message/send",
            {"message": message.model_dump(mode="json", by_alias=True, exclude_none=True)},
        )
        return Task.model_validate(result)

    async def get_task(self, task_id: TaskID) -> Task:
        result = await self._call("tasks/get", {"id": task_id})
        return Task.model_validate(result)

    async def cancel_task(self, task_id: TaskID) -> Task:
        result = await self._call("tasks/cancel", {"id": task_id})
        return Task.model_validate(result)

    async def stream_message(
        self,
        text: str | None = None,
        *,
        message: Message | None = None,
        task_id: TaskID | None = None,
    ) -> AsyncIterator[TaskEvent]:
        """`message/stream`. Same parameters as send_message; returns an async
        iterator of TaskEvents instead of a one-shot Task."""
        if message is None:
            if text is None:
                raise ValueError("either text or message must be provided")
            message = Message(
                role=MessageRole.USER,
                parts=[TextPart(text=text)],
                task_id=task_id,
            )
        elif task_id is not None:
            message = message.model_copy(update={"task_id": task_id})

        envelope = {
            "jsonrpc": "2.0",
            "id": str(uuid4()),
            "method": "message/stream",
            "params": {
                "message": message.model_dump(mode="json", by_alias=True, exclude_none=True),
            },
        }

        async with self._http.stream("POST", "/v1/jsonrpc/stream", json=envelope) as r:
            if r.status_code != 200:
                body = await r.aread()
                raise A2ATransportError(r.status_code, body.decode(errors="replace"))
            async for ev in _parse_sse_events(r):
                yield ev

    async def resubscribe(self, task_id: TaskID) -> AsyncIterator[TaskEvent]:
        envelope = {
            "jsonrpc": "2.0",
            "id": str(uuid4()),
            "method": "tasks/resubscribe",
            "params": {"id": task_id},
        }
        async with self._http.stream("POST", "/v1/jsonrpc/stream", json=envelope) as r:
            if r.status_code != 200:
                body = await r.aread()
                raise A2ATransportError(r.status_code, body.decode(errors="replace"))
            async for ev in _parse_sse_events(r):
                yield ev

    # ── Internals ─────────────────────────────────────────────────────────

    async def _call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        envelope = {
            "jsonrpc": "2.0",
            "id": str(uuid4()),
            "method": method,
            "params": params,
        }
        r = await self._http.post("/v1/jsonrpc", json=envelope)
        if r.status_code != 200:
            raise A2ATransportError(r.status_code, r.text)
        body = r.json()
        if "error" in body:
            err = body["error"]
            raise A2AError(
                JSONRPCErrorCode(err.get("code", -32603)),
                err.get("message", "unspecified error"),
                data=err.get("data"),
            )
        return body["result"]


async def _parse_sse_events(response: httpx.Response) -> AsyncIterator[TaskEvent]:
    """Minimal SSE parser tolerant of the EventSourceResponse framing.

    Each event arrives as `data: <json>\\n\\n`. We accumulate `data:` lines per
    event and parse the JSON-RPC envelope at the boundary.
    """
    buffer: list[str] = []
    async for line in response.aiter_lines():
        if line.startswith("data:"):
            buffer.append(line[5:].lstrip())
            continue
        if line == "" and buffer:
            payload = "".join(buffer)
            buffer.clear()
            try:
                env = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if "result" in env:
                result = env["result"]
                kind = result.get("kind")
                if kind == "status-update":
                    yield TaskStatusUpdateEvent.model_validate(result)
                elif kind == "artifact-update":
                    yield TaskArtifactUpdateEvent.model_validate(result)
    # Final buffer (no trailing blank line)
    if buffer:
        payload = "".join(buffer)
        try:
            env = json.loads(payload)
            result = env.get("result")
            if result:
                kind = result.get("kind")
                if kind == "status-update":
                    yield TaskStatusUpdateEvent.model_validate(result)
                elif kind == "artifact-update":
                    yield TaskArtifactUpdateEvent.model_validate(result)
        except json.JSONDecodeError:
            pass
