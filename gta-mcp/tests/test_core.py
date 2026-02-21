"""Unit tests for GTA MCP core business logic.

Tests build_filters(), build_count_filters(), HS code lookup,
sector lookup, and Pydantic model validators — all without network calls.
"""

import pytest
from pydantic import ValidationError

from gta_mcp.api import (
    build_filters,
    build_count_filters,
    convert_iso_to_un_codes,
    convert_mast_chapters,
    convert_intervention_types,
    convert_sectors,
    convert_eligible_firms,
    convert_implementation_levels,
    MAST_CHAPTER_TO_ID,
    ISO_TO_UN_CODE,
    GTA_EVALUATION_TO_ID,
)
from gta_mcp.models import (
    GTASearchInput,
    GTAGetInterventionInput,
    GTAImpactChainInput,
    GTACountInput,
    ResponseFormat,
)
from gta_mcp.hs_lookup import search_hs_codes
from gta_mcp.sector_lookup import search_sectors


# ============================================================================
# build_filters() tests
# ============================================================================


class TestBuildFilters:
    """Tests for the primary filter-building function."""

    def test_empty_params(self):
        """Empty params produce default announcement_period only."""
        filters, messages = build_filters({})
        assert filters["announcement_period"] == ["1900-01-01", "2099-12-31"]
        assert len(messages) == 0

    def test_implementing_jurisdictions_iso_to_un(self):
        """ISO codes are converted to UN codes."""
        filters, _ = build_filters({"implementing_jurisdictions": ["USA", "CHN"]})
        assert ISO_TO_UN_CODE["USA"] in filters["implementer"]
        assert ISO_TO_UN_CODE["CHN"] in filters["implementer"]

    def test_affected_jurisdictions(self):
        filters, _ = build_filters({"affected_jurisdictions": ["DEU"]})
        assert ISO_TO_UN_CODE["DEU"] in filters["affected"]

    def test_india_code_anomaly(self):
        """India should map to 699, not 356."""
        filters, _ = build_filters({"implementing_jurisdictions": ["IND"]})
        assert 699 in filters["implementer"]

    def test_evaluation_red(self):
        filters, _ = build_filters({"gta_evaluation": ["Red"]})
        assert 1 in filters["gta_evaluation"]

    def test_evaluation_harmful_expands(self):
        """'Harmful' expands to Red (1) + Amber (2)."""
        filters, _ = build_filters({"gta_evaluation": ["Harmful"]})
        assert 1 in filters["gta_evaluation"]
        assert 2 in filters["gta_evaluation"]

    def test_evaluation_green(self):
        filters, _ = build_filters({"gta_evaluation": ["Green"]})
        assert 3 in filters["gta_evaluation"]

    def test_evaluation_liberalising(self):
        filters, _ = build_filters({"gta_evaluation": ["Liberalising"]})
        assert 3 in filters["gta_evaluation"]

    def test_evaluation_liberalizing_us_spelling(self):
        filters, _ = build_filters({"gta_evaluation": ["Liberalizing"]})
        assert 3 in filters["gta_evaluation"]

    def test_evaluation_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown GTA evaluation"):
            build_filters({"gta_evaluation": ["Purple"]})

    def test_evaluation_dedup(self):
        """Multiple evaluation values that resolve to same ID are deduped."""
        filters, _ = build_filters({"gta_evaluation": ["Red", "Red"]})
        assert filters["gta_evaluation"] == [1]

    def test_mast_chapters_letter_to_id(self):
        """MAST chapter letters are converted to correct non-alphabetical IDs."""
        filters, _ = build_filters({"mast_chapters": ["L"]})
        assert MAST_CHAPTER_TO_ID["L"] in filters["mast_chapters"]
        # L=10, not 12
        assert 10 in filters["mast_chapters"]

    def test_mast_chapters_multiple(self):
        filters, _ = build_filters({"mast_chapters": ["A", "P"]})
        assert MAST_CHAPTER_TO_ID["A"] in filters["mast_chapters"]
        assert MAST_CHAPTER_TO_ID["P"] in filters["mast_chapters"]

    def test_date_announced_gte_only(self):
        filters, _ = build_filters({"date_announced_gte": "2024-01-01"})
        assert filters["announcement_period"] == ["2024-01-01", "2099-12-31"]

    def test_date_announced_lte_only(self):
        filters, _ = build_filters({"date_announced_lte": "2024-12-31"})
        assert filters["announcement_period"] == ["1900-01-01", "2024-12-31"]

    def test_date_announced_both(self):
        filters, _ = build_filters({
            "date_announced_gte": "2024-01-01",
            "date_announced_lte": "2024-12-31"
        })
        assert filters["announcement_period"] == ["2024-01-01", "2024-12-31"]

    def test_implementation_period(self):
        filters, _ = build_filters({"date_implemented_gte": "2025-01-01"})
        assert filters["implementation_period"] == ["2025-01-01", "2099-12-31"]

    def test_update_period(self):
        filters, _ = build_filters({"date_modified_gte": "2026-02-01"})
        assert filters["update_period"][0] == "2026-02-01"

    def test_affected_products_passthrough(self):
        filters, _ = build_filters({"affected_products": [282520, 283691]})
        assert filters["affected_products"] == [282520, 283691]

    def test_query_passthrough(self):
        filters, _ = build_filters({"query": "Tesla"})
        assert filters["query"] == "Tesla"

    def test_intervention_id_passthrough(self):
        filters, _ = build_filters({"intervention_id": [138295, 138296]})
        assert filters["intervention_id"] == [138295, 138296]

    def test_keep_affected_false_generates_message(self):
        filters, messages = build_filters({
            "affected_jurisdictions": ["USA"],
            "keep_affected": False,
        })
        assert filters["keep_affected"] is False
        assert any("Excluding" in m for m in messages)

    def test_keep_affected_true_no_message(self):
        filters, messages = build_filters({
            "affected_jurisdictions": ["USA"],
            "keep_affected": True,
        })
        assert filters["keep_affected"] is True
        assert not any("Excluding" in m for m in messages)

    def test_none_params_ignored(self):
        """None-valued params should not appear in filters."""
        filters, _ = build_filters({
            "implementing_jurisdictions": None,
            "affected_jurisdictions": None,
            "query": None,
        })
        assert "implementer" not in filters
        assert "affected" not in filters
        assert "query" not in filters

    def test_implementation_level_singular_field_name(self):
        """v2 data endpoint uses singular 'implementation_level' field name."""
        filters, _ = build_filters({"implementation_levels": ["National"]})
        # Key should be singular for v2 endpoint
        assert "implementation_level" in filters


