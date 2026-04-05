"""Quality gate evaluation for workflow steps."""

from __future__ import annotations

from typing import Any

from .models import Gate


class GateResult:
    """Result of a gate evaluation."""

    def __init__(self, passed: bool, errors: list[str] | None = None):
        self.passed = passed
        self.errors = errors or []

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "errors": self.errors}


def evaluate_gate(gate: Gate | None, output: dict[str, Any]) -> GateResult:
    """Evaluate a quality gate against step output.

    Currently supports 'schema' gates which check for required keys.
    Returns GateResult with pass/fail and error details.
    """
    if gate is None:
        return GateResult(passed=True)

    if gate.type == "schema":
        missing = [
            key
            for key in gate.schema_def.required
            if key not in output or output[key] is None
        ]
        if missing:
            return GateResult(
                passed=False,
                errors=[f"Missing required output(s): {', '.join(missing)}"],
            )
        # Check for empty string values
        empty = [
            key
            for key in gate.schema_def.required
            if key in output
            and isinstance(output[key], str)
            and output[key].strip() == ""
        ]
        if empty:
            return GateResult(
                passed=False,
                errors=[f"Empty required output(s): {', '.join(empty)}"],
            )
        return GateResult(passed=True)

    return GateResult(passed=False, errors=[f"Unknown gate type: {gate.type}"])
