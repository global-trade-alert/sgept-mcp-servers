"""AgentBackend Protocol — the contract every A2A-enabled asset implements.

The protocol layer (this package) is generic. Asset-specific logic lives in
the consumer's implementation of `AgentBackend`. The package provides:

- FastAPI app factory (server.py)
- JSON-RPC dispatcher (jsonrpc.py)
- SSE streaming (sse.py)
- Lifecycle state machine (lifecycle.py)
- A2A wire models (models.py)
- Agent card publication (card.py)

The backend provides:

- A static `agent_card` declaring skills + capabilities
- `submit_task(message, ...)` — start a new task from a fresh Message
- `continue_task(task_id, message, history)` — resume from input-required
- `cancel_task(task_id)` — transition to canceled
- `get_task(task_id)` — return a Task object
- `stream_events(task_id)` — async iterator of TaskStatusUpdate / TaskArtifactUpdate
- `authenticate(token)` — Bearer-token → AuthContext (or None for reject)

Returning a TaskHandle from submit/continue is sufficient — the actual work
runs in whatever worker the backend manages (Iran-monitor has its own
async worker pool; GTA-a2a would have its own). The protocol package does
not own task execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Protocol, runtime_checkable

from .card import AgentCard
from .models import (
    Artifact,
    ContextID,
    Message,
    Task,
    TaskID,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
)


@dataclass
class AuthContext:
    """Returned by `authenticate`. Opaque to the protocol package; backends
    use the fields they need (org_id for rate-limiting, scopes for skill
    gating, etc.)."""

    principal: str             # opaque identity (org_id, user_id, etc.)
    scopes: frozenset[str]     # capabilities granted to this token
    raw_token: str             # original Bearer token (for downstream calls)
    metadata: dict | None = None


@dataclass
class TaskContext:
    """Auxiliary context passed alongside a Message. Lets the backend track
    rate-limit accounting, audit trail, request origin, etc."""

    auth: AuthContext
    context_id: ContextID            # A2A contextId — caller-chosen or server-assigned
    client_ip: str | None = None
    request_id: str | None = None    # JSON-RPC id, for log correlation


@dataclass
class TaskHandle:
    """What submit/continue return synchronously.

    The actual work runs asynchronously in the backend's worker; this is the
    receipt the caller polls / streams against.
    """

    task: Task


TaskEvent = TaskStatusUpdateEvent | TaskArtifactUpdateEvent


@runtime_checkable
class AgentBackend(Protocol):
    """The interface every A2A-enabled asset implements."""

    @property
    def agent_card(self) -> AgentCard:
        """Static card describing skills + auth + capabilities."""
        ...

    async def submit_task(
        self, message: Message, task_id: TaskID, context: TaskContext,
    ) -> TaskHandle:
        """Start a new task. The backend should:

        1. Translate the A2A Message into its domain inputs.
        2. Enqueue work in its worker.
        3. Return a TaskHandle with the initial Task (status = submitted).
        """
        ...

    async def continue_task(
        self, task_id: TaskID, message: Message, history: list[Message],
    ) -> TaskHandle:
        """Resume a task previously in input-required or auth-required state.

        The backend appends `message` to the task's history and transitions
        the lifecycle from input-required → working (or rejects if e.g. the
        max round-trip cap is hit).
        """
        ...

    async def cancel_task(self, task_id: TaskID) -> Task:
        """Best-effort cancellation. Transitions the task to `canceled`
        (or no-op if already terminal). Returns the final Task object."""
        ...

    async def get_task(self, task_id: TaskID) -> Task | None:
        """Look up the task. Returns None if not found (caller maps to 404 /
        JSON-RPC -32004 internally)."""
        ...

    async def stream_events(self, task_id: TaskID) -> AsyncIterator[TaskEvent]:
        """Async iterator of status + artifact events. Used by SSE.

        Implementations subscribe to their backend-internal event bus (asyncio
        queue, Redis pub/sub, etc.) and yield events until the task reaches
        terminal state. The protocol's SSE layer wraps the iterator in HTTP/2
        SSE framing and handles heartbeats.
        """
        ...

    def authenticate(self, token: str) -> AuthContext | None:
        """Bearer-token → AuthContext or None.

        Synchronous on purpose: auth check happens on every request and the
        backend typically has an in-memory key store. If you need async auth,
        wrap the SyncToAsync helper.
        """
        ...
