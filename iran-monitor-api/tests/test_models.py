"""Pydantic models + quorum rule + helpers."""

from __future__ import annotations

import pytest

from iran_monitor_api.models import (
    ALL_PERSPECTIVES,
    DEFAULT_PERSPECTIVES,
    CreateQueryRequest,
    Horizon,
    Tier,
    horizon_to_days,
    quorum_required,
)


def test_default_perspectives_excludes_nuclear_only_pair():
    assert "solingen-proliferation" not in DEFAULT_PERSPECTIVES
    assert "narang-nuclear" not in DEFAULT_PERSPECTIVES
    assert len(DEFAULT_PERSPECTIVES) == len(ALL_PERSPECTIVES) - 2


def test_quorum_rule_two_thirds_ceiling():
    assert quorum_required(12) == 8     # ⌈24/3⌉
    assert quorum_required(14) == 10    # ⌈28/3⌉ = 10
    assert quorum_required(3) == 2
    assert quorum_required(7) == 5      # ⌈14/3⌉ = 5
    assert quorum_required(1) == 1


def test_horizon_to_days_table():
    assert horizon_to_days(Horizon.D7) == 7
    assert horizon_to_days(Horizon.D30) == 30
    assert horizon_to_days(Horizon.D90) == 90


def test_create_query_request_validates_scenario_length():
    with pytest.raises(ValueError):
        CreateQueryRequest(scenario="too short", horizon=Horizon.D30, tier=Tier.STANDARD)
    long = "x" * 1501
    with pytest.raises(ValueError):
        CreateQueryRequest(scenario=long, horizon=Horizon.D30, tier=Tier.STANDARD)


def test_create_query_request_strips_control_chars():
    msg = "Iran launches a cyber attack on German critical infrastructure\x00\x01 within 30 days"
    body = CreateQueryRequest(
        scenario=msg, horizon=Horizon.D30, tier=Tier.STANDARD,
    )
    assert "\x00" not in body.scenario
    assert "\x01" not in body.scenario
    assert "Iran launches" in body.scenario


def test_create_query_request_rejects_unknown_perspectives():
    with pytest.raises(ValueError):
        CreateQueryRequest(
            scenario="Iran launches a cyber attack on German infrastructure in 30 days",
            horizon=Horizon.D30,
            tier=Tier.STANDARD,
            perspectives=["tetlock-forecaster", "made-up-agent", "schelling-bargaining"],
        )


def test_create_query_request_requires_min_three_perspectives():
    with pytest.raises(ValueError):
        CreateQueryRequest(
            scenario="Iran launches a cyber attack on German infrastructure in 30 days",
            horizon=Horizon.D30,
            tier=Tier.STANDARD,
            perspectives=["tetlock-forecaster", "schelling-bargaining"],
        )


def test_create_query_request_accepts_valid_perspectives():
    body = CreateQueryRequest(
        scenario="Iran launches a cyber attack on German infrastructure in 30 days",
        horizon=Horizon.D30,
        tier=Tier.PREMIUM,
        perspectives=["tetlock-forecaster", "schelling-bargaining", "ostovar-irgc"],
    )
    assert body.tier == Tier.PREMIUM
    assert len(body.perspectives) == 3
