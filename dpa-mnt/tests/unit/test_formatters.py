"""Unit tests for dpa_mnt formatters."""

import pytest

from dpa_mnt.formatters import (
    CHARACTER_LIMIT,
    _truncate,
    format_issue_comment,
    format_verification_comment,
    format_review_complete_comment,
    truncate_quote,
    format_review_queue,
    format_event_detail,
    format_intervention_context,
    format_source_result,
    format_templates,
)
from dpa_mnt.models import SourceResult


# ============================================================================
# Low-level helpers
# ============================================================================


def test_truncate_short_passthrough():
    short = "x" * 100
    assert _truncate(short, "hint") == short


def test_truncate_long_bounded_with_hint():
    long = "x" * (CHARACTER_LIMIT + 5000)
    result = _truncate(long, "Re-request with smaller page")
    assert len(result) <= CHARACTER_LIMIT
    assert "[truncated" in result
    assert "Re-request with smaller page" in result


def test_truncate_quote_short():
    assert truncate_quote("short", max_length=500) == "short"


def test_truncate_quote_long():
    result = truncate_quote("A" * 600, max_length=500)
    assert result.endswith(" [...]")
    assert len(result) == 506


# ============================================================================
# Comment formatters
# ============================================================================


def test_format_issue_comment():
    result = format_issue_comment(
        field="event_type",
        criticality="Critical",
        current_value="Announcement",
        suggested_value="Enforcement",
        rationale="Source cites penalty schedule.",
        source_quote="A fine of EUR 10m shall apply",
        source_ref="Official Journal, 15 Jan 2026",
    )
    assert "## FIELD: event_type" in result
    assert "**Criticality:** Critical" in result
    assert "A fine of EUR 10m shall apply" in result


def test_format_verification_comment():
    result = format_verification_comment(
        decision="Implementation date confirmed as 2026-01-15",
        source_quote="Entry into force: 15 January 2026",
        source_ref="Official Journal",
        explanation="Source confirms date.",
    )
    assert "## VERIFIED:" in result
    assert "15 January 2026" in result


def test_format_review_complete_comment():
    result = format_review_complete_comment(
        verified_fields=["event_title", "event_date"],
        critical_decisions=["Event type classification"],
    )
    assert "## REVIEW COMPLETE" in result
    assert "Buzessa Claudini automated review system" in result


# ============================================================================
# Review queue
# ============================================================================


def test_format_review_queue_empty():
    data = {"results": [], "count": 0}
    out = format_review_queue(data)
    assert "No events awaiting review" in out


def test_format_review_queue_with_events():
    data = {
        "results": [
            {
                "event_id": 501,
                "event_title": "Proposed amendment to data protection regulation",
                "event_type_name": "Bill Introduction",
                "action_type_name": "Announcement",
                "status_time": "2026-02-01",
            },
            {
                "event_id": 502,
                "event_title": "Guidance on cross-border transfers",
                "event_type_name": "Guidance",
                "action_type_name": "Publication",
                "status_time": "2026-01-31",
            },
        ],
        "count": 2,
    }
    out = format_review_queue(data)
    assert "DPA Review Queue (2 events)" in out
    assert "| 501 |" in out
    assert "| 502 |" in out
    assert "Date Entered Review" in out


# ============================================================================
# Event detail — including the Phase 2 schema-alignment fields
# ============================================================================


