"""Lifecycle: 8 states + transition validator."""

from __future__ import annotations

import pytest

from a2a_protocol.lifecycle import TaskState, is_terminal, is_valid_transition


def test_eight_states_present():
    assert {s.value for s in TaskState} == {
        "submitted", "working", "input-required",
        "completed", "failed", "canceled", "rejected", "auth-required",
    }


def test_terminal_states():
    assert is_terminal(TaskState.COMPLETED)
    assert is_terminal(TaskState.FAILED)
    assert is_terminal(TaskState.CANCELED)
    assert is_terminal(TaskState.REJECTED)
    assert not is_terminal(TaskState.WORKING)
    assert not is_terminal(TaskState.INPUT_REQUIRED)


@pytest.mark.parametrize("frm,to,ok", [
    (TaskState.SUBMITTED, TaskState.WORKING, True),
    (TaskState.SUBMITTED, TaskState.COMPLETED, False),     # must go through working
    (TaskState.WORKING, TaskState.INPUT_REQUIRED, True),
    (TaskState.WORKING, TaskState.COMPLETED, True),
    (TaskState.INPUT_REQUIRED, TaskState.WORKING, True),
    (TaskState.INPUT_REQUIRED, TaskState.REJECTED, True),
    (TaskState.COMPLETED, TaskState.WORKING, False),       # terminal — no exit
    (TaskState.CANCELED, TaskState.WORKING, False),
    (TaskState.WORKING, TaskState.WORKING, True),          # idempotent progress
])
def test_transitions(frm, to, ok):
    assert is_valid_transition(frm, to) is ok


def test_terminal_states_have_no_transitions():
    for terminal in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED, TaskState.REJECTED):
        for any_state in TaskState:
            assert is_valid_transition(terminal, any_state) is False
