"""Orchestrator aggregation + quorum behavior (with subagent mocked)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

import pytest

from iran_monitor_api import orchestrator, signing
from iran_monitor_api.config import get_settings
from iran_monitor_api.models import Status, Tier
from iran_monitor_api.subagent import PerspectiveResult, SubagentError


def _make_result(name: str, p: float, reasoning: str = "ok") -> PerspectiveResult:
    return PerspectiveResult(
        name=name,
        p_point=p,
        p_interval=(max(0.0, p - 0.05), min(1.0, p + 0.05)),
        key_reasoning=reasoning,
        evidence_urls=[f"https://example.gov/{name}"],
        raw_json={},
        runtime_seconds=1.0,
    )


def _ensure_signing_key():
    settings = get_settings()
    if not settings.signing_key_path.exists():
        priv, pub = signing.generate_keypair()
        signing.write_keys(
            priv, pub,
            private_path=settings.signing_key_path,
            public_path=settings.signing_pub_key_path,
        )


@pytest.mark.asyncio
async def test_orchestrator_happy_path(isolated_env, monkeypatch):
    _ensure_signing_key()

    calls = []
    async def fake_invoke(*, name, scenario, horizon_days, intel_base_summary,
                          cold_start_prior, output_dir, timeout_seconds=None):
        calls.append((name, cold_start_prior))
        return _make_result(name, p=0.15)

    monkeypatch.setattr(orchestrator, "invoke_perspective", fake_invoke)

    perspectives = ["wack-strategic", "tetlock-forecaster", "schelling-bargaining", "red-team-adversarial"]
    result_dict, audit_dict, sig, status = await orchestrator.run_assess(
        query_id=uuid4(),
        scenario="a scenario long enough to pass validation later",
        horizon="30d",
        tier=Tier.STANDARD,
        perspectives=perspectives,
        intel_base_hash="sha256:test",
        query_delta_path=None,
        query_delta_hash=None,
    )

    assert status == Status.COMPLETED
    # Tetlock must run first
    assert calls[0][0] == "tetlock-forecaster"
    assert calls[0][1] is None  # tetlock has no prior
    # All subsequent agents see tetlock's prior
    for name, prior in calls[1:]:
        assert prior is not None
        assert prior["p_point"] == 0.15
        # Independence: prior is NUMBERS ONLY. We must not propagate
        # Tetlock's reasoning text to other perspectives — that caused
        # the chain-leakage failure in spike run 20260512T180303Z.
        assert "reasoning" not in prior, (
            "cold_start_prior must not include Tetlock's reasoning text; "
            "downstream perspectives copy-paste it. Pass p_point + p_interval only."
        )

    assert result_dict["p_point"] == pytest.approx(0.15)
    assert result_dict["divergence_flag"] is False
    assert sig  # signed
    assert audit_dict["aggregation_method"] == "weighted_uniform_average_v1"


@pytest.mark.asyncio
async def test_orchestrator_flags_divergence_over_15pp(isolated_env, monkeypatch):
    _ensure_signing_key()

    p_values = iter([0.10, 0.50, 0.20, 0.15])  # tetlock first, spread = 40pp
    async def fake_invoke(**kwargs):
        return _make_result(kwargs["name"], p=next(p_values))

    monkeypatch.setattr(orchestrator, "invoke_perspective", fake_invoke)

    result_dict, audit_dict, sig, status = await orchestrator.run_assess(
        query_id=uuid4(),
        scenario="a scenario",
        horizon="30d",
        tier=Tier.STANDARD,
        perspectives=["tetlock-forecaster", "schelling-bargaining", "wack-strategic", "red-team-adversarial"],
        intel_base_hash="sha256:test",
        query_delta_path=None,
        query_delta_hash=None,
    )
    assert status == Status.COMPLETED
    assert result_dict["divergence_flag"] is True


@pytest.mark.asyncio
async def test_orchestrator_returns_partial_when_some_fail(isolated_env, monkeypatch):
    _ensure_signing_key()
    perspectives = ["tetlock-forecaster", "schelling-bargaining", "wack-strategic",
                    "red-team-adversarial", "ostovar-irgc", "gause-regional"]

    async def fake_invoke(**kwargs):
        if kwargs["name"] in ("ostovar-irgc", "gause-regional"):
            raise SubagentError("simulated failure")
        return _make_result(kwargs["name"], p=0.2)

    monkeypatch.setattr(orchestrator, "invoke_perspective", fake_invoke)

    result_dict, audit_dict, sig, status = await orchestrator.run_assess(
        query_id=uuid4(),
        scenario="a scenario",
        horizon="30d",
        tier=Tier.STANDARD,
        perspectives=perspectives,
        intel_base_hash="sha256:test",
        query_delta_path=None,
        query_delta_hash=None,
    )
    # 4 of 6 completed, quorum is ⌈12/3⌉=4, so PARTIAL
    assert status == Status.PARTIAL
    assert sorted(result_dict["failed_perspectives"]) == ["gause-regional", "ostovar-irgc"]


@pytest.mark.asyncio
async def test_orchestrator_fails_when_quorum_not_met(isolated_env, monkeypatch):
    _ensure_signing_key()
    perspectives = ["tetlock-forecaster", "schelling-bargaining", "wack-strategic",
                    "red-team-adversarial", "ostovar-irgc", "gause-regional"]

    async def fake_invoke(**kwargs):
        if kwargs["name"] in ("wack-strategic", "red-team-adversarial",
                               "ostovar-irgc", "gause-regional"):
            raise SubagentError("simulated failure")
        return _make_result(kwargs["name"], p=0.2)

    monkeypatch.setattr(orchestrator, "invoke_perspective", fake_invoke)

    result_dict, audit_dict, sig, status = await orchestrator.run_assess(
        query_id=uuid4(),
        scenario="a scenario",
        horizon="30d",
        tier=Tier.STANDARD,
        perspectives=perspectives,
        intel_base_hash="sha256:test",
        query_delta_path=None,
        query_delta_hash=None,
    )
    # 2 of 6 completed, quorum is 4, so FAILED
    assert status == Status.FAILED
    assert "quorum_met" in audit_dict["result_summary"]
    assert audit_dict["result_summary"]["quorum_met"] is False


def test_resolve_perspectives_uses_default_when_none(isolated_env):
    from iran_monitor_api.models import DEFAULT_PERSPECTIVES
    assert orchestrator.resolve_perspectives(None) == DEFAULT_PERSPECTIVES


def test_resolve_perspectives_passes_through_explicit_list(isolated_env):
    requested = ["tetlock-forecaster", "schelling-bargaining", "ostovar-irgc"]
    assert orchestrator.resolve_perspectives(requested) == requested
