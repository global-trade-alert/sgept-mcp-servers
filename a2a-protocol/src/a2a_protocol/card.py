"""AgentCard model + FastAPI route factory.

A2A's discovery mechanism: GET /.well-known/agent-card.json returns this card.
Buyer agents read the card to learn:
- What skills the agent exposes
- What auth scheme to use
- What transports/methods are available
- What capabilities (streaming, push notifications, state-transition history)
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field


class AgentProvider(BaseModel):
    organization: str
    url: str | None = None


class AgentCapabilities(BaseModel):
    """A2A capability flags. Spec-defined, but `streamingGranularity` is an
    extension we use to honestly declare event-vs-token streaming."""

    model_config = ConfigDict(populate_by_name=True)

    streaming: bool = False
    push_notifications: bool = Field(default=False, alias="pushNotifications")
    state_transition_history: bool = Field(default=True, alias="stateTransitionHistory")
    streaming_granularity: Literal["event", "token"] | None = Field(
        default=None, alias="streamingGranularity"
    )


class AgentAuthentication(BaseModel):
    """A2A auth declaration. Following the OpenAPI-ish security-scheme shape."""

    schemes: list[str]                         # e.g. ["bearer"]
    credentials: dict[str, Any] | None = None  # bearerFormat, scopes, etc.


class AgentSkill(BaseModel):
    """One named capability exposed by the agent."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    input_modes: list[str] | None = Field(default=None, alias="inputModes")
    output_modes: list[str] | None = Field(default=None, alias="outputModes")


class AgentCard(BaseModel):
    """The /.well-known/agent-card.json payload."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str
    url: str
    provider: AgentProvider | None = None
    version: str = "1.0.0"
    protocol_version: str = Field(default="1.0", alias="protocolVersion")
    documentation_url: str | None = Field(default=None, alias="documentationUrl")
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    authentication: AgentAuthentication | None = None
    default_input_modes: list[str] = Field(
        default_factory=lambda: ["application/json"], alias="defaultInputModes"
    )
    default_output_modes: list[str] = Field(
        default_factory=lambda: ["application/json", "text/markdown"],
        alias="defaultOutputModes",
    )
    skills: list[AgentSkill]


def build_card_router(card: AgentCard) -> APIRouter:
    """Returns a FastAPI router serving GET /.well-known/agent-card.json."""

    router = APIRouter()

    @router.get("/.well-known/agent-card.json", include_in_schema=False)
    async def get_agent_card() -> JSONResponse:
        return JSONResponse(card.model_dump(mode="json", by_alias=True, exclude_none=True))

    return router
