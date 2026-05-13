"""Agent card serialization + /.well-known/ endpoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from a2a_protocol import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    AgentAuthentication,
)
from a2a_protocol.card import build_card_router


def _make_card() -> AgentCard:
    return AgentCard(
        name="test",
        description="for tests",
        url="https://example.com",
        capabilities=AgentCapabilities(streaming=True, push_notifications=False),
        authentication=AgentAuthentication(schemes=["bearer"]),
        skills=[
            AgentSkill(id="s1", name="skill 1", description="d", examples=["ex"]),
        ],
    )


def test_card_serializes_with_camelcase():
    card = _make_card()
    d = card.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert d["protocolVersion"] == "1.0"
    assert d["capabilities"]["pushNotifications"] is False
    assert d["capabilities"]["stateTransitionHistory"] is True
    assert d["defaultInputModes"] == ["application/json"]
    assert d["skills"][0]["id"] == "s1"


def test_well_known_endpoint_returns_card():
    app = FastAPI()
    app.include_router(build_card_router(_make_card()))
    client = TestClient(app)
    r = client.get("/.well-known/agent-card.json")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "test"
    assert body["capabilities"]["streaming"] is True
    assert body["skills"][0]["name"] == "skill 1"


def test_capabilities_streaming_granularity_alias():
    cap = AgentCapabilities(streaming=True, streaming_granularity="event")
    d = cap.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert d["streamingGranularity"] == "event"
