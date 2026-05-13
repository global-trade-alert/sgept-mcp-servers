"""JSON-RPC 2.0 + A2A-specific error codes.

JSON-RPC 2.0 reserves -32700 to -32000.
A2A uses -32001 .. -32099 for its own error codes (spec convention).
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any


class JSONRPCErrorCode(IntEnum):
    # Standard JSON-RPC 2.0
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # A2A spec
    TASK_NOT_FOUND = -32001
    TASK_NOT_CANCELABLE = -32002
    PUSH_NOTIFICATIONS_NOT_SUPPORTED = -32003
    UNSUPPORTED_OPERATION = -32004
    CONTENT_TYPE_NOT_SUPPORTED = -32005
    INVALID_AGENT_RESPONSE = -32006
    AUTHENTICATION_REQUIRED = -32007

    # SGEPT extensions (in the spec-allowed -32099..-32000 range)
    RATE_LIMITED = -32050
    AUTH_INVALID = -32051


class A2AError(Exception):
    """Base exception. Server-side code raises these; the dispatcher converts
    them to JSON-RPC error responses."""

    def __init__(
        self,
        code: JSONRPCErrorCode,
        message: str,
        data: dict[str, Any] | None = None,
    ):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"[{code.name}/{int(code)}] {message}")

    def to_jsonrpc(self, request_id: Any) -> dict[str, Any]:
        body: dict[str, Any] = {"code": int(self.code), "message": self.message}
        if self.data is not None:
            body["data"] = self.data
        return {"jsonrpc": "2.0", "id": request_id, "error": body}


JSONRPCError = A2AError  # alias for clarity at import sites
