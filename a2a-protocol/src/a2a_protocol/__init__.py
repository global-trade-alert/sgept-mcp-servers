"""A2A protocol — reusable FastAPI server + Python client.

Public API:
- AgentBackend: Protocol consumers implement
- AgentCard, AgentCapabilities, AgentSkill: card models
- Task, Message, Part, TextPart, DataPart, Artifact: A2A core models
- TaskState: 8-state lifecycle enum + transition validator
- create_app(backend): FastAPI app factory
- A2AClient: generic JSON-RPC + SSE client
- A2AError, JSONRPCError: error types
"""

from a2a_protocol.backend import AgentBackend, TaskHandle, TaskContext, TaskEvent, AuthContext
from a2a_protocol.card import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    AgentProvider,
    AgentAuthentication,
)
from a2a_protocol.errors import A2AError, JSONRPCError, JSONRPCErrorCode
from a2a_protocol.lifecycle import TaskState, is_valid_transition
from a2a_protocol.models import (
    Task,
    TaskID,
    Message,
    MessageRole,
    Part,
    TextPart,
    DataPart,
    FilePart,
    Artifact,
    TaskStatus,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
)
from a2a_protocol.server import create_app

__version__ = "0.1.0"

__all__ = [
    "AgentBackend",
    "TaskHandle",
    "TaskContext",
    "TaskEvent",
    "AuthContext",
    "AgentCard",
    "AgentCapabilities",
    "AgentSkill",
    "AgentProvider",
    "AgentAuthentication",
    "A2AError",
    "JSONRPCError",
    "JSONRPCErrorCode",
    "TaskState",
    "is_valid_transition",
    "Task",
    "TaskID",
    "Message",
    "MessageRole",
    "Part",
    "TextPart",
    "DataPart",
    "FilePart",
    "Artifact",
    "TaskStatus",
    "TaskStatusUpdateEvent",
    "TaskArtifactUpdateEvent",
    "create_app",
    "__version__",
]
