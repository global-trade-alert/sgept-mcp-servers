"""Generalization smoke — the experiment's verdict.

If MockBackend (a pure-echo, zero-domain-knowledge implementation of
AgentBackend) can run all the protocol-level tests without ANY Iran-monitor
imports, then the protocol package is genuinely reusable. The CEO's "can we
A2A-enable our other databases?" experiment passes its first check.
"""

from __future__ import annotations

import sys

import pytest
from fastapi.testclient import TestClient

from a2a_protocol import AgentBackend, create_app

from .mock_backend import MockBackend


def test_mock_backend_satisfies_protocol():
    """The Protocol is runtime_checkable; isinstance() works."""
    backend = MockBackend()
    assert isinstance(backend, AgentBackend)


def test_no_iran_monitor_imports():
    """The protocol package + its tests must not depend on iran_monitor_api."""
    # Walk a2a_protocol's own modules — none should reference iran_monitor_api.
    leaked = [
        name for name in sys.modules
        if name.startswith("a2a_protocol") and "iran_monitor" in name
    ]
    assert leaked == [], f"protocol package leaked iran-monitor imports: {leaked}"


def test_mock_backend_runs_full_jsonrpc_flow():
    """A full submit → get → cancel cycle works against MockBackend with no
    Iran-specific code path involved."""
    client = TestClient(create_app(MockBackend()))

    # Submit
    msg = {"role": "user", "parts": [{"kind": "text", "text": "ping"}]}
    r = client.post(
        "/v1/jsonrpc",
        json={"jsonrpc": "2.0", "method": "message/send", "params": {"message": msg}, "id": 1},
        headers={"Authorization": "Bearer mock-key"},
    )
    assert r.status_code == 200, r.text
    task_id = r.json()["result"]["id"]

    # Get
    r = client.post(
        "/v1/jsonrpc",
        json={"jsonrpc": "2.0", "method": "tasks/get", "params": {"id": task_id}, "id": 2},
        headers={"Authorization": "Bearer mock-key"},
    )
    assert r.json()["result"]["id"] == task_id


def test_mock_backend_card_endpoint():
    """Generalization smoke: a totally different agent's card is served
    correctly via the same /.well-known/ route."""
    client = TestClient(create_app(MockBackend()))
    r = client.get("/.well-known/agent-card.json")
    body = r.json()
    assert body["name"] == "mock-agent"        # not iran-monitor!
    assert body["skills"][0]["id"] == "echo"   # not assess_scenario!
