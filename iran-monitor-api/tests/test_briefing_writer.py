"""Briefing-writer model parsing + prompt construction."""

from __future__ import annotations

from iran_monitor_api.briefing_writer import (
    _build_briefing_prompt,
    parse_briefing_output,
)
from iran_monitor_api.models import HighElasticityEvent, MajorDisagreement


def test_parse_briefing_output_happy_path():
    raw = {
        "major_disagreements": [
            {
                "topic": "German government public attribution",
                "spread_pp": 12.0,
                "high_side": ["red-team-adversarial"],
                "low_side": ["tetlock-forecaster", "wack-strategic"],
                "narrative": "Tetlock and Wack treat attribution as structurally near-impossible.",
            }
        ],
        "high_elasticity_events": [
            {
                "event": "Germany openly provides ISR support to US forces",
                "shift_direction": "up",
                "magnitude_pp": "+8 to +12",
                "monitor": "Bundeswehr deployment announcements; Pistorius statements",
            }
        ],
        "briefing_markdown": "# Scenario assessment\n\nBottom line.",
    }
    dis, ev, md = parse_briefing_output(raw)
    assert len(dis) == 1 and isinstance(dis[0], MajorDisagreement)
    assert dis[0].topic == "German government public attribution"
    assert len(ev) == 1 and isinstance(ev[0], HighElasticityEvent)
    assert ev[0].shift_direction == "up"
    assert md.startswith("# Scenario assessment")


def test_parse_briefing_output_skips_malformed_items():
    raw = {
        "major_disagreements": [
            {"topic": "ok", "spread_pp": 5.0, "high_side": ["a"], "low_side": ["b"], "narrative": "n"},
            {"topic": "missing_fields"},  # malformed — should be skipped
        ],
        "high_elasticity_events": [
            {"event": "ok", "shift_direction": "down", "magnitude_pp": "-1", "monitor": "x"},
            {"shift_direction": "sideways"},  # malformed
        ],
        "briefing_markdown": "ok",
    }
    dis, ev, md = parse_briefing_output(raw)
    assert len(dis) == 1
    assert len(ev) == 1
    assert md == "ok"


def test_parse_briefing_output_handles_empty():
    dis, ev, md = parse_briefing_output({})
    assert dis == []
    assert ev == []
    assert md == ""


def test_prompt_includes_scenario_and_perspectives():
    prompt = _build_briefing_prompt(
        scenario="Iran cyber attack on Germany in 30d",
        horizon_days=30,
        p_point=0.018,
        p_interval=(0.013, 0.025),
        divergence_flag=False,
        consensus_summary="tight consensus",
        perspectives=[
            {
                "name": "tetlock-forecaster",
                "p_point": 0.020,
                "p_interval": [0.015, 0.030],
                "key_reasoning": "Fermi decomp yields…",
                "evidence_urls": ["https://example.gov/x"],
                "divergence_from_consensus_pp": 0.2,
            },
        ],
        intel_base_hash="sha256:abc123",
    )
    assert "Iran cyber attack on Germany" in prompt
    assert "tetlock-forecaster" in prompt
    assert "Fermi decomp" in prompt
    assert "sha256:abc123" in prompt
    assert "START_USER_SCENARIO" in prompt
    assert "END_USER_SCENARIO" in prompt
