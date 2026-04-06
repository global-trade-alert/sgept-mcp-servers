"""Core workflow state machine engine."""

from __future__ import annotations

import json
import logging
import os
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

logger = logging.getLogger(__name__)


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

    def __init__(
        self,
        audit_log: AuditLog | None = None,
        persistence_dir: str | Path | None = None,
    ):
        self._workflows: dict[str, WorkflowDef] = {}
        self._instances: dict[str, WorkflowInstance] = {}
        self._audit = audit_log or AuditLog()

        # Resolve persistence directory: explicit param > env var > None (disabled)
        if persistence_dir is None:
            persistence_dir = os.environ.get("METIS_PERSISTENCE_DIR")
        if persistence_dir is not None:
            self._persistence_dir: Path | None = Path(persistence_dir)
            self._persistence_dir.mkdir(parents=True, exist_ok=True)
            (self._persistence_dir / "completed").mkdir(exist_ok=True)
            self._load_instances()
        else:
            self._persistence_dir = None

    # ------------------------------------------------------------------
    # Instance Persistence
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_instance(instance: WorkflowInstance) -> dict:
        """Serialize a WorkflowInstance to a JSON-compatible dict."""
        data = instance.model_dump()
        for key in ("created_at", "updated_at"):
            if isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        data["status"] = instance.status.value
        for step_id, state in data["step_states"].items():
            state["status"] = instance.step_states[step_id].status.value
        return data

    @staticmethod
    def _deserialize_instance(data: dict) -> WorkflowInstance:
        """Reconstruct a WorkflowInstance from a serialized dict."""
        for key in ("created_at", "updated_at"):
            if isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        data["status"] = WorkflowStatus(data["status"])
        step_states = {}
        for step_id, state_data in data["step_states"].items():
            step_states[step_id] = StepState(
                status=StepStatus(state_data["status"]),
                output=state_data.get("output", {}),
            )
        data["step_states"] = step_states
        return WorkflowInstance(**data)

    def _save_instance(self, instance_id: str) -> None:
        """Persist a workflow instance to disk as JSON (atomic write)."""
        if self._persistence_dir is None:
            return
        instance = self._instances.get(instance_id)
        if instance is None:
            return

        data = self._serialize_instance(instance)
        target = self._persistence_dir / f"{instance_id}.json"
        tmp = self._persistence_dir / f"{instance_id}.json.tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        tmp.rename(target)

    def _load_instances(self) -> None:
        """Load all persisted workflow instances from disk."""
        if self._persistence_dir is None:
            return
        count = 0
        for json_file in self._persistence_dir.glob("*.json"):
            if json_file.name.endswith(".tmp"):
                continue
            try:
                with open(json_file) as f:
                    data = json.load(f)
                instance = self._deserialize_instance(data)
                self._instances[instance.instance_id] = instance
                count += 1
            except Exception:
                logger.warning("Failed to load instance from %s", json_file, exc_info=True)
        if count:
            logger.info("Loaded %d persisted workflow instance(s)", count)

    def _delete_instance(self, instance_id: str) -> None:
        """Move a completed instance file to the completed/ subdirectory."""
        if self._persistence_dir is None:
            return
        source = self._persistence_dir / f"{instance_id}.json"
        if source.exists():
            dest = self._persistence_dir / "completed" / f"{instance_id}.json"
            source.rename(dest)

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
            if yaml_file.name.startswith("_"):
                continue  # Skip schema/meta files
            try:
                self.load_workflow_file(yaml_file)
                count += 1
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"Skipping invalid workflow {yaml_file.name}: {e}"
                )
        return count

    def load_workflow_file(self, path: str | Path) -> WorkflowDef:
        """Load a single workflow definition from a YAML file."""
        path = Path(path)
        with open(path) as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict) or "id" not in raw or "steps" not in raw:
            raise EngineError(
                f"Invalid workflow file {path.name}: missing 'id' or 'steps'"
            )

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
                permitted_tools=step_raw.get("permitted_tools", []),
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

        # Write enforcement state for the first step
        self.write_enforcement_state(instance_id)

        # Persist to disk
        self._save_instance(instance_id)

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
            # Clear enforcement state on completion
            self.clear_enforcement_state(instance_id=instance_id)
            # Move persisted file to completed/
            self._save_instance(instance_id)
            self._delete_instance(instance_id)
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

        # Update enforcement state for the new step
        self.write_enforcement_state(instance_id)

        # Persist updated state to disk
        self._save_instance(instance_id)

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

    # ------------------------------------------------------------------
    # Enforcement State (hook integration)
    # ------------------------------------------------------------------

    @staticmethod
    def _enforcement_dir() -> Path | None:
        """Return the enforcement directory from env, or None if unset."""
        env_dir = os.environ.get("METIS_ENFORCEMENT_DIR")
        if env_dir:
            return Path(env_dir)
        return None

    def write_enforcement_state(
        self, instance_id: str, enforcement_dir: str | Path | None = None
    ) -> Path | None:
        """Write .metis-workflow-state.json for hook enforcement.

        Called after start_workflow() and advance() to update the state file
        whenever the current step changes.

        Args:
            instance_id: The workflow instance to write state for.
            enforcement_dir: Directory to write the state file to.
                If None, reads from METIS_ENFORCEMENT_DIR env var.
                If still None, does nothing (enforcement disabled).

        Returns:
            Path to the written state file, or None if enforcement is disabled.
        """
        if enforcement_dir is None:
            enforcement_dir = self._enforcement_dir()
        if enforcement_dir is None:
            return None

        enforcement_dir = Path(enforcement_dir)
        enforcement_dir.mkdir(parents=True, exist_ok=True)

        instance = self._instances.get(instance_id)
        if instance is None:
            return None

        workflow = self._workflows.get(instance.workflow_id)
        if workflow is None:
            return None

        current_step = workflow.get_step(instance.current_step_id)
        if current_step is None:
            return None

        state = {
            "instance_id": instance_id,
            "workflow_id": instance.workflow_id,
            "current_step_id": instance.current_step_id,
            "current_step_actor": current_step.actor,
            "permitted_tools": current_step.permitted_tools,
            "blocked_tools": [],
            "step_started_at": datetime.now(timezone.utc).isoformat(),
            "enforce": len(current_step.permitted_tools) > 0,
        }

        # Namespace by instance_id so concurrent workflows don't clobber each other
        state_file = enforcement_dir / f".metis-workflow-state-{instance_id}.json"
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

        return state_file

    def clear_enforcement_state(
        self, enforcement_dir: str | Path | None = None,
        instance_id: str | None = None,
    ) -> bool:
        """Remove enforcement state file when a workflow completes.

        Args:
            enforcement_dir: Directory containing the state file.
                If None, reads from METIS_ENFORCEMENT_DIR env var.
            instance_id: Instance to clear. If None, clears all (legacy compat).

        Returns:
            True if file(s) were removed, False otherwise.
        """
        if enforcement_dir is None:
            enforcement_dir = self._enforcement_dir()
        if enforcement_dir is None:
            return False

        removed = False
        enforcement_path = Path(enforcement_dir)
        if instance_id:
            state_file = enforcement_path / f".metis-workflow-state-{instance_id}.json"
            if state_file.exists():
                state_file.unlink()
                removed = True
        else:
            # Legacy: clean up old singleton file
            old_file = enforcement_path / ".metis-workflow-state.json"
            if old_file.exists():
                old_file.unlink()
                removed = True
            return True
        return False

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