def _sample_event_data(**overrides) -> dict:
    """Minimal event_data shape matching api.get_event() return."""
    data = {
        "event": {
            "event_id": 501,
            "intervention_id": 777,
            "event_title": "Data protection amendment introduced",
            "event_description": "Parliament introduced a bill amending Article 5.",
            "event_date": "2026-02-01",
            "event_type_name": "Bill Introduction",
            "action_type_name": "Announcement",
            "gov_branch_name": "Legislature",
            "gov_body_name": "Parliament",
            "status_name": "Step 1 Review (AT)",
            "status_id": 2,
            "is_case": False,
            "is_current": True,
        },
        "intervention": {
            "intervention_id": 777,
            "intervention_title": "Data Protection Reform 2026",
            "policy_area_name": "Data protection",
            "intervention_type_name": "Statute",
            "implementation_level_name": "National",
            "current_status_name": "Under development",
        },
        "development": {"development_name": "Data Protection Reform Package"},
        "economic_activities": [{"economic_activity_name": "Telecommunications"}],
        "implementing_jurisdictions": [
            {"jurisdiction_name": "Germany", "iso_code": "DEU"}
        ],
        "policy_areas": [{"policy_area_name": "Cross-border data transfer"}],
        "related_interventions": [],
        "issues": [{"issue_name": "GDPR compatibility"}],
        "rationales": [{"rationale_name": "Align with EU framework"}],
        "agents": [],
        "author": {
            "user_id": 42,
            "username": "a_smith",
            "first_name": "Alex",
            "last_name": "Smith",
            "email": "a.smith@dpa.example",
        },
        "benchmarks": [
            {
                "id": 1,
                "is_dpa_existing": 1,
                "benchmark_name": "GDPR Article 5",
                "overlap_name": "Full",
                "substance_name": "Principles",
            }
        ],
        "sources": [],
        "comments": [],
    }
    data.update(overrides)
    return data


def test_format_event_detail_error_shape():
    out = format_event_detail({"error": "Event 999 not found"})
    assert "# Error" in out
    assert "Event 999 not found" in out


def test_format_event_detail_renders_author():
    out = format_event_detail(_sample_event_data())
    assert "**Author:** Alex Smith (@a_smith, user_id=42)" in out


def test_format_event_detail_renders_author_unknown_when_none():
    out = format_event_detail(_sample_event_data(author=None))
    assert "**Author:** *Unknown*" in out


def test_format_event_detail_renders_is_current():
    out = format_event_detail(_sample_event_data())
    assert "**Is Current:** Yes" in out
    out_no = format_event_detail(_sample_event_data(event={**_sample_event_data()["event"], "is_current": False}))
    assert "**Is Current:** No" in out_no


def test_format_event_detail_renders_benchmarks():
    out = format_event_detail(_sample_event_data())
    assert "## Benchmarks (1)" in out
    assert "GDPR Article 5" in out
    assert "Overlap: Full" in out
    assert "Substance: Principles" in out


def test_format_event_detail_renders_issues_and_rationales():
    out = format_event_detail(_sample_event_data())
    assert "GDPR compatibility" in out
    assert "Align with EU framework" in out


def test_format_event_detail_truncates_oversize():
    # Force a giant description to exceed CHARACTER_LIMIT.
    data = _sample_event_data()
    data["event"] = {**data["event"], "event_description": "A" * (CHARACTER_LIMIT + 50_000)}
    out = format_event_detail(data)
    assert len(out) <= CHARACTER_LIMIT
    assert "[truncated" in out
    assert "include_intervention=False" in out


# ============================================================================
# Intervention context — including Phase 2 parity fields
# ============================================================================


def _sample_context_data(**overrides) -> dict:
    data = {
        "intervention": {
            "intervention_id": 777,
            "intervention_title": "Data Protection Reform 2026",
            "policy_area_name": "Data protection",
            "intervention_type_name": "Statute",
            "implementation_level_name": "National",
            "current_status_name": "Under development",
        },
        "development": {"development_name": "Data Protection Reform Package"},
        "implementing_jurisdictions": [{"jurisdiction_name": "Germany", "iso_code": "DEU"}],
        "economic_activities": [],
        "events": [
            {
                "event_id": 501,
                "event_date": "2026-02-01",
                "event_title": "Bill introduced",
                "event_type_name": "Bill Introduction",
                "action_type_name": "Announcement",
                "status_name": "Step 1 Review (AT)",
                "status_id": 2,
                "event_description": "Parliament introduced the bill.",
            },
            {
                "event_id": 502,
                "event_date": "2026-02-15",
                "event_title": "Bill passed first reading",
                "event_type_name": "Legislative Proceeding",
                "action_type_name": "Update",
                "status_name": "Published",
                "status_id": 7,
                "event_description": "First reading passed with amendments.",
            },
        ],
        "related_interventions": [],
        "development_siblings": [],
        "issues": [{"issue_name": "GDPR compatibility"}],
        "rationales": [{"rationale_name": "Align with EU framework"}],
        "agents": [{"agent_type_name": "Regulator", "firm_name": "BfDI", "role_name": "Commenting"}],
        "benchmarks": [
            {
                "is_dpa_existing": 0,
                "benchmark_name": "GDPR Article 5",
                "overlap_name": "Partial",
                "substance_name": "Principles",
            }
        ],
    }
    data.update(overrides)
    return data


