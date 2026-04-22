"""Tests for strict Pydantic input validation on dpa-mnt tool inputs."""

import pytest
from pydantic import ValidationError

from dpa_mnt.server import (
    SetStatusInput,
    GetEventInput,
    ListReviewQueueInput,
    AddCommentInput,
    AddReviewTagInput,
    GetInterventionContextInput,
)


class TestSetStatusInput:
    def test_valid_status_id_accepted(self):
        # Valid DPA event status IDs from lux_event_status_list:
        # 1=In Progress, 2=Step 1 review (AT), 3=Publishable (legacy),
        # 4=AT concern, 5=AT under revision, 6=AT revised, 7=Published,
        # 14=Archived. The review workflow uses 4/5/6/14 as verdict outcomes.
        for sid in (1, 2, 3, 4, 5, 6, 7, 14):
            model = SetStatusInput(event_id=42, new_status_id=sid)
            assert model.new_status_id == sid

    def test_invalid_status_id_rejected(self):
        with pytest.raises(ValidationError) as exc:
            SetStatusInput(event_id=42, new_status_id=99)
        msg = str(exc.value)
        # The validator message enumerates every valid id=name pair so the
        # calling agent can recover without a round-trip to docs.
        assert "1, 2, 3, 4, 5, 6, 7, 14" in msg
        assert "Archived" in msg

    def test_status_id_19_rejected(self):
        # 19 is GTA's 'Step 2' status but NOT a valid DPA status.
        # This catches accidental cross-wiring between the sibling servers.
        with pytest.raises(ValidationError):
            SetStatusInput(event_id=42, new_status_id=19)

    def test_extra_field_rejected(self):
        """Silent-drop of stale field names was the main LLM-drift failure mode."""
        with pytest.raises(ValidationError) as exc:
            # `status_id` is a common alias the LLM emits for `new_status_id`.
            # Without extra='forbid' this would succeed with new_status_id=3
            # and status_id being silently dropped.
            SetStatusInput(event_id=42, new_status_id=3, status_id=99)
        assert "extra" in str(exc.value).lower() or "not permitted" in str(exc.value).lower()

    def test_measure_id_alias_rejected(self):
        # `measure_id` is the GTA name for the ID field. DPA uses `event_id`.
        # A cross-wired agent call must fail loudly, not silently succeed.
        with pytest.raises(ValidationError):
            SetStatusInput(measure_id=42, new_status_id=3)


class TestGetEventInput:
    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            GetEventInput(event_id=1, include_junk=True)

    def test_defaults(self):
        model = GetEventInput(event_id=1)
        assert model.include_intervention is True
        assert model.include_comments is True


class TestListReviewQueueInput:
    def test_whitespace_stripped_on_strings(self):
        """str_strip_whitespace=True catches agent-added leading/trailing spaces."""
        model = ListReviewQueueInput(
            implementing_jurisdictions=[" USA ", "CHN\t"],
            date_entered_review_gte=" 2026-01-01 ",
        )
        assert model.implementing_jurisdictions == ["USA", "CHN"]
        assert model.date_entered_review_gte == "2026-01-01"

    def test_limit_bounds(self):
        with pytest.raises(ValidationError):
            ListReviewQueueInput(limit=0)
        with pytest.raises(ValidationError):
            ListReviewQueueInput(limit=101)
        # Inside bounds is fine.
        ListReviewQueueInput(limit=1)
        ListReviewQueueInput(limit=100)


class TestAddCommentInput:
    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            AddCommentInput(event_id=1, comment_text="x", author_id=9999)


class TestAddReviewTagInput:
    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            AddReviewTagInput(event_id=1, issue_id=83)


class TestGetInterventionContextInput:
    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            GetInterventionContextInput(intervention_id=1, include_events=True)
