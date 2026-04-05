"""Pydantic models for the METIS capability registry."""

from pydantic import BaseModel


class CapabilityEntry(BaseModel):
    """A single capability (skill, agent, or workflow) in the registry."""

    id: str
    category: str  # "skill" | "agent" | "workflow"
    name: str
    description: str
    tags: list[str] = []
    inputs: list[str] = []
    outputs: list[str] = []
    tools: list[str] = []
    model: str | None = None
    source: str  # relative path to the actual definition file
    confidence: str = "medium"  # "high" | "medium" | "low"
    human_required: bool = False


class StaffingMatch(BaseModel):
    """A single capability matched to a requirement."""

    capability_id: str
    capability_name: str
    match_reason: str


class StaffingPlan(BaseModel):
    """Result of the staffing recommender: matched capabilities and gaps."""

    matched: list[StaffingMatch] = []
    gaps: list[str] = []  # requirements with no matching capability
