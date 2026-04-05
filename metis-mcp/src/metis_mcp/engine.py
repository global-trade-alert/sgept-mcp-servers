"""Core workflow state machine engine."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .audit import AuditLog
from .gates import evaluate_gate
from .models import (
    Gate,
    GateSchema,
    StepDef,
    StepInput,
    StepOutput,
    StepState,
    StepStatus,
    WorkflowDef,
    WorkflowInstance,
    WorkflowStatus,
)


class EngineError(Exception):
    """Base exception for engine errors."""


class WorkflowNotFoundError(EngineError):
    """Raised when a workflow definition is not found."""


class InstanceNotFoundError(EngineError):
    """Raised when a workflow instance is not found."""


class InvalidAdvanceError(EngineError):
    """Raised when an advance operation is invalid."""


class WorkflowEngine:
    """Deterministic workflow state machine.

    Loads workflow definitions from YAML files, creates instances,
    and advances them through steps with gate validation.
    """

    def __init__(self, audit_log: AuditLog | None = None):
        self._workflows: dict[str, WorkflowDef] = {}
        self._instances: dict[str, WorkflowInstance] = {}
        self._audit = audit_log or AuditLog()

    # ------------------------------------------------------------------
    # Workflow Definition Management
    # ------------------------------------------------------------------

    def load_workflows(self, directory: str | Path) -> int:
        """Load all *.yaml workflow definitions from a directory.

        Returns the number of workflows loaded.
        """
        directory = Path(directory)
        if not directory.is_dir():
            raise EngineError(f"Workflow directory does not exist: {directory}")

        count = 0
        for yaml_file in sorted(directory.glob("*.yaml")):
            self.load_workflow_file(yaml_file)
            count += 1
        return count

    def load_workflow_file(self, path: str | Path) -> WorkflowDef:
        """Load a single workflow definition from a YAML file."""
        path = Path(path)
        with open(path) as f:
            raw = yaml.safe_load(f)

        workflow = self._parse_workflow(raw)
        self._workflows[workflow.id] = workflow
        return workflow

    def _parse_workflow(self, raw: dict[str, Any]) -> WorkflowDef:
        """Parse raw YAML dict into a WorkflowDef model."""
        steps = []
        for step_raw in raw.get("steps", []):
            # Parse gate
            gate = None
            if "gate" in step_raw:
                gate_raw = step_raw["gate"]
                gate = Gate(
                    type=gate_raw.get("type", "schema"),
                    schema=GateSchema(
                        required=gate_raw.get("schema", {}).get("required", [])
                    ),
                )

            step = StepDef(
                id=step_raw["id"],
                name=step_raw["name"],
                actor=step_raw.get("actor", "human"),
                inputs=[StepInput(**i) for i in step_raw.get("inputs", [])],
                outputs=[StepOutput(**o) for o in step_raw.get("outputs", [])],
                gate=gate,
                next=step_raw.get("next", []),
            )
            steps.append(step)

        return WorkflowDef(
            id=raw["id"],
            name=raw["name"],
            version=raw.get("version", 1),
            steps=steps,
        )

    def list_workflows(self) -> list[dict[str, Any]]:
        """Return summaries of all loaded workflows."""
        return [
            {
                "id": w.id,
                "name": w.name,
                "version": w.version,
                "step_count": len(w.steps),
                "steps": [
                    {"id": s.id, "name": s.name, "actor": s.actor} for s in w.steps
                ],
            }
            for w in self._workflows.values()
        ]

    # ------------------------------------------------------------------
    # Instance Management
    # ------------------------------------------------------------------

    def start_workflow(
        self,
        workflow_id: str,
        inputs: dict[str, Any],
        actor: str | None = None,
    ) -> WorkflowInstance:
        """Create and start a new workflow instance.

        Validates that required inputs for the first step are present.
        """
        if workflow_id not in self._workflows:
            raise WorkflowNotFoundError(f"Workflow not found: {workflow_id}")

        workflow = self._workflows[workflow_id]
        first_step = workflow.steps[0]

        # Validate required inputs for first step
        missing = [
            inp.name
            for inp in first_step.inputs
            if inp.required and inp.name not in inputs
        ]
        if missing:
            raise InvalidAdvanceError(
                f"Missing required inputs for step '{first_step.id}': {', '.join(missing)}"
            )

        instance_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Initialize step states
        step_states = {}
        for step in workflow.steps:
            step_states[step.id] = StepState(status=StepStatus.PENDING)
        step_states[first_step.id] = StepState(status=StepStatus.IN_PROGRESS)

        instance = WorkflowInstance(
            instance_id=instance_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            current_step_id=first_step.id,
            step_states=step_states,
            inputs=inputs,
            created_at=now,
            updated_at=now,
            correlation_id=correlation_id,
        )

        self._instances[instance_id] = instance

        self._audit.log(
            event="workflow_started",
            correlation_id=correlation_id,
            instance_id=instance_id,
            details={
                "workflow_id": workflow_id,
                "first_step": first_step.id,
                "inputs": inputs,
            },
        )

        return instance

    def advance(
        self,
        instance_id: str,
        step_output: dict[str, Any],
    ) -> dict[str, Any]:
        """Advance a workflow instance by completing the current step.

        Validates the step output against the gate, then transitions
        to the next step or completes the workflow.

        Returns a dict with the result details.
        """
        if instance_id not in self._instances:
            raise InstanceNotFoundError(f"Instance not found: {instance_id}")

        instance = self._instances[instance_id]

        if instance.status != WorkflowStatus.RUNNING:
            raise InvalidAdvanceError(
                f"Cannot advance instance in status '{instance.status.value}'"
            )

        workflow = self._workflows[instance.workflow_id]
        current_step = workflow.get_step(instance.current_step_id)
        if current_step is None:
            raise EngineError(f"Step not found: {instance.current_step_id}")

        current_state = instance.step_states[current_step.id]
        if current_state.status != StepStatus.IN_PROGRESS:
            raise InvalidAdvanceError(
                f"Step '{current_step.id}' is not in_progress "
                f"(status: {current_state.status.value})"
            )

        # Evaluate gate
        gate_result = evaluate_gate(current_step.gate, step_output)

        if not gate_result.passed:
            self._audit.log(
                event="gate_failed",
                correlation_id=instance.correlation_id,
                instance_id=instance_id,
                details={
                    "step_id": current_step.id,
                    "errors": gate_result.errors,
                    "output_keys": list(step_output.keys()),
                },
            )
            return {
                "status": "gate_failed",
                "step_id": current_step.id,
                "errors": gate_result.errors,
            }

        # Gate passed — mark step completed
        self._audit.log(
            event="gate_passed",
            correlation_id=instance.correlation_id,
            instance_id=instance_id,
            details={"step_id": current_step.id},
        )

        current_state.status = StepStatus.COMPLETED
        current_state.output = step_output
        instance.updated_at = datetime.now(timezone.utc)

        self._audit.log(
            event="step_advanced",
            correlation_id=instance.correlation_id,
            instance_id=instance_id,
            details={
                "step_id": current_step.id,
                "output_keys": list(step_output.keys()),
            },
        )

        # Determine next step
        if not current_step.next:
            # No next steps — workflow complete
            instance.status = WorkflowStatus.COMPLETED
            self._audit.log(
                event="workflow_completed",
                correlation_id=instance.correlation_id,
                instance_id=instance_id,
                details={"workflow_id": instance.workflow_id},
            )
            return {
                "status": "completed",
                "workflow_id": instance.workflow_id,
                "instance_id": instance_id,
            }

        # Move to first next step
        next_step_id = current_step.next[0]
        next_step = workflow.get_step(next_step_id)
        if next_step is None:
            raise EngineError(f"Next step not found: {next_step_id}")

        instance.current_step_id = next_step_id
        instance.step_states[next_step_id].status = StepStatus.IN_PROGRESS

        return {
            "status": "advanced",
            "completed_step": current_step.id,
            "current_step": {
                "id": next_step.id,
                "name": next_step.name,
                "actor": next_step.actor,
                "inputs": [i.name for i in next_step.inputs],
                "outputs": [o.name for o in next_step.outputs],
            },
            "instance_id": instance_id,
        }

    def get_state(self, instance_id: str) -> dict[str, Any]:
        """Return full instance state as a serializable dict."""
        if instance_id not in self._instances:
            raise InstanceNotFoundError(f"Instance not found: {instance_id}")

        instance = self._instances[instance_id]
        workflow = self._workflows.get(instance.workflow_id)

        return {
            "instance_id": instance.instance_id,
            "workflow_id": instance.workflow_id,
            "workflow_name": workflow.name if workflow else "unknown",
            "status": instance.status.value,
            "current_step_id": instance.current_step_id,
            "step_states": {
                step_id: {
                    "status": state.status.value,
                    "output": state.output,
                }
                for step_id, state in instance.step_states.items()
            },
            "inputs": instance.inputs,
            "created_at": instance.created_at.isoformat(),
            "updated_at": instance.updated_at.isoformat(),
            "correlation_id": instance.correlation_id,
        }

    def list_instances(
        self,
        status: str | None = None,
        workflow_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List workflow instances, optionally filtered."""
        results = []
        for instance in self._instances.values():
            if status and instance.status.value != status:
                continue
            if workflow_id and instance.workflow_id != workflow_id:
                continue
            results.append(
                {
                    "instance_id": instance.instance_id,
                    "workflow_id": instance.workflow_id,
                    "status": instance.status.value,
                    "current_step_id": instance.current_step_id,
                    "created_at": instance.created_at.isoformat(),
                    "updated_at": instance.updated_at.isoformat(),
                }
            )
        return results
