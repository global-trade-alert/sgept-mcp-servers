"""Pydantic models for METIS workflow engine."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================


class WorkflowStatus(str, Enum):
    """Overall workflow instance status."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class StepStatus(str, Enum):
    """Individual step status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Workflow Definition Models (parsed from YAML)
# ============================================================================


class StepInput(BaseModel):
    """An input parameter for a workflow step."""
    name: str
    required: bool = True


class StepOutput(BaseModel):
    """An output parameter for a workflow step."""
    name: str
    required: bool = True


class GateSchema(BaseModel):
    """Schema-based quality gate definition."""
    required: list[str] = Field(default_factory=list)


class Gate(BaseModel):
    """Quality gate for a workflow step."""
    type: str = "schema"
    schema_def: GateSchema = Field(default_factory=GateSchema, alias="schema")

    model_config = {"populate_by_name": True}


class StepDef(BaseModel):
    """Definition of a single workflow step."""
    id: str
    name: str
    actor: str = "human"
    inputs: list[StepInput] = Field(default_factory=list)
    outputs: list[StepOutput] = Field(default_factory=list)
    gate: Optional[Gate] = None
    next: list[str] = Field(default_factory=list)
    permitted_tools: list[str] = Field(default_factory=list)


class WorkflowDef(BaseModel):
    """Definition of a complete workflow (parsed from YAML)."""
    id: str
    name: str
    version: int = 1
    steps: list[StepDef]

    def get_step(self, step_id: str) -> StepDef | None:
        """Get a step definition by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    @property
    def first_step_id(self) -> str:
        """Return the ID of the first step."""
        return self.steps[0].id


# ============================================================================
# Workflow Instance Models (runtime state)
# ============================================================================


class StepState(BaseModel):
    """Runtime state of a single step within a workflow instance."""
    status: StepStatus = StepStatus.PENDING
    output: dict[str, Any] = Field(default_factory=dict)


class WorkflowInstance(BaseModel):
    """Runtime state of a workflow instance."""
    instance_id: str
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.RUNNING
    current_step_id: str
    step_states: dict[str, StepState] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str = ""
