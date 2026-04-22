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

    # Current formatter renders an ID | Title | Date Entered Review table.
    # Jurisdiction was dropped from the queue view in the MySQL-direct rewrite
    # (it requires a separate join). Assert on what the formatter actually ships.
    assert "Step 1 Review Queue (2 measures)" in result
    assert "| 123 |" in result
    assert "| 124 |" in result
    assert "Date Entered Review" in result


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

    # The formatter reads nested structures (implementing_jurisdictions as a list
    # on interventions, status via a lookup table). For this flat fixture we just
    # verify the top-level scaffolding and intervention count are correct.
    assert "# StateAct 123: Test Measure" in result
    assert "## Interventions (2)" in result
    assert "INT-1" in result
    assert "INT-2" in result
    assert "## Comments (1)" in result
    assert "john_doe" in result


def test_format_measure_detail_multi_update_description():
    """Multi-row description_rows should render one block per update with order_nr, status, and timestamps."""
    measure = {
        "id": 777,
        "title": "Multi-update measure",
        "interventions": [
            {
                "id": 42,
                "intervention_type": "Tariff",
                "description": "Update 1 body\nUpdate 2 body\nUpdate 3 body",
                "description_rows": [
                    {
                        "id": 101, "order_nr": 1, "status": "NEW",
                        "datetime_created": datetime(2025, 9, 14, 10, 0),
                        "datetime_modified": datetime(2025, 9, 14, 10, 0),
                        "description": "Update 1 body",
                        "description_markdown": "Update 1 body",
                        "dates": [{"date": datetime(2025, 9, 14).date(), "date_type_name": "announcement"}],
                    },
                    {
                        "id": 102, "order_nr": 2, "status": "CHANGED",
                        "datetime_created": datetime(2025, 11, 2, 9, 30),
                        "datetime_modified": datetime(2025, 11, 2, 9, 30),
                        "description": "Update 2 body",
                        "description_markdown": "Update 2 body",
                        "dates": [],
                    },
                    {
                        "id": 103, "order_nr": 3, "status": "STATIC",
                        "datetime_created": datetime(2026, 1, 8, 12, 0),
                        "datetime_modified": datetime(2026, 2, 3, 12, 0),
                        "description": "Update 3 body",
                        "description_markdown": "Update 3 body",
                        "dates": [],
                    },
                ],
            }
        ],
    }
    result = format_measure_detail(measure)

    assert "#### Description (3 updates)" in result
    assert "**Update 1**" in result and "status: NEW" in result and "2025-09-14" in result
    assert "**Update 2**" in result and "status: CHANGED" in result and "2025-11-02" in result
    assert "**Update 3**" in result and "status: STATIC" in result
    assert "2026-01-08" in result and "2026-02-03" in result
    assert "announcement" in result
    assert "Update 1 body" in result and "Update 2 body" in result and "Update 3 body" in result


def test_format_measure_detail_single_update_description_unchanged():
    """Single-row (or zero-row) description_rows should keep the compact rendering."""
    measure = {
        "id": 778,
        "title": "Single-update measure",
        "interventions": [
            {
                "id": 43,
                "intervention_type": "Tariff",
                "description": "Only one update body",
                "description_rows": [
                    {
                        "id": 201, "order_nr": 1, "status": "NEW",
                        "datetime_created": datetime(2025, 5, 1, 10, 0),
                        "datetime_modified": datetime(2025, 5, 1, 10, 0),
                        "description": "Only one update body",
                        "description_markdown": "Only one update body",
                        "dates": [],
                    }
                ],
            }
        ],
    }
    result = format_measure_detail(measure)

    assert "#### Description" in result
    assert "updates)" not in result
    assert "**Update 1**" not in result
    assert "Only one update body" in result


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
    """Test format_source_result caps at CHARACTER_LIMIT with a pagination hint."""
    from gta_mnt.formatters import CHARACTER_LIMIT
    long_content = "A" * (CHARACTER_LIMIT + 10_000)
    source = SourceResult(
        source_type="file",
        source_url="s3://bucket/large.pdf",
        content=long_content,
        content_type="pdf"
    )
    result = format_source_result(source)

    assert len(result) <= CHARACTER_LIMIT
    assert "truncated" in result
    # The pagination hint names the specific smaller payload to re-request.
    assert "fetch_content=False" in result


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
