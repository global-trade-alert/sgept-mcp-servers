"""JSON-RPC dispatcher: auth, validation, method dispatch, error mapping."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from a2a_protocol import create_app
from a2a_protocol.errors import JSONRPCErrorCode

from .mock_backend import MockBackend


@pytest.fixture
def client():
    return TestClient(create_app(MockBackend()))


def _envelope(method, params=None, id=1):
    return {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": id}


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_missing_auth_returns_jsonrpc_error(client):
    r = client.post("/v1/jsonrpc", json=_envelope("tasks/get", {"id": "x"}))
    body = r.json()
    assert body["error"]["code"] == JSONRPCErrorCode.AUTHENTICATION_REQUIRED


def test_invalid_token_returns_jsonrpc_error(client):
    r = client.post(
        "/v1/jsonrpc", json=_envelope("tasks/get", {"id": "x"}),
        headers={"Authorization": "Bearer wrong"},
    )
    body = r.json()
    assert body["error"]["code"] == JSONRPCErrorCode.AUTH_INVALID


# ── Envelope validation ──────────────────────────────────────────────────────


def test_invalid_jsonrpc_version_returns_invalid_request(client):
    r = client.post(
        "/v1/jsonrpc",
        json={"jsonrpc": "1.0", "method": "tasks/get", "params": {}, "id": 1},
        headers={"Authorization": "Bearer mock-key"},
    )
    body = r.json()
    assert body["error"]["code"] == JSONRPCErrorCode.INVALID_REQUEST


def test_unknown_method_returns_method_not_found(client):
    r = client.post(
        "/v1/jsonrpc",
        json=_envelope("does_not_exist"),
        headers={"Authorization": "Bearer mock-key"},
    )
    body = r.json()
    assert body["error"]["code"] == JSONRPCErrorCode.METHOD_NOT_FOUND


def test_invalid_params_in_message_send(client):
    r = client.post(
        "/v1/jsonrpc",
        json=_envelope("message/send", {}),  # missing 'message'
        headers={"Authorization": "Bearer mock-key"},
    )
    body = r.json()
    assert body["error"]["code"] == JSONRPCErrorCode.INVALID_PARAMS


# ── message/send ─────────────────────────────────────────────────────────────


def test_message_send_creates_task(client):
    msg = {
        "role": "user",
        "parts": [{"kind": "text", "text": "hello mock"}],
    }
    r = client.post(
        "/v1/jsonrpc",
        json=_envelope("message/send", {"message": msg}),
        headers={"Authorization": "Bearer mock-key"},
    )
    body = r.json()
    assert "result" in body
    task = body["result"]
    assert task["kind"] == "task"
    assert task["status"]["state"] == "submitted"
    assert task["history"][0]["parts"][0]["text"] == "hello mock"


# ── tasks/get ─────────────────────────────────────────────────────────────────


def test_tasks_get_for_unknown_returns_task_not_found(client):
    r = client.post(
        "/v1/jsonrpc",
        json=_envelope("tasks/get", {"id": "unknown-id"}),
        headers={"Authorization": "Bearer mock-key"},
    )
    body = r.json()
    assert body["error"]["code"] == JSONRPCErrorCode.TASK_NOT_FOUND


def test_tasks_get_returns_submitted_task(client):
    # Submit
    msg = {"role": "user", "parts": [{"kind": "text", "text": "x"}]}
    r1 = client.post(
        "/v1/jsonrpc",
        json=_envelope("message/send", {"message": msg}),
        headers={"Authorization": "Bearer mock-key"},
    )
    task_id = r1.json()["result"]["id"]

    r2 = client.post(
        "/v1/jsonrpc",
        json=_envelope("tasks/get", {"id": task_id}),
        headers={"Authorization": "Bearer mock-key"},
    )
    body = r2.json()
    assert body["result"]["id"] == task_id


# ── tasks/cancel ─────────────────────────────────────────────────────────────


def test_tasks_cancel_unknown_returns_not_found(client):
    r = client.post(
        "/v1/jsonrpc",
        json=_envelope("tasks/cancel", {"id": "unknown"}),
        headers={"Authorization": "Bearer mock-key"},
    )
    body = r.json()
    assert body["error"]["code"] == JSONRPCErrorCode.TASK_NOT_FOUND


# ── /healthz ─────────────────────────────────────────────────────────────────


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.text == "ok"


# ── Agent card via app ───────────────────────────────────────────────────────


def test_agent_card_served_at_well_known(client):
    r = client.get("/.well-known/agent-card.json")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "mock-agent"
    assert body["skills"][0]["id"] == "echo"