# ============================================================================
# build_count_filters() tests
# ============================================================================


class TestBuildCountFilters:
    """Tests for the count-endpoint filter builder."""

    def test_empty_params(self):
        """Empty params produce empty filters (no default announcement_period)."""
        filters, messages = build_count_filters({})
        assert "announcement_period" not in filters
        assert len(messages) == 0

    def test_implementing_jurisdictions(self):
        filters, _ = build_count_filters({"implementing_jurisdictions": ["USA"]})
        assert ISO_TO_UN_CODE["USA"] in filters["implementer"]

    def test_evaluation_red(self):
        filters, _ = build_count_filters({"gta_evaluation": ["Red"]})
        assert 1 in filters["gta_evaluation"]

    def test_revocation_period(self):
        """Count endpoint supports revocation_period (build_filters does not)."""
        filters, _ = build_count_filters({"date_removed_gte": "2024-01-01"})
        assert filters["revocation_period"] == ["2024-01-01", "2099-12-31"]

    def test_affected_flow(self):
        """Count endpoint supports affected_flow."""
        filters, _ = build_count_filters({"affected_flow": [1, 2]})
        assert filters["affected_flow"] == [1, 2]

    def test_implementation_levels_plural_field_name(self):
        """v1 counts endpoint uses plural 'implementation_levels' field name."""
        filters, _ = build_count_filters({"implementation_levels": ["National"]})
        assert "implementation_levels" in filters

    def test_announcement_period_only_when_dates_set(self):
        """Count filters should NOT include default announcement_period."""
        filters, _ = build_count_filters({})
        assert "announcement_period" not in filters

        filters2, _ = build_count_filters({"date_announced_gte": "2024-01-01"})
        assert "announcement_period" in filters2


# ============================================================================
# Conversion function tests
# ============================================================================


class TestConversions:
    """Tests for individual conversion functions."""

    def test_iso_to_un_basic(self):
        codes = convert_iso_to_un_codes(["USA", "CHN", "DEU"])
        assert len(codes) == 3

    def test_iso_to_un_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown ISO"):
            convert_iso_to_un_codes(["ZZZ"])

    def test_mast_chapters_all_letters(self):
        """All valid MAST chapter letters convert without error."""
        for letter in "ABCDEFGHIJKLMNP":
            result = convert_mast_chapters([letter])
            assert len(result) == 1
            assert isinstance(result[0], int)

    def test_mast_chapters_non_sequential(self):
        """Verify the non-alphabetical mapping is correct."""
        assert convert_mast_chapters(["C"]) == [17]
        assert convert_mast_chapters(["L"]) == [10]
        assert convert_mast_chapters(["H"]) == [18]

    def test_mast_chapters_invalid_raises(self):
        with pytest.raises(ValueError):
            convert_mast_chapters(["Z"])

    def test_intervention_types_exact_match(self):
        result = convert_intervention_types(["Import tariff"])
        assert len(result) == 1
        assert isinstance(result[0], int)

    def test_intervention_types_case_insensitive(self):
        result = convert_intervention_types(["import tariff"])
        assert len(result) == 1

    def test_intervention_types_unknown_raises(self):
        with pytest.raises(ValueError):
            convert_intervention_types(["Completely nonexistent type 12345"])


