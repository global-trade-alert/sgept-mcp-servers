"""Tests for GTAGetInterventionInput model and multi-record formatter.

Covers all acceptance criteria from issue 057:
- Pydantic validation (both/neither/unknown show_keys)
- apply_show_keys_projection
- format_interventions_batch_markdown / format_interventions_batch_json
"""

import json
import pytest
from pydantic import ValidationError

from gta_mcp.models import GTAGetInterventionInput, ResponseFormat
from gta_mcp.formatters import (
    apply_show_keys_projection,
    format_interventions_batch_markdown,
    format_interventions_batch_json,
)


# ---------------------------------------------------------------------------
# Pydantic model validator tests
# ---------------------------------------------------------------------------


class TestGTAGetInterventionInputValidation:
    """Pydantic validation cases (no network)."""

    def test_single_id_valid(self):
        m = GTAGetInterventionInput(intervention_id=138295)
        assert m.intervention_id == 138295
        assert m.intervention_ids is None

    def test_batch_ids_valid(self):
        m = GTAGetInterventionInput(intervention_ids=[138295, 138296])
        assert m.intervention_ids == [138295, 138296]
        assert m.intervention_id is None

    def test_both_set_raises(self):
        with pytest.raises(ValidationError, match="not both"):
            GTAGetInterventionInput(intervention_id=1, intervention_ids=[2, 3])

    def test_neither_set_raises(self):
        with pytest.raises(ValidationError):
            GTAGetInterventionInput()

    def test_intervention_id_zero_raises(self):
        with pytest.raises(ValidationError):
            GTAGetInterventionInput(intervention_id=0)

    def test_intervention_id_negative_raises(self):
        with pytest.raises(ValidationError):
            GTAGetInterventionInput(intervention_id=-5)

    def test_batch_ids_with_zero_raises(self):
        with pytest.raises(ValidationError):
            GTAGetInterventionInput(intervention_ids=[138295, 0])

    def test_batch_ids_with_negative_raises(self):
        with pytest.raises(ValidationError):
            GTAGetInterventionInput(intervention_ids=[-1])

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            GTAGetInterventionInput(intervention_id=1, unknown_field="x")

    def test_show_keys_stored(self):
        m = GTAGetInterventionInput(intervention_id=1, show_keys=["title", "gta_evaluation"])
        assert m.show_keys == ["title", "gta_evaluation"]

    def test_show_keys_star(self):
        m = GTAGetInterventionInput(intervention_id=1, show_keys=["*"])
        assert m.show_keys == ["*"]

    def test_show_keys_none_default(self):
        m = GTAGetInterventionInput(intervention_id=1)
        assert m.show_keys is None

    def test_default_response_format_markdown(self):
        m = GTAGetInterventionInput(intervention_id=1)
        assert m.response_format == ResponseFormat.MARKDOWN


# ---------------------------------------------------------------------------
# apply_show_keys_projection tests
# ---------------------------------------------------------------------------


class TestApplyShowKeysProjection:
    """Field projection unit tests."""

    _record = {
        "intervention_id": 1,
        "state_act_title": "Test",
        "gta_evaluation": "Red",
        "intervention_description": "long text",
        "date_announced": "2024-01-01",
    }

    def test_none_returns_full(self):
        result = apply_show_keys_projection(self._record, None)
        assert result == self._record

    def test_star_returns_full(self):
        result = apply_show_keys_projection(self._record, ["*"])
        assert result == self._record

    def test_specific_keys(self):
        result = apply_show_keys_projection(
            self._record, ["intervention_id", "gta_evaluation"]
        )
        assert set(result.keys()) == {"intervention_id", "gta_evaluation"}
        assert result["intervention_id"] == 1
        assert result["gta_evaluation"] == "Red"

    def test_unknown_key_silently_dropped(self):
        result = apply_show_keys_projection(self._record, ["intervention_id", "nonexistent"])
        assert "nonexistent" not in result
        assert "intervention_id" in result

    def test_empty_show_keys_returns_empty_dict(self):
        result = apply_show_keys_projection(self._record, [])
        assert result == {}


# ---------------------------------------------------------------------------
# Multi-record formatter tests
# ---------------------------------------------------------------------------


_RECORD_A = {
    "intervention_id": 100,
    "state_act_title": "Measure A",
    "gta_evaluation": "Red",
    "intervention_type": "Import tariff",
    "mast_chapter": "F",
    "implementation_level": "National",
    "eligible_firm": "All",
    "is_in_force": True,
    "date_announced": "2024-06-01",
    "date_implemented": "2024-07-01",
    "date_removed": None,
    "implementing_jurisdictions": [{"name": "Germany", "iso": "DEU"}],
    "affected_jurisdictions": [],
    "affected_products": [],
    "affected_sectors": [],
    "intervention_description": "Description of measure A.",
    "state_act_source": "Official source A",
    "intervention_url": "https://globaltradealert.org/intervention/100",
    "state_act_url": "https://globaltradealert.org/state-act/100",
    "is_official_source": True,
    "state_act_id": 200,
}

