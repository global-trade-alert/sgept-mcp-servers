"""Identity management for multi-token Slack MCP server."""

import json
import os
import logging
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class IdentityConfig(BaseModel):
    """Configuration for a single Slack identity."""
    name: str
    description: str = ""
    token_env: str = Field(description="Environment variable name containing the Slack token")
    send_enabled: bool = Field(default=False, description="Whether this identity can send messages")
    default: bool = Field(default=False, description="Whether this is the default identity")
    token: str = Field(default="", exclude=True, description="Resolved token value (never logged)")


class IdentityRegistry:
    """Registry of available Slack identities with token resolution."""

    def __init__(self, identities: dict[str, IdentityConfig], default_name: str):
        self._identities = identities
        self._default_name = default_name

    @property
    def names(self) -> list[str]:
        return list(self._identities.keys())

    @property
    def default_name(self) -> str:
        return self._default_name

    def resolve(self, name: Optional[str] = None) -> IdentityConfig:
        """Resolve an identity by name, or return the default.

        Raises:
            ValueError: If the named identity doesn't exist.
        """
        target = name or self._default_name
        if target not in self._identities:
            available = ", ".join(self._identities.keys())
            raise ValueError(
                f"Unknown Slack identity '{target}'. Available: {available}"
            )
        return self._identities[target]


def load_identities() -> IdentityRegistry:
    """Load identity configuration from file or fall back to legacy env vars.

    Priority:
    1. SLACK_IDENTITIES_FILE env var → JSON config file with multiple identities
    2. Legacy mode: SLACK_BOT_TOKEN / SLACK_USER_TOKEN + SLACK_ENABLE_SEND

    Returns:
        IdentityRegistry with all available identities.

    Raises:
        ValueError: If no tokens are configured at all.
    """
    identities_file = os.getenv("SLACK_IDENTITIES_FILE")

    if identities_file:
        return _load_from_file(identities_file)
    return _load_legacy()


def _load_from_file(path: str) -> IdentityRegistry:
    """Load identities from a JSON config file."""
    with open(path) as f:
        raw = json.load(f)

    identities: dict[str, IdentityConfig] = {}
    default_name: Optional[str] = None

    for entry in raw:
        config = IdentityConfig(**entry)
        token = os.getenv(config.token_env, "")

        if not token:
            logger.warning(
                f"Identity '{config.name}': env var {config.token_env} not set — skipping"
            )
            continue

        if not token.startswith(("xoxp-", "xoxb-")):
            logger.warning(
                f"Identity '{config.name}': invalid token format in {config.token_env} — skipping"
            )
            continue

        config.token = token
        identities[config.name] = config

        if config.default:
            default_name = config.name

    if not identities:
        raise ValueError(
            f"No valid identities loaded from {path}. "
            "Check that token env vars are set and contain valid xoxp-/xoxb- tokens."
        )

    # SLACK_DEFAULT_IDENTITY env var overrides the JSON default flag
    env_default = os.getenv("SLACK_DEFAULT_IDENTITY")
    if env_default and env_default in identities:
        default_name = env_default
    elif env_default and env_default not in identities:
        logger.warning(
            f"SLACK_DEFAULT_IDENTITY='{env_default}' not found in loaded identities — ignoring"
        )

    # Fall back to first identity if no default specified
    if default_name is None:
        default_name = next(iter(identities))

    return IdentityRegistry(identities, default_name)


def _load_legacy() -> IdentityRegistry:
    """Fall back to legacy single-token mode for backward compatibility."""
    token = os.getenv("SLACK_BOT_TOKEN") or os.getenv("SLACK_USER_TOKEN")
    if not token:
        raise ValueError(
            "No Slack token configured. Set SLACK_IDENTITIES_FILE for multi-identity mode, "
            "or SLACK_BOT_TOKEN / SLACK_USER_TOKEN for single-token mode."
        )

    if not token.startswith(("xoxp-", "xoxb-")):
        raise ValueError(
            "Invalid token format. Token must start with 'xoxp-' (user) or 'xoxb-' (bot)."
        )

    send_enabled = os.getenv("SLACK_ENABLE_SEND", "false").lower() == "true"
    token_env = "SLACK_BOT_TOKEN" if os.getenv("SLACK_BOT_TOKEN") else "SLACK_USER_TOKEN"

    config = IdentityConfig(
        name="default",
        description="Legacy single-token identity",
        token_env=token_env,
        send_enabled=send_enabled,
        default=True,
        token=token,
    )

    return IdentityRegistry({"default": config}, "default")
