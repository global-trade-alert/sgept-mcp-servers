"""Queue DAL: enqueue/claim/perspective tracking/complete."""

from __future__ import annotations

import json

from iran_monitor_api import db
from iran_monitor_api.models import Status, Tier, new_query_id


def test_enqueue_then_claim_marks_running(isolated_env):
    qid = new_query_id()
    db.enqueue_query(
        query_id=qid,
        org_id="org-1",
        api_key="test-key-A",
        scenario="scenario text long enough",
        horizon="30d",
        tier=Tier.STANDARD,
        perspectives_invoked=["tetlock-forecaster", "schelling-bargaining", "ostovar-irgc"],
    )

    row = db.claim_next_query()
    assert row is not None
    assert row["status"] == Status.RUNNING.value
    assert row["started_at_utc"] is not None
    assert row["query_id"] == str(qid)


def test_claim_returns_none_when_empty(isolated_env):
    assert db.claim_next_query() is None


def test_claim_returns_in_fifo_order(isolated_env):
    import time as _t
    q1 = new_query_id()
    db.enqueue_query(
        query_id=q1, org_id="o", api_key="test-key-A", scenario="x" * 30,
        horizon="30d", tier=Tier.STANDARD, perspectives_invoked=["a", "b", "c"],
    )
    _t.sleep(0.01)
    q2 = new_query_id()
    db.enqueue_query(
        query_id=q2, org_id="o", api_key="test-key-A", scenario="y" * 30,
        horizon="30d", tier=Tier.STANDARD, perspectives_invoked=["a", "b", "c"],
    )
    first = db.claim_next_query()
    assert first["query_id"] == str(q1)
    second = db.claim_next_query()
    assert second["query_id"] == str(q2)


def test_mark_perspective_completed_appends(isolated_env):
    qid = new_query_id()
    db.enqueue_query(
        query_id=qid, org_id="o", api_key="k", scenario="x" * 30,
        horizon="30d", tier=Tier.PREMIUM, perspectives_invoked=["a", "b", "c"],
    )
    db.mark_perspective_completed(qid, "a")
    db.mark_perspective_completed(qid, "b")
    db.mark_perspective_completed(qid, "a")  # idempotent
    row = db.get_query(qid)
    completed = json.loads(row["perspectives_completed"])
    assert completed == ["a", "b"]


def test_complete_query_writes_audit_and_signature(isolated_env):
    qid = new_query_id()
    db.enqueue_query(
        query_id=qid, org_id="o", api_key="k", scenario="x" * 30,
        horizon="30d", tier=Tier.PREMIUM, perspectives_invoked=["a", "b", "c"],
    )
    db.claim_next_query()
    db.complete_query(
        query_id=qid,
        status=Status.COMPLETED,
        intel_base_hash="sha256:test",
        query_delta_hash="sha256:delta",
        result_json='{"p_point":0.2}',
        audit_record_json='{"version":"1.0"}',
        audit_signature="base64sig",
        runtime_seconds=900,
    )
    row = db.get_query(qid)
    assert row["status"] == Status.COMPLETED.value
    assert row["audit_signature"] == "base64sig"
    assert row["runtime_seconds"] == 900


def test_running_recovery(isolated_env):
    qid = new_query_id()
    db.enqueue_query(
        query_id=qid, org_id="o", api_key="k", scenario="x" * 30,
        horizon="30d", tier=Tier.STANDARD, perspectives_invoked=["a", "b", "c"],
    )
    db.claim_next_query()
    running = db.find_running_queries()
    assert len(running) == 1
    db.reset_running_to_queued(qid)
    assert db.find_running_queries() == []
    row = db.get_query(qid)
    assert row["status"] == Status.QUEUED.value


def test_rate_limit_counts_within_window(isolated_env):
    from datetime import timedelta
    from iran_monitor_api.models import utc_now
    now = utc_now()
    db.record_rate_limit_event("org-x", Tier.STANDARD, now - timedelta(minutes=10))
    db.record_rate_limit_event("org-x", Tier.STANDARD, now - timedelta(minutes=5))
    db.record_rate_limit_event("org-x", Tier.PREMIUM, now)
    window_start = (now - timedelta(hours=1)).isoformat()
    assert db.count_rate_limit_events("org-x", Tier.STANDARD, window_start) == 2
    assert db.count_rate_limit_events("org-x", Tier.PREMIUM, window_start) == 1
    assert db.count_rate_limit_events("org-y", Tier.STANDARD, window_start) == 0