_RECORD_B = {
    "intervention_id": 101,
    "state_act_title": "Measure B",
    "gta_evaluation": "Green",
    "intervention_type": "Export subsidy",
    "mast_chapter": "P",
    "implementation_level": "National",
    "eligible_firm": "All",
    "is_in_force": False,
    "date_announced": "2023-01-01",
    "date_implemented": None,
    "date_removed": "2024-01-01",
    "implementing_jurisdictions": [],
    "affected_jurisdictions": [],
    "affected_products": [],
    "affected_sectors": [],
    "intervention_description": None,
    "state_act_source": None,
    "intervention_url": "https://globaltradealert.org/intervention/101",
    "state_act_url": "https://globaltradealert.org/state-act/101",
    "is_official_source": False,
    "state_act_id": 201,
}


class TestFormatInterventionsBatchMarkdown:

    def test_two_records_contain_both_titles(self):
        result = format_interventions_batch_markdown([_RECORD_A, _RECORD_B], [])
        assert "Measure A" in result
        assert "Measure B" in result

    def test_preserves_input_order(self):
        result = format_interventions_batch_markdown([_RECORD_A, _RECORD_B], [])
        pos_a = result.index("Measure A")
        pos_b = result.index("Measure B")
        assert pos_a < pos_b

    def test_errors_appended(self):
        errors = [{"intervention_id": 999, "error": "not found"}]
        result = format_interventions_batch_markdown([_RECORD_A], errors)
        assert "999" in result
        assert "not found" in result.lower()

    def test_no_results_no_errors_returns_error_message(self):
        result = format_interventions_batch_markdown([], [])
        assert "No interventions" in result

    def test_projection_applied(self):
        result = format_interventions_batch_markdown(
            [_RECORD_A], [], show_keys=["intervention_id", "state_act_title"]
        )
        assert "Measure A" in result
        assert "Description of measure A" not in result

    def test_single_record_no_record_header(self):
        result = format_interventions_batch_markdown([_RECORD_A], [])
        assert "Record 1 of 1" not in result

    def test_multiple_records_have_record_headers(self):
        result = format_interventions_batch_markdown([_RECORD_A, _RECORD_B], [])
        assert "Record 1 of 2" in result
        assert "Record 2 of 2" in result


class TestFormatInterventionsBatchJson:

    def test_returns_valid_json(self):
        result = format_interventions_batch_json([_RECORD_A, _RECORD_B], [])
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_count_field(self):
        result = format_interventions_batch_json([_RECORD_A, _RECORD_B], [])
        parsed = json.loads(result)
        assert parsed["count"] == 2

    def test_results_field(self):
        result = format_interventions_batch_json([_RECORD_A], [])
        parsed = json.loads(result)
        assert len(parsed["results"]) == 1

    def test_errors_included_when_present(self):
        errors = [{"intervention_id": 999, "error": "not found"}]
        result = format_interventions_batch_json([_RECORD_A], errors)
        parsed = json.loads(result)
        assert "errors" in parsed
        assert parsed["errors"][0]["intervention_id"] == 999

    def test_no_errors_key_when_empty(self):
        result = format_interventions_batch_json([_RECORD_A], [])
        parsed = json.loads(result)
        assert "errors" not in parsed

    def test_projection_in_json(self):
        result = format_interventions_batch_json(
            [_RECORD_A], [], show_keys=["intervention_id", "gta_evaluation"]
        )
        parsed = json.loads(result)
        rec = parsed["results"][0]
        assert set(rec.keys()) == {"intervention_id", "gta_evaluation"}

    def test_star_show_keys_returns_all_fields(self):
        result = format_interventions_batch_json([_RECORD_A], [], show_keys=["*"])
        parsed = json.loads(result)
        rec = parsed["results"][0]
        assert "intervention_description" in rec

    def test_markdown_and_json_project_same_keys(self):
        keys = ["intervention_id", "state_act_title", "gta_evaluation"]
        md = format_interventions_batch_markdown([_RECORD_A], [], show_keys=keys)
        js = format_interventions_batch_json([_RECORD_A], [], show_keys=keys)
        parsed = json.loads(js)
        rec = parsed["results"][0]
        assert set(rec.keys()) == set(keys)
        # Markdown contains title (projected key)
        assert "Measure A" in md
        # Markdown does NOT contain description (not in projection)
        assert "Description of measure A" not in md
