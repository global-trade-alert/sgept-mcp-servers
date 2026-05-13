"""Bearer-token auth helper. Delegates the actual check to the backend.

The protocol package doesn't store keys. The backend's `authenticate(token)`
returns an AuthContext (success) or None (reject); we wrap that into a
FastAPI dependency.
"""

from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Header

from .backend import AgentBackend, AuthContext
from .errors import A2AError, JSONRPCErrorCode


def make_bearer_dependency(backend: AgentBackend) -> Callable:
    """Returns a FastAPI dependency that resolves to an AuthContext or raises
    an A2AError mapped to AUTH_INVALID."""

    async def require_bearer(
        authorization: Annotated[str | None, Header()] = None,
    ) -> AuthContext:
        if not authorization:
            raise A2AError(
                JSONRPCErrorCode.AUTHENTICATION_REQUIRED,
                "missing Authorization header",
            )
        parts = authorization.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise A2AError(
                JSONRPCErrorCode.AUTH_INVALID,
                "Authorization header must be 'Bearer <token>'",
            )
        token = parts[1].strip()
        ctx = backend.authenticate(token)
        if ctx is None:
            raise A2AError(JSONRPCErrorCode.AUTH_INVALID, "invalid token")
        return ctx

    return require_bearer
