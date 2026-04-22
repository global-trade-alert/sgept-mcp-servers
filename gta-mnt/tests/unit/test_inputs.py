"""Tests for strict Pydantic input validation on gta-mnt tool inputs."""

import pytest
from pydantic import ValidationError

from gta_mnt.server import (
    SetStatusInput,
    GetMeasureInput,
    ListStep1QueueInput,
)


class TestSetStatusInput:
    def test_valid_status_id_accepted(self):
        for sid in (1, 2, 3, 6, 19):
            model = SetStatusInput(state_act_id=1, new_status_id=sid)
            assert model.new_status_id == sid

    def test_invalid_status_id_rejected(self):
        with pytest.raises(ValidationError) as exc:
            SetStatusInput(state_act_id=1, new_status_id=99)
        # The validator message should enumerate valid IDs so the
        # calling agent can recover without a round-trip to docs.
        msg = str(exc.value)
        assert "1, 2, 3, 6, 19" in msg

    def test_extra_field_rejected(self):
        """Silent-drop of stale field names was the main LLM-drift failure mode."""
        with pytest.raises(ValidationError) as exc:
            # `status_id` is a common alias the LLM emits for `new_status_id`.
            # Without extra='forbid' this would succeed with new_status_id defaulting.
            SetStatusInput(state_act_id=1, new_status_id=2, status_id=99)
        assert "extra" in str(exc.value).lower() or "not permitted" in str(exc.value).lower()


class TestGetMeasureInput:
    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            GetMeasureInput(state_act_id=1, include_junk=True)


class TestListStep1QueueInput:
    def test_whitespace_stripped_on_strings(self):
        """str_strip_whitespace=True catches agent-added leading/trailing spaces."""
        model = ListStep1QueueInput(
            implementing_jurisdictions=[" USA ", "CHN\t"],
            date_entered_review_gte=" 2026-01-01 ",
        )
        # List[str] items: pydantic strips each string element.
        assert model.implementing_jurisdictions == ["USA", "CHN"]
        assert model.date_entered_review_gte == "2026-01-01"
