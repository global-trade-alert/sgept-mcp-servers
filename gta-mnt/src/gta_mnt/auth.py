"""JWT authentication manager for GTA MNT server."""

import base64
import json
import time
from typing import Optional

import httpx


# Buffer before token expiry (seconds) to trigger refresh
_EXPIRY_BUFFER_SECONDS = 300  # 5 minutes


class JWTAuthManager:
    """Manages JWT Bearer tokens for the GTA API.

    Obtains tokens from /auth/get_token/, caches them in memory,
    and transparently refreshes before expiry.
    """

    BASE_URL = "https://api.globaltradealert.org"

    def __init__(self, email: str, password: str) -> None:
        self._email = email
        self._password = password
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0
        self._user_id: Optional[int] = None  # Will be set after authentication

    async def get_token(self) -> str:
        """Get a valid JWT access token, refreshing if expired.

        Returns:
            Valid JWT access token string.

        Raises:
            httpx.HTTPStatusError: If authentication fails.
            RuntimeError: If token obtain fails unexpectedly.
        """
        if not self._is_token_valid():
            await self._obtain_token()
        return self._access_token  # type: ignore[return-value]

    async def get_user_id(self) -> int:
        """Get the authenticated user's ID.

        Returns:
            User ID from the JWT token payload.

        Raises:
            RuntimeError: If no token available or user_id not in payload.
        """
        if self._user_id is None:
            # Ensure we have a valid token
            await self.get_token()

            # Parse user_id from token payload
            if self._access_token:
                try:
                    parts = self._access_token.split(".")
                    payload_b64 = parts[1]
                    padding = 4 - len(payload_b64) % 4
                    if padding != 4:
                        payload_b64 += "=" * padding
                    payload_bytes = base64.urlsafe_b64decode(payload_b64)
                    payload = json.loads(payload_bytes)
                    self._user_id = payload.get("user_id")
                except Exception:
                    pass

            if self._user_id is None:
                raise RuntimeError("Could not extract user_id from JWT token")

        return self._user_id

    async def _obtain_token(self) -> None:
        """Obtain a new JWT token from the auth endpoint."""
        endpoint = f"{self.BASE_URL}/auth/get_token/"
        payload = {
            "email": self._email,
            "password": self._password,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

        access_token = data.get("access")
        if not access_token:
            raise RuntimeError(
                "JWT auth response missing 'access' token. "
                f"Response keys: {list(data.keys())}"
            )

        self._access_token = access_token
        self._token_expiry = self._parse_expiry(access_token)
        self._user_id = None  # Reset user_id, will be extracted on next get_user_id call

    def _parse_expiry(self, token: str) -> float:
        """Extract exp claim from JWT payload via base64 decode.

        Args:
            token: JWT token string (header.payload.signature).

        Returns:
            Expiry timestamp as float. Falls back to current time + 1 hour
            if parsing fails.
        """
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return time.time() + 3600

            # JWT payload is base64url-encoded
            payload_b64 = parts[1]
            # Add padding if needed
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding

            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_bytes)
            return float(payload.get("exp", time.time() + 3600))
        except Exception:
            # Fallback: assume 1 hour validity
            return time.time() + 3600

    def _is_token_valid(self) -> bool:
        """Check if token exists and is not within expiry buffer."""
        if self._access_token is None:
            return False
        return time.time() < (self._token_expiry - _EXPIRY_BUFFER_SECONDS)
