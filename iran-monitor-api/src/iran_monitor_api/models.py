"""Pydantic models for request/response bodies and the signed audit record.

Schemas match the design doc Surface section. Wire format is JSON.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Tier(str, Enum):
    STANDARD = "standard"
    PREMIUM = "premium"


class Horizon(str, Enum):
    D7 = "7d"
    D14 = "14d"
    D30 = "30d"
    D60 = "60d"
    D90 = "90d"


class Status(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


# ── Canonical perspective set ─────────────────────────────────────────────────

ALL_PERSPECTIVES = [
    # Methodology
    "wack-strategic",
    "schelling-bargaining",
    "tetlock-forecaster",
    "taleb-tail-risk",
    "red-team-adversarial",
    "ach-process",
    "jervis-misperception",
    "posen-inadvertent",
    "kahn-escalation",
    "peripheral-scanner",
    # Domain
    "ostovar-irgc",
    "pollack-military",
    "gause-regional",
    "solingen-proliferation",
    "narang-nuclear",
]

# Frozen Phase 1 default: drop the two nuclear-only domain agents.
# Routing layer LLM can re-add them if scenario keywords trigger.
DEFAULT_PERSPECTIVES = [
    p for p in ALL_PERSPECTIVES if p not in {"solingen-proliferation", "narang-nuclear"}
]


# ── Request ───────────────────────────────────────────────────────────────────


class CreateQueryRequest(BaseModel):
    scenario: str = Field(min_length=10, max_length=1500)
    horizon: Horizon
    tier: Tier
    perspectives: list[str] | None = None
    deliver_to: str | None = Field(
        default=None,
        description=(
            "Optional email address for delivery of the completed briefing. "
            "If set, we send an HTML email with JSON + signed audit attached "
            "when the query completes. Polling still works in parallel."
        ),
    )

    @field_validator("deliver_to")
    @classmethod
    def validate_deliver_to(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        # Cheap email-shape check; SMTP layer will reject malformed addresses anyway.
        if "@" not in v or len(v) < 5 or len(v) > 254:
            raise ValueError("deliver_to must look like an email address")
        return v

    @field_validator("scenario")
    @classmethod
    def strip_control_chars(cls, v: str) -> str:
        # Drop control chars; explicit markdown/HTML stripping happens before
        # the agent prompt is built. Phase 1 prompt-injection defense.
        return "".join(c for c in v if c.isprintable() or c in {"\n", "\t"})

    @field_validator("perspectives")
    @classmethod
    def validate_perspectives(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        unknown = [p for p in v if p not in ALL_PERSPECTIVES]
        if unknown:
            raise ValueError(f"unknown perspectives: {unknown}")
        if len(v) < 3:
            raise ValueError("must request at least 3 perspectives")
        return v


# ── POST /v1/queries → 202 ────────────────────────────────────────────────────


class CreateQueryResponse(BaseModel):
    query_id: UUID
    status: Literal[Status.QUEUED]
    tier: Tier
    submitted_at_utc: datetime
    estimated_completion_utc: datetime


# ── GET /v1/queries/{id} ──────────────────────────────────────────────────────


class QueryInProgressResponse(BaseModel):
    query_id: UUID
    status: Literal[Status.QUEUED, Status.RUNNING]
    perspectives_total: int
    perspectives_completed: int
    elapsed_seconds: int


class PerspectiveOutput(BaseModel):
    name: str
    p_point: float = Field(ge=0.0, le=1.0)
    p_interval: tuple[float, float] | None = None
    key_reasoning: str
    evidence_urls: list[str] = []
    divergence_from_consensus_pp: float | None = None


class MajorDisagreement(BaseModel):
    """A cluster of perspectives that diverge from another cluster on a specific
    sub-question. Surfaced for the buyer because the *substance* of disagreement
    is often more actionable than the consensus number."""

    topic: str  # e.g. "Likelihood of German government public attribution"
    spread_pp: float  # max - min across the involved perspectives
    high_side: list[str]  # perspective names taking the higher-P position
    low_side: list[str]  # perspective names taking the lower-P position
    narrative: str  # 1–3 sentences naming the substantive split


class HighElasticityEvent(BaseModel):
    """An event that, if it materialised, would shift the assessed probability
    materially (>5pp). The buyer monitors for these signals to know when to
    re-query. Parallels the iran-monitor cron's "event elasticity tiers"
    methodology."""

    event: str  # the named event (concrete, observable)
    shift_direction: Literal["up", "down"]
    magnitude_pp: str  # e.g. "+8 to +12" — LLM-generated range, string to preserve
    monitor: str  # what the buyer should watch to detect this event


class QueryResult(BaseModel):
    p_point: float = Field(ge=0.0, le=1.0)
    p_interval: tuple[float, float]
    divergence_flag: bool
    consensus_summary: str
    perspectives: list[PerspectiveOutput]
    # Phase 1.5 additions — populated by the briefing-writer subagent after
    # aggregation. Empty lists / empty string are valid (Standard tier may
    # not run the briefing writer to save compute).
    major_disagreements: list[MajorDisagreement] = []
    high_elasticity_events: list[HighElasticityEvent] = []
    briefing_markdown: str = ""


class AuditRecord(BaseModel):
    """Signed envelope. Canonicalized JSON is what gets Ed25519-signed."""

    model_config = ConfigDict(extra="forbid")

    query_id: UUID
    scenario_text: str
    horizon_days: int
    tier: Tier
    intelligence_base_hash: str
    query_delta_hash: str | None
    perspectives_invoked: list[str]
    perspectives_completed: list[str]
    aggregation_method: str
    result_summary: dict  # {p_point, p_interval, divergence_flag}
    evidence_urls: list[str]
    started_at_utc: datetime
    runtime_seconds: int
    version: str = "1.0"


class QueryCompletedResponse(BaseModel):
    query_id: UUID
    status: Literal[Status.COMPLETED, Status.PARTIAL]
    partial: bool = False
    failed_perspectives: list[str] = []
    result: QueryResult
    audit_record: AuditRecord
    audit_signature: str  # base64 Ed25519


class QueryFailedResponse(BaseModel):
    query_id: UUID
    status: Literal[Status.FAILED]
    audit_record: AuditRecord
    audit_signature: str
    failed_perspectives: list[str]


# ── Helpers ───────────────────────────────────────────────────────────────────


def new_query_id() -> UUID:
    return uuid4()


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def horizon_to_days(h: Horizon) -> int:
    return {Horizon.D7: 7, Horizon.D14: 14, Horizon.D30: 30, Horizon.D60: 60, Horizon.D90: 90}[h]


def quorum_required(n_perspectives: int) -> int:
    """⌈2N/3⌉ — design doc quorum rule."""
    return -(-2 * n_perspectives // 3)
