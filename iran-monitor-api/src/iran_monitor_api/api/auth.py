"""API key auth — Bearer token. Maps to org_id from settings.api_keys_json.

In production, IRAN_API_API_KEYS_JSON is loaded from SOPS-encrypted env.
"""

from __future__ import annotations

import json
from functools import lru_cache

from fastapi import Header, status
from fastapi.exceptions import HTTPException

from ..config import get_settings
from ..errors import APIError, ErrorCode


@lru_cache(maxsize=1)
def _api_keys() -> dict[str, str]:
    settings = get_settings()
    try:
        return json.loads(settings.api_keys_json)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"IRAN_API_API_KEYS_JSON is not valid JSON: {e}") from e


def reset_api_keys_cache() -> None:
    _api_keys.cache_clear()


def require_api_key(authorization: str | None = Header(default=None)) -> tuple[str, str]:
    """Returns (api_key, org_id). Raises APIError otherwise."""
    if not authorization:
        raise APIError(ErrorCode.MISSING_API_KEY, "missing Authorization header")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise APIError(
            ErrorCode.MISSING_API_KEY,
            "Authorization header must be 'Bearer <token>'",
        )
    api_key = parts[1].strip()
    keys = _api_keys()
    org_id = keys.get(api_key)
    if org_id is None:
        raise APIError(ErrorCode.INVALID_API_KEY, "invalid API key")
    return api_key, org_id