def test_format_intervention_context_error_shape():
    out = format_intervention_context({"error": "Intervention 999 not found"})
    assert "# Error" in out
    assert "Intervention 999 not found" in out


def test_format_intervention_context_renders_events_timeline():
    out = format_intervention_context(_sample_context_data())
    assert "# Intervention Context: Data Protection Reform 2026 (INT-777)" in out
    assert "[PUBLISHED]" in out  # status_id == 7 marker
    assert "[IN REVIEW]" in out  # status_id == 2 marker
    assert "## Event Timeline (2 events)" in out


def test_format_intervention_context_renders_issues_rationales():
    out = format_intervention_context(_sample_context_data())
    assert "**Thematic Issues:**" in out
    assert "GDPR compatibility" in out
    assert "**Stated Rationales:**" in out
    assert "Align with EU framework" in out


def test_format_intervention_context_renders_agents():
    out = format_intervention_context(_sample_context_data())
    assert "## Agents/Firms (1)" in out
    assert "**Regulator**" in out
    assert "(BfDI)" in out


def test_format_intervention_context_renders_benchmarks():
    out = format_intervention_context(_sample_context_data())
    assert "## Benchmarks (1)" in out
    assert "GDPR Article 5" in out
    assert "external" in out  # is_dpa_existing == 0


def test_format_intervention_context_truncates_oversize():
    # Use published events (status_id=7), because the context formatter
    # renders their full event_description text — that's the expansion
    # path that actually makes a payload exceed CHARACTER_LIMIT.
    data = _sample_context_data()
    data["events"] = [
        {
            **data["events"][0],
            "event_id": i,
            "status_id": 7,
            "status_name": "Published",
            "event_description": "X" * 5000,
        }
        for i in range(60)
    ]
    out = format_intervention_context(data)
    assert len(out) <= CHARACTER_LIMIT
    assert "[truncated" in out
    assert "dpa_mnt_get_event" in out


# ============================================================================
# Source result
# ============================================================================


def test_format_source_result_with_content():
    src = SourceResult(
        source_type="url",
        source_url="https://example.com/policy.pdf",
        content="Extracted PDF body.",
        content_type="pdf",
    )
    out = format_source_result(src)
    assert "# Official Source" in out
    assert "**URL:** https://example.com/policy.pdf" in out
    assert "**Content Type:** pdf" in out
    assert "Extracted PDF body." in out


def test_format_source_result_without_content():
    src = SourceResult(
        source_type="url",
        source_url="https://example.com/policy.html",
        content=None,
        content_type="html",
    )
    out = format_source_result(src)
    assert "Content not fetched (fetch_content=False)" in out


def test_format_source_result_truncates_long_content():
    big = "A" * (CHARACTER_LIMIT + 20_000)
    src = SourceResult(
        source_type="url",
        source_url="https://example.com/big.pdf",
        content=big,
        content_type="pdf",
    )
    out = format_source_result(src)
    assert len(out) <= CHARACTER_LIMIT
    assert "[truncated" in out
    assert "fetch_content=False" in out


# ============================================================================
# Templates
# ============================================================================


def test_format_templates_empty():
    out = format_templates({"results": []})
    assert "No templates available" in out


def test_format_templates_with_data():
    data = {
        "results": [
            {
                "id": 1,
                "template_name": "Issue comment",
                "template_text": "## FIELD: {field}\n\n**Criticality:** {criticality}",
                "is_checklist": 0,
            }
        ]
    }
    out = format_templates(data)
    assert "Comment Templates (1)" in out
    assert "Issue comment" in out
