"""HTTP route tests: auth, validation, rate limit, status flow."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from iran_monitor_api import db, signing
from iran_monitor_api.config import get_settings
from iran_monitor_api.main import create_app
from iran_monitor_api.models import Status, Tier, new_query_id


@pytest.fixture
def client(isolated_env):
    return TestClient(create_app())


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_missing_auth_returns_401(client):
    r = client.post(
        "/v1/queries",
        json={"scenario": "x" * 30, "horizon": "30d", "tier": "standard"},
    )
    assert r.status_code == 401
    assert r.json()["error"] == "missing_api_key"


def test_invalid_token_returns_401(client):
    r = client.post(
        "/v1/queries",
        headers={"Authorization": "Bearer wrong"},
        json={"scenario": "x" * 30, "horizon": "30d", "tier": "standard"},
    )
    assert r.status_code == 401
    assert r.json()["error"] == "invalid_api_key"


# ── Input validation ──────────────────────────────────────────────────────────


def test_short_scenario_returns_400(client):
    r = client.post(
        "/v1/queries",
        headers={"Authorization": "Bearer test-key-A"},
        json={"scenario": "no", "horizon": "30d", "tier": "standard"},
    )
    assert r.status_code == 422  # pydantic validation


def test_unknown_horizon_returns_422(client):
    r = client.post(
        "/v1/queries",
        headers={"Authorization": "Bearer test-key-A"},
        json={"scenario": "x" * 30, "horizon": "120d", "tier": "standard"},
    )
    assert r.status_code == 422


def test_unknown_tier_returns_422(client):
    r = client.post(
        "/v1/queries",
        headers={"Authorization": "Bearer test-key-A"},
        json={"scenario": "x" * 30, "horizon": "30d", "tier": "ultra"},
    )
    assert r.status_code == 422


# ── Happy path: enqueue + poll ───────────────────────────────────────────────


def test_create_query_returns_202_with_query_id(client):
    r = client.post(
        "/v1/queries",
        headers={"Authorization": "Bearer test-key-A"},
        json={
            "scenario": "Iran launches a cyber attack on German critical infrastructure in 30 days",
            "horizon": "30d",
            "tier": "standard",
        },
    )
    assert r.status_code == 202
    body = r.json()
    assert "query_id" in body
    assert body["status"] == "queued"
    assert body["tier"] == "standard"


def test_get_query_returns_in_progress_after_create(client):
    r = client.post(
        "/v1/queries",
        headers={"Authorization": "Bearer test-key-A"},
        json={
            "scenario": "Iran launches a cyber attack on German infrastructure in 30 days",
            "horizon": "30d",
            "tier": "standard",
        },
    )
    qid = r.json()["query_id"]
    r2 = client.get(
        f"/v1/queries/{qid}",
        headers={"Authorization": "Bearer test-key-A"},
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["status"] == "queued"
    assert body["perspectives_completed"] == 0
    assert body["perspectives_total"] >= 3


def test_get_query_not_found_returns_404(client):
    qid = new_query_id()
    r = client.get(
        f"/v1/queries/{qid}",
        headers={"Authorization": "Bearer test-key-A"},
    )
    assert r.status_code == 404
    assert r.json()["error"] == "query_not_found"


def test_get_query_org_isolation(client):
    """org-A creates a query; org-B asking gets 404 (not 403, to avoid leaking existence)."""
    r = client.post(
        "/v1/queries",
        headers={"Authorization": "Bearer test-key-A"},
        json={
            "scenario": "Iran cyber attack on German infrastructure in 30 days",
            "horizon": "30d",
            "tier": "standard",
        },
    )
    qid = r.json()["query_id"]
    r2 = client.get(
        f"/v1/queries/{qid}",
        headers={"Authorization": "Bearer test-key-B"},
    )
    assert r2.status_code == 404


# ── Rate limiting ─────────────────────────────────────────────────────────────


def test_premium_rate_limit_exceeded_returns_429(client, monkeypatch):
    # Premium default is 10/hr; submit 11 and the last should 429
    payload = {
        "scenario": "Iran launches a cyber attack on German infrastructure in 30 days",
        "horizon": "30d",
        "tier": "premium",
    }
    headers = {"Authorization": "Bearer test-key-A"}
    for _ in range(10):
        r = client.post("/v1/queries", headers=headers, json=payload)
        assert r.status_code == 202
    r = client.post("/v1/queries", headers=headers, json=payload)
    assert r.status_code == 429
    assert r.json()["error"] == "rate_limited"
    assert r.headers.get("Retry-After") is not None


# ── Healthz ───────────────────────────────────────────────────────────────────


def test_healthz_ok(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.text == "ok"


# ── Public key endpoint ───────────────────────────────────────────────────────


def test_public_key_returns_503_when_unprovisioned(client):
    r = client.get("/.well-known/iran-monitor-signing-key.pub")
    assert r.status_code == 503


def test_public_key_served_when_provisioned(client):
    settings = get_settings()
    priv, pub = signing.generate_keypair()
    signing.write_keys(
        priv, pub,
        private_path=settings.signing_key_path,
        public_path=settings.signing_pub_key_path,
    )
    r = client.get("/.well-known/iran-monitor-signing-key.pub")
    assert r.status_code == 200
    assert r.content == pub
