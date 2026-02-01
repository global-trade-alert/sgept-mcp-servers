"""Unit tests for formatters."""

import pytest
from datetime import datetime

from gta_mnt.formatters import (
    format_issue_comment,
    format_verification_comment,
    format_review_complete_comment,
    truncate_quote,
    format_step1_queue,
    format_measure_detail,
    format_source_result,
    format_templates
)
from gta_mnt.models import SourceResult


def test_format_issue_comment():
    """Test issue comment formatting."""
    result = format_issue_comment(
        field="intervention_type",
        criticality="Critical",
        current_value="Subsidy",
        suggested_value="Export tax",
        rationale="Source clearly states export tax, not subsidy.",
        source_quote="Article 3: An export tax of 5% shall apply",
        source_ref="Official Gazette, 15 Jan 2026"
    )

    assert "## FIELD: intervention_type" in result
    assert "**Criticality:** Critical" in result
    assert "**Current Value:** Subsidy" in result
    assert "**Suggested Value:** Export tax" in result
    assert "Article 3: An export tax of 5% shall apply" in result
    assert "Official Gazette, 15 Jan 2026" in result


def test_format_verification_comment():
    """Test verification comment formatting."""
    result = format_verification_comment(
        decision="Intervention type correctly classified as tariff",
        source_quote="Tariff schedule shows 10% duty",
        source_ref="Customs Notice 2026-01",
        explanation="The source clearly indicates tariff application."
    )

    assert "## VERIFIED:" in result
    assert "Tariff schedule shows 10% duty" in result
    assert "Customs Notice 2026-01" in result
    assert "The source clearly indicates" in result


def test_format_review_complete_comment():
    """Test review complete comment formatting."""
    result = format_review_complete_comment(
        verified_fields=["intervention_type", "affected_jurisdiction", "implementation_level"],
        critical_decisions=["Tariff classification", "Sectoral scope"]
    )

    assert "## REVIEW COMPLETE" in result
    assert "intervention_type" in result
    assert "affected_jurisdiction" in result
    assert "implementation_level" in result
    assert "Tariff classification" in result
    assert "Sectoral scope" in result
    assert "Sancho Claudino automated review system" in result


def test_truncate_quote_short():
    """Test truncate_quote doesn't truncate short quotes."""
    short_quote = "This is a short quote."
    result = truncate_quote(short_quote, max_length=500)
    assert result == short_quote
    assert "[...]" not in result


def test_truncate_quote_long():
    """Test truncate_quote truncates long quotes."""
    long_quote = "A" * 600
    result = truncate_quote(long_quote, max_length=500)
    assert len(result) == 506  # 500 chars + " [...]" (6 chars)
    assert result.endswith(" [...]")


def test_format_step1_queue_empty():
    """Test format_step1_queue with no results."""
    data = {"results": [], "count": 0}
    result = format_step1_queue(data)

    assert "No measures awaiting Step 1 review" in result


def test_format_step1_queue_with_measures():
    """Test format_step1_queue with measures."""
    data = {
        "results": [
            {
                "id": 123,
                "title": "US tariff on steel imports from China",
                "implementing_jurisdiction": "USA",
                "status_time": "2026-02-01T10:30:00Z"
            },
            {
                "id": 124,
                "title": "EU subsidy for green hydrogen production",
                "implementing_jurisdiction": "EUN",
                "status_time": "2026-01-31T15:20:00Z"
            }
        ],
        "count": 2
    }
    result = format_step1_queue(data)

    assert "Step 1 Review Queue (2 measures)" in result
    assert "| 123 |" in result
    assert "| 124 |" in result
    assert "USA" in result
    assert "EUN" in result


def test_format_measure_detail():
    """Test format_measure_detail with full data."""
    measure = {
        "id": 123,
        "title": "Test Measure",
        "description": "Test description",
        "implementing_jurisdiction": "USA",
        "status_id": 2,
        "source_url": "https://example.com/source.pdf",
        "interventions": [
            {"id": 1, "intervention_type": "Tariff", "affected_jurisdiction": "CHN"},
            {"id": 2, "intervention_type": "Quota", "affected_jurisdiction": "DEU"}
        ],
        "comments": [
            {"author": "john_doe", "created": "2026-02-01T10:00:00Z", "text": "Test comment text"}
        ]
    }
    result = format_measure_detail(measure)

    assert "# StateAct 123: Test Measure" in result
    assert "**Implementing Jurisdiction:** USA" in result
    assert "**Status ID:** 2" in result
    assert "## Interventions (2)" in result
    assert "INT-1" in result
    assert "INT-2" in result
    assert "## Comments (1)" in result
    assert "john_doe" in result


def test_format_source_result_with_content():
    """Test format_source_result with fetched content."""
    source = SourceResult(
        source_type="file",
        source_url="s3://bucket/file.pdf",
        content="This is the extracted PDF content.",
        content_type="pdf"
    )
    result = format_source_result(source)

    assert "# Official Source" in result
    assert "**Type:** file" in result
    assert "**URL:** s3://bucket/file.pdf" in result
    assert "**Content Type:** pdf" in result
    assert "This is the extracted PDF content." in result


def test_format_source_result_without_content():
    """Test format_source_result when content not fetched."""
    source = SourceResult(
        source_type="url",
        source_url="https://example.com/doc.html",
        content=None,
        content_type="html"
    )
    result = format_source_result(source)

    assert "**Type:** url" in result
    assert "Content not fetched (fetch_content=False)" in result


def test_format_source_result_truncates_long_content():
    """Test format_source_result truncates very long content."""
    long_content = "A" * 60000
    source = SourceResult(
        source_type="file",
        source_url="s3://bucket/large.pdf",
        content=long_content,
        content_type="pdf"
    )
    result = format_source_result(source)

    assert "content truncated for brevity" in result
    assert len(result) < 60000  # Should be truncated


def test_format_templates_empty():
    """Test format_templates with no results."""
    data = {"results": []}
    result = format_templates(data)

    assert "No templates available" in result


def test_format_templates_with_data():
    """Test format_templates with templates."""
    data = {
        "results": [
            {"id": 1, "name": "Issue template", "type": "issue", "description": "Template for reporting issues"},
            {"id": 2, "name": "Verification", "type": "verification", "description": "Template for verifications"}
        ]
    }
    result = format_templates(data)

    assert "Comment Templates (2)" in result
    assert "| 1 |" in result
    assert "| 2 |" in result
    assert "Issue template" in result
    assert "Verification" in result
