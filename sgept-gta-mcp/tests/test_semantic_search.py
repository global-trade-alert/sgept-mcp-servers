"""Tests for GTASemanticSearchInput model and show_keys projection.

Covers all acceptance criteria from issue 059:
- GTASemanticSearchInput.limit accepts new ceiling (100)
- Values above ceiling raise ValidationError
- Default limit=20 preserved
- show_keys plumbed through (validated on the model)
- show_keys=["intervention_id", "score"] omits blurb, url, publication_date, title
- show_keys=["*"] returns full record
- Pre-existing callers (default params) produce correct defaults
"""

import pytest
from pydantic import ValidationError

from gta_mcp.models import GTASemanticSearchInput, ResponseFormat, SEMANTIC_SEARCH_SHOW_KEYS_AVAILABLE
from gta_mcp.formatters import apply_show_keys_projection


# ---------------------------------------------------------------------------
# GTASemanticSearchInput validation
# ---------------------------------------------------------------------------


class TestGTASemanticSearchInputValidation:

    def test_minimal_valid(self):
        m = GTASemanticSearchInput(query="trade barriers")
        assert m.query == "trade barriers"
        assert m.limit == 20
        assert m.intervention_ids is None
        assert m.show_keys is None
        assert m.response_format == ResponseFormat.MARKDOWN

    def test_limit_default_20(self):
        m = GTASemanticSearchInput(query="test")
        assert m.limit == 20

    def test_limit_new_ceiling_100(self):
        m = GTASemanticSearchInput(query="test", limit=100)
        assert m.limit == 100

    def test_limit_above_ceiling_raises(self):
        with pytest.raises(ValidationError):
            GTASemanticSearchInput(query="test", limit=101)

    def test_limit_zero_raises(self):
        with pytest.raises(ValidationError):
            GTASemanticSearchInput(query="test", limit=0)

    def test_limit_negative_raises(self):
        with pytest.raises(ValidationError):
            GTASemanticSearchInput(query="test", limit=-1)

    def test_limit_50_valid(self):
        m = GTASemanticSearchInput(query="test", limit=50)
        assert m.limit == 50

    def test_limit_1_valid(self):
        m = GTASemanticSearchInput(query="test", limit=1)
        assert m.limit == 1

    def test_empty_query_raises(self):
        with pytest.raises(ValidationError):
            GTASemanticSearchInput(query="")

    def test_query_whitespace_stripped(self):
        m = GTASemanticSearchInput(query="  hello  ")
        assert m.query == "hello"

    def test_intervention_ids_stored(self):
        m = GTASemanticSearchInput(query="test", intervention_ids=[1, 2, 3])
        assert m.intervention_ids == [1, 2, 3]

    def test_show_keys_stored(self):
        m = GTASemanticSearchInput(query="test", show_keys=["intervention_id", "score"])
        assert m.show_keys == ["intervention_id", "score"]

    def test_show_keys_star(self):
        m = GTASemanticSearchInput(query="test", show_keys=["*"])
        assert m.show_keys == ["*"]

    def test_show_keys_none_default(self):
        m = GTASemanticSearchInput(query="test")
        assert m.show_keys is None

    def test_response_format_json(self):
        m = GTASemanticSearchInput(query="test", response_format="json")
        assert m.response_format == ResponseFormat.JSON

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            GTASemanticSearchInput(query="test", unknown_field="x")


# ---------------------------------------------------------------------------
# show_keys projection on semantic search records
# ---------------------------------------------------------------------------


_FULL_RECORD = {
    "intervention_id": 12345,
    "title": "Export Control on Semiconductors",
    "score": 0.9123,
    "blurb": "This measure restricts exports of advanced chips.",
    "url": "https://example.com/intervention/12345",
    "publication_date": "2024-03-01",
}


class TestSemanticShowKeysProjection:
    """Verify show_keys projection on semantic search result records."""

    def test_show_keys_none_returns_full(self):
        result = apply_show_keys_projection(_FULL_RECORD, None)
        assert result == _FULL_RECORD

    def test_show_keys_star_returns_full(self):
        result = apply_show_keys_projection(_FULL_RECORD, ["*"])
        assert result == _FULL_RECORD

    def test_show_keys_id_and_score_omits_others(self):
        result = apply_show_keys_projection(_FULL_RECORD, ["intervention_id", "score"])
        assert set(result.keys()) == {"intervention_id", "score"}
        assert "blurb" not in result
        assert "url" not in result
        assert "publication_date" not in result
        assert "title" not in result

    def test_show_keys_id_and_score_values_preserved(self):
        result = apply_show_keys_projection(_FULL_RECORD, ["intervention_id", "score"])
        assert result["intervention_id"] == 12345
        assert result["score"] == 0.9123

    def test_show_keys_unknown_field_silently_dropped(self):
        result = apply_show_keys_projection(_FULL_RECORD, ["intervention_id", "nonexistent_field"])
        assert "nonexistent_field" not in result
        assert "intervention_id" in result

    def test_show_keys_empty_list_returns_empty(self):
        result = apply_show_keys_projection(_FULL_RECORD, [])
        assert result == {}

    def test_pre_existing_caller_no_show_keys_gets_full_record(self):
        """Default caller (no show_keys) should get byte-identical full record."""
        result = apply_show_keys_projection(_FULL_RECORD, None)
        assert result is _FULL_RECORD  # same object reference when no projection applied


# ---------------------------------------------------------------------------
# SEMANTIC_SEARCH_SHOW_KEYS_AVAILABLE sanity check
# ---------------------------------------------------------------------------


def test_show_keys_available_contains_expected_fields():
    expected = {"intervention_id", "title", "score", "blurb", "url", "publication_date"}
    assert expected.issubset(set(SEMANTIC_SEARCH_SHOW_KEYS_AVAILABLE))
