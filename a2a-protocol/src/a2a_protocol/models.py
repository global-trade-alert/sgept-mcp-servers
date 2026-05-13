"""A2A core models: Task, Message, Part, Artifact, status-update events.

Mirrors the A2A v1.0 wire schema. Field naming follows the spec (camelCase on
the wire, snake_case in Python with `model_config(populate_by_name=True)` aliases).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Literal, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from .lifecycle import TaskState

TaskID = str
MessageID = str
ContextID = str


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _new_id() -> str:
    return str(uuid4())


# ── Message roles ────────────────────────────────────────────────────────────


class MessageRole(str, Enum):
    USER = "user"          # the calling agent / client
    AGENT = "agent"        # this agent (server side)


# ── Parts (text / data / file) ───────────────────────────────────────────────


class _BasePart(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    kind: str  # discriminator
    metadata: dict[str, Any] | None = None


class TextPart(_BasePart):
    kind: Literal["text"] = "text"
    text: str


class DataPart(_BasePart):
    """Structured JSON payload."""
    kind: Literal["data"] = "data"
    data: dict[str, Any]


class FilePart(_BasePart):
    """File reference (URI) or inline base64 bytes. A2A spec supports both."""
    kind: Literal["file"] = "file"
    file: dict[str, Any]  # {name, mimeType, bytes?, uri?}


Part = Annotated[
    Union[TextPart, DataPart, FilePart],
    Field(discriminator="kind"),
]


# ── Message ──────────────────────────────────────────────────────────────────


class Message(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: MessageRole
    parts: list[Part]
    message_id: MessageID = Field(default_factory=_new_id, alias="messageId")
    task_id: TaskID | None = Field(default=None, alias="taskId")
    context_id: ContextID | None = Field(default=None, alias="contextId")
    kind: Literal["message"] = "message"
    metadata: dict[str, Any] | None = None

    def text(self) -> str:
        """Concatenate text parts. Convenience for clients."""
        return "\n".join(p.text for p in self.parts if isinstance(p, TextPart))

    def data(self) -> dict[str, Any]:
        """Merge data parts into a single dict (last write wins for collisions)."""
        out: dict[str, Any] = {}
        for p in self.parts:
            if isinstance(p, DataPart):
                out.update(p.data)
        return out


# ── Artifact ─────────────────────────────────────────────────────────────────


class Artifact(BaseModel):
    """A2A `Artifact` — the durable output of a task."""

    model_config = ConfigDict(populate_by_name=True)

    artifact_id: str = Field(default_factory=_new_id, alias="artifactId")
    name: str | None = None
    description: str | None = None
    parts: list[Part]
    metadata: dict[str, Any] | None = None


# ── TaskStatus + Task ────────────────────────────────────────────────────────


class TaskStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    state: TaskState
    message: Message | None = None    # optional status note (often the agent's clarification question)
    timestamp: datetime = Field(default_factory=_now)


class Task(BaseModel):
    """A2A `Task` — the durable record of a single delegated unit of work."""

    model_config = ConfigDict(populate_by_name=True)

    id: TaskID
    context_id: ContextID = Field(alias="contextId")
    status: TaskStatus
    artifacts: list[Artifact] = Field(default_factory=list)
    history: list[Message] = Field(default_factory=list)
    kind: Literal["task"] = "task"
    metadata: dict[str, Any] | None = None


# ── Streaming event envelopes ────────────────────────────────────────────────


class TaskStatusUpdateEvent(BaseModel):
    """SSE event payload — status change."""

    model_config = ConfigDict(populate_by_name=True)

    task_id: TaskID = Field(alias="taskId")
    context_id: ContextID = Field(alias="contextId")
    status: TaskStatus
    final: bool = False
    kind: Literal["status-update"] = "status-update"
    metadata: dict[str, Any] | None = None


class TaskArtifactUpdateEvent(BaseModel):
    """SSE event payload — new artifact or artifact fragment."""

    model_config = ConfigDict(populate_by_name=True)

    task_id: TaskID = Field(alias="taskId")
    context_id: ContextID = Field(alias="contextId")
    artifact: Artifact
    append: bool = False
    last_chunk: bool = True
    kind: Literal["artifact-update"] = "artifact-update"
    metadata: dict[str, Any] | None = None


# ── Helpers ──────────────────────────────────────────────────────────────────


def new_task_id() -> TaskID:
    return _new_id()


def new_context_id() -> ContextID:
    return _new_id()


def text_message(role: MessageRole, text: str, **kwargs) -> Message:
    """Convenience constructor for a single-text-part Message."""
    return Message(role=role, parts=[TextPart(text=text)], **kwargs)


def data_message(role: MessageRole, data: dict[str, Any], **kwargs) -> Message:
    """Convenience constructor for a single-data-part Message."""
    return Message(role=role, parts=[DataPart(data=data)], **kwargs)