# ============================================================================
# HS code lookup tests
# ============================================================================


class TestHSCodeLookup:
    """Tests for HS code search (local data, no network)."""

    def test_keyword_search_lithium(self):
        result = search_hs_codes("lithium")
        assert "lithium" in result.lower() or "Lithium" in result
        assert "affected_products" in result

    def test_chapter_prefix_28(self):
        """Chapter 28 (inorganic chemicals) search by number."""
        result = search_hs_codes("28")
        assert "28" in result

    def test_code_prefix_8541(self):
        """Heading 8541 (semiconductors) search by code prefix."""
        result = search_hs_codes("8541")
        assert "8541" in result

    def test_no_match_returns_message(self):
        result = search_hs_codes("xyznonexistent12345")
        assert "No matching" in result or "0 results" in result.lower() or "affected_products" not in result

    def test_max_results_respected(self):
        result = search_hs_codes("steel", max_results=5)
        # Count table rows (lines starting with |, excluding header/separator)
        lines = [l for l in result.split("\n") if l.startswith("|") and "---" not in l and "Code" not in l]
        assert len(lines) <= 5


# ============================================================================
# Sector lookup tests
# ============================================================================


class TestSectorLookup:
    """Tests for CPC sector search (local data, no network)."""

    def test_keyword_search_financial(self):
        result = search_sectors("financial")
        assert "financial" in result.lower() or "Financial" in result
        assert "affected_sectors" in result

    def test_code_prefix_71(self):
        """Division 71 (financial services) search by code prefix."""
        result = search_sectors("71")
        assert "71" in result

    def test_no_match(self):
        result = search_sectors("xyznonexistent12345")
        assert "No matching" in result or "0 results" in result.lower() or "affected_sectors" not in result

    def test_transport_search(self):
        result = search_sectors("transport")
        assert "transport" in result.lower() or "Transport" in result


# ============================================================================
# Pydantic model validator tests
# ============================================================================


class TestModelValidators:
    """Tests for Pydantic input model validators."""

    def test_iso_code_auto_uppercase(self):
        """ISO codes should be auto-uppercased."""
        model = GTASearchInput(implementing_jurisdictions=["usa", "chn"])
        assert model.implementing_jurisdictions == ["USA", "CHN"]

    def test_iso_code_already_uppercase(self):
        model = GTASearchInput(implementing_jurisdictions=["USA"])
        assert model.implementing_jurisdictions == ["USA"]

    def test_extra_fields_rejected(self):
        """extra='forbid' should reject unknown parameters."""
        with pytest.raises(ValidationError):
            GTASearchInput(nonexistent_field="value")

    def test_extra_fields_rejected_get_intervention(self):
        with pytest.raises(ValidationError):
            GTAGetInterventionInput(intervention_id=1, unknown="x")

    def test_intervention_id_must_be_positive(self):
        with pytest.raises(ValidationError):
            GTAGetInterventionInput(intervention_id=0)
        with pytest.raises(ValidationError):
            GTAGetInterventionInput(intervention_id=-1)

    def test_granularity_product(self):
        model = GTAImpactChainInput(granularity="product")
        assert model.granularity == "product"

    def test_granularity_sector(self):
        model = GTAImpactChainInput(granularity="sector")
        assert model.granularity == "sector"

    def test_granularity_invalid(self):
        with pytest.raises(ValidationError, match="product.*sector|sector.*product"):
            GTAImpactChainInput(granularity="invalid")

    def test_granularity_case_insensitive(self):
        model = GTAImpactChainInput(granularity="Product")
        assert model.granularity == "product"

    def test_count_by_required(self):
        with pytest.raises(ValidationError):
            GTACountInput()

    def test_count_by_valid_dimension(self):
        model = GTACountInput(count_by=["date_announced_year"])
        assert model.count_by == ["date_announced_year"]

    def test_count_by_invalid_dimension(self):
        with pytest.raises(ValidationError):
            GTACountInput(count_by=["invalid_dimension"])

    def test_default_response_format_markdown(self):
        model = GTASearchInput()
        assert model.response_format == ResponseFormat.MARKDOWN

    def test_default_limit(self):
        model = GTASearchInput()
        assert model.limit == 50

    def test_limit_bounds(self):
        with pytest.raises(ValidationError):
            GTASearchInput(limit=0)
        with pytest.raises(ValidationError):
            GTASearchInput(limit=1001)

    def test_default_sorting(self):
        model = GTASearchInput()
        assert model.sorting == "-date_announced"
