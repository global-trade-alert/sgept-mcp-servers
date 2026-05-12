"""Extended model coverage: deliver_to validation, new result fields."""

from __future__ import annotations

import pytest

from iran_monitor_api.models import (
    CreateQueryRequest,
    HighElasticityEvent,
    Horizon,
    MajorDisagreement,
    PerspectiveOutput,
    QueryResult,
    Tier,
)


def test_create_query_request_deliver_to_accepts_email():
    body = CreateQueryRequest(
        scenario="Iran cyber attack on German infrastructure in 30 days",
        horizon=Horizon.D30, tier=Tier.PREMIUM,
        deliver_to="desk@hedge-fund.com",
    )
    assert body.deliver_to == "desk@hedge-fund.com"


def test_create_query_request_deliver_to_strips_whitespace():
    body = CreateQueryRequest(
        scenario="Iran cyber attack on German infrastructure in 30 days",
        horizon=Horizon.D30, tier=Tier.PREMIUM,
        deliver_to="  desk@hedge-fund.com  ",
    )
    assert body.deliver_to == "desk@hedge-fund.com"


def test_create_query_request_deliver_to_rejects_non_email():
    with pytest.raises(ValueError):
        CreateQueryRequest(
            scenario="Iran cyber attack on German infrastructure in 30 days",
            horizon=Horizon.D30, tier=Tier.PREMIUM,
            deliver_to="not-an-email",
        )


def test_create_query_request_deliver_to_none_is_ok():
    body = CreateQueryRequest(
        scenario="Iran cyber attack on German infrastructure in 30 days",
        horizon=Horizon.D30, tier=Tier.PREMIUM,
    )
    assert body.deliver_to is None


def test_major_disagreement_model():
    d = MajorDisagreement(
        topic="German attribution",
        spread_pp=12.5,
        high_side=["red-team-adversarial"],
        low_side=["tetlock-forecaster", "wack-strategic"],
        narrative="Tetlock and Wack treat attribution as structurally improbable.",
    )
    assert d.spread_pp == 12.5
    assert len(d.high_side) == 1
    assert len(d.low_side) == 2


def test_high_elasticity_event_shift_direction_enum():
    HighElasticityEvent(
        event="Germany provides ISR support to US forces",
        shift_direction="up",
        magnitude_pp="+8 to +12",
        monitor="Bundeswehr announcements",
    )
    HighElasticityEvent(
        event="Iran-US MoU signed",
        shift_direction="down",
        magnitude_pp="-1 to -2",
        monitor="Iranian state media",
    )
    with pytest.raises(ValueError):
        HighElasticityEvent(
            event="x", shift_direction="sideways", magnitude_pp="0", monitor="x",
        )


def test_query_result_has_phase_1_5_fields_with_empty_defaults():
    result = QueryResult(
        p_point=0.1,
        p_interval=(0.05, 0.2),
        divergence_flag=False,
        consensus_summary="test",
        perspectives=[
            PerspectiveOutput(name="a", p_point=0.1, key_reasoning="x", evidence_urls=[]),
        ],
    )
    assert result.major_disagreements == []
    assert result.high_elasticity_events == []
    assert result.briefing_markdown == ""


def test_query_result_serialization_includes_phase_1_5_fields():
    result = QueryResult(
        p_point=0.1,
        p_interval=(0.05, 0.2),
        divergence_flag=False,
        consensus_summary="test",
        perspectives=[],
        major_disagreements=[
            MajorDisagreement(topic="t", spread_pp=5.0, high_side=["a"], low_side=["b"], narrative="n"),
        ],
        high_elasticity_events=[
            HighElasticityEvent(event="e", shift_direction="up", magnitude_pp="+1", monitor="m"),
        ],
        briefing_markdown="# B",
    )
    d = result.model_dump(mode="json")
    assert "major_disagreements" in d
    assert "high_elasticity_events" in d
    assert "briefing_markdown" in d
    assert d["briefing_markdown"] == "# B"
    assert d["major_disagreements"][0]["topic"] == "t"
