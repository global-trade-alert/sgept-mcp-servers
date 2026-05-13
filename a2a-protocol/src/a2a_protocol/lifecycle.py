"""A2A 8-state task lifecycle + transition validator.

Per the A2A spec:
    submitted → working → (input-required ↔ working)* → terminal
    terminal ∈ {completed, failed, canceled, rejected}
    auth-required is reachable from working if the backend needs credentials mid-task.
"""

from __future__ import annotations

from enum import Enum


class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    REJECTED = "rejected"
    AUTH_REQUIRED = "auth-required"


TERMINAL_STATES = frozenset(
    {TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED, TaskState.REJECTED}
)


# Adjacency list of legal transitions. `from -> {to, ...}`.
# Source: A2A v1.0 spec, "Task lifecycle" section.
_TRANSITIONS: dict[TaskState, frozenset[TaskState]] = {
    TaskState.SUBMITTED: frozenset({
        TaskState.WORKING,
        TaskState.CANCELED,
        TaskState.REJECTED,
        TaskState.AUTH_REQUIRED,
    }),
    TaskState.WORKING: frozenset({
        TaskState.WORKING,         # idempotent progress updates
        TaskState.INPUT_REQUIRED,
        TaskState.AUTH_REQUIRED,
        TaskState.COMPLETED,
        TaskState.FAILED,
        TaskState.CANCELED,
    }),
    TaskState.INPUT_REQUIRED: frozenset({
        TaskState.WORKING,         # caller responded; resume
        TaskState.CANCELED,
        TaskState.REJECTED,        # too many round-trips
        TaskState.FAILED,
    }),
    TaskState.AUTH_REQUIRED: frozenset({
        TaskState.WORKING,         # auth provided; resume
        TaskState.CANCELED,
        TaskState.REJECTED,
        TaskState.FAILED,
    }),
    # Terminal states have no outgoing transitions.
    TaskState.COMPLETED: frozenset(),
    TaskState.FAILED: frozenset(),
    TaskState.CANCELED: frozenset(),
    TaskState.REJECTED: frozenset(),
}


def is_valid_transition(from_state: TaskState, to_state: TaskState) -> bool:
    """True iff the A2A spec allows from_state → to_state."""
    return to_state in _TRANSITIONS[from_state]


def is_terminal(state: TaskState) -> bool:
    return state in TERMINAL_STATES
