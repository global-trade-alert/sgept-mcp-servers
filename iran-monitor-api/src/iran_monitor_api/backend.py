"""IranMonitorBackend — implements a2a_protocol.AgentBackend.

This is the bridge between the generic A2A protocol surface (provided by the
sibling `a2a_protocol` package) and the Iran-monitor business logic (existing
orchestrator + worker + DB + signing). The backend does:

1. Translate A2A Messages → CreateQueryRequest (scenario + horizon + tier)
2. Translate QueryResult → A2A Task + Artifact + signed audit
3. Wire the existing auth + rate-limit + email layers
4. Drive the multi-turn clarifier loop, transitioning to input-required when
   the scenario is underspecified

Existing REST endpoints (POST /v1/queries + GET /v1/queries/{id}) remain
available for back-compat. The A2A surface lives alongside.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import AsyncIterator
from uuid import UUID

from a2a_protocol import (
    AgentBackend,
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
    AgentAuthentication,
    Artifact,
    AuthContext,
    DataPart,
    Message,
    MessageRole,
    Task,
    TaskContext,
    TaskHandle,
    TaskID,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    TextPart,
)
from a2a_protocol.event_bus import EventBus

from . import __version__, db, signing
from .api import auth as iran_auth
from .api import rate_limit
from .config import get_settings
from .errors import APIError, ErrorCode
from .models import (
    DEFAULT_PERSPECTIVES,
    Horizon,
    Status,
    Tier,
    horizon_to_days,
    new_query_id,
    utc_now,
)

logger = logging.getLogger(__name__)


# ── Status ↔ TaskState mapping ────────────────────────────────────────────────


_STATUS_TO_TASKSTATE: dict[str, TaskState] = {
    Status.QUEUED.value: TaskState.SUBMITTED,
    Status.RUNNING.value: TaskState.WORKING,
    Status.COMPLETED.value: TaskState.COMPLETED,
    Status.PARTIAL.value: TaskState.COMPLETED,   # PARTIAL still "completed" for A2A; partial flag flows via metadata
    Status.FAILED.value: TaskState.FAILED,
}


def _status_to_a2a(s: str) -> TaskState:
    return _STATUS_TO_TASKSTATE.get(s, TaskState.WORKING)


# ── Agent card factory ────────────────────────────────────────────────────────


def _build_agent_card() -> AgentCard:
    return AgentCard(
        name="iran-monitor",
        description=(
            "Queryable inference over the Iran Conflict Scenario Monitor's "
            "perspective stack. Submit a novel geopolitical scenario about Iran "
            "or its proxies; the agent runs 14 independent perspective agents "
            "(Tetlock superforecasting, Schelling bargaining, Wack predetermined-"
            "elements, plus 11 others) against a verified intelligence base updated "
            "every 6 hours, and returns a probability with reasoning trace, "
            "structured major-disagreements, high-elasticity events, a human-"
            "readable briefing, and an Ed25519-signed audit record."
        ),
        url="https://a2a.globaltradealert.org",
        provider=AgentProvider(
            organization="SGEPT / Global Trade Alert",
            url="https://a2a.globaltradealert.org",
        ),
        version=__version__,
        protocol_version="1.0",
        documentation_url="https://a2a.globaltradealert.org",
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            state_transition_history=True,
            streaming_granularity="event",
        ),
        authentication=AgentAuthentication(
            schemes=["bearer"],
            credentials={
                "bearerFormat": "imk-<token>",
                "issuanceContact": "johannes.fritz@sgept.org",
            },
        ),
        default_input_modes=["application/json", "text/plain"],
        default_output_modes=["application/json", "text/markdown"],
        skills=[
            AgentSkill(
                id="assess_scenario",
                name="Assess novel scenario",
                description=(
                    "Submit a novel geopolitical scenario about Iran or its proxies. "
                    "Returns a probability point estimate + uncertainty interval, "
                    "per-framework reasoning across 14 perspectives, structured "
                    "major-disagreements, high-elasticity events with monitor signals, "
                    "a 500-1500 word human-readable briefing, and a signed audit "
                    "record bound to the intelligence base used."
                ),
                tags=["geopolitics", "forecasting", "iran", "risk"],
                examples=[
                    "Iran launches a meaningfully disruptive cyber attack on German critical infrastructure within 30 days, with German government public attribution.",
                    "Iran and China sign a formal bilateral agreement enabling oil-for-yuan settlement (not crude swap, not informal credit) with at least one explicit volume commitment, within 30 days, publicly announced by both parties.",
                    "Houthi forces conduct a multi-vessel attack on commercial shipping in the Red Sea within 30 days that causes ≥3 vessel casualties, prompting at least one Western navy to declare an Article 5-equivalent response posture.",
                ],
                input_modes=["application/json", "text/plain"],
                output_modes=["application/json", "text/markdown"],
            ),
        ],
    )


# ── The backend ───────────────────────────────────────────────────────────────


class IranMonitorBackend:
    """Implements `a2a_protocol.AgentBackend` against the existing orchestrator
    + worker + DB. The protocol layer handles HTTP/JSON-RPC/SSE; this class
    handles "what does Iran-monitor actually do."""

    def __init__(self, event_bus: EventBus | None = None):
        self._card = _build_agent_card()
        self._event_bus = event_bus or EventBus()

    @property
    def agent_card(self) -> AgentCard:
        return self._card

    @property
    def event_bus(self) -> EventBus:
        """Exposed so the worker can publish into the same bus the SSE
        endpoint subscribes against."""
        return self._event_bus

    # ── Auth ─────────────────────────────────────────────────────────────────

    def authenticate(self, token: str) -> AuthContext | None:
        keys = iran_auth._api_keys()
        org_id = keys.get(token)
        if org_id is None:
            return None
        return AuthContext(
            principal=org_id,
            scopes=frozenset({"assess_scenario"}),
            raw_token=token,
        )

    # ── Lifecycle ────────────────────────────────────────────────────────────

    async def submit_task(
        self, message: Message, task_id: TaskID, context: TaskContext,
    ) -> TaskHandle:
        """A new task. Translate the Message into our internal CreateQueryRequest
        + enqueue. Worker picks it up asynchronously."""
        scenario, horizon, tier, deliver_to, perspectives = self._extract_inputs(message)

        # Rate-limit by the auth principal (org_id).
        try:
            rate_limit.check_and_record(context.auth.principal, Tier(tier))
        except APIError as e:
            from a2a_protocol import A2AError, JSONRPCErrorCode
            raise A2AError(JSONRPCErrorCode.RATE_LIMITED, e.message) from e

        qid = UUID(task_id) if _looks_like_uuid(task_id) else new_query_id()
        db.enqueue_query(
            query_id=qid,
            org_id=context.auth.principal,
            api_key=context.auth.raw_token,
            scenario=scenario,
            horizon=horizon,
            tier=Tier(tier),
            perspectives_invoked=perspectives,
            deliver_to=deliver_to,
        )

        # Persist the initial message to the task history so continue_task can
        # see it. Reuses the queries table — the scenario field already holds
        # the canonical text; the message itself is reconstructable.
        # (A formal task_messages table would let us be richer; Phase 1.5
        # keeps it lean — the scenario column IS the first message.)

        task = self._build_task(str(qid), context.context_id, history=[message])
        return TaskHandle(task=task)

    async def continue_task(
        self, task_id: TaskID, message: Message, history: list[Message],
    ) -> TaskHandle:
        """Resume an input-required task. Append the new Message to history;
        worker re-runs the clarifier on the augmented context."""
        row = db.get_query(_qid(task_id))
        if row is None:
            from a2a_protocol import A2AError, JSONRPCErrorCode
            raise A2AError(JSONRPCErrorCode.TASK_NOT_FOUND, f"task {task_id} not found")

        # Append to the scenario column — the orchestrator's clarifier will
        # see the augmented text on the next worker iteration.
        new_text = message.text() or ""
        augmented = (row["scenario"] or "") + "\n\n[CALLER CLARIFICATION]: " + new_text
        db.update_scenario_after_clarification(_qid(task_id), augmented)
        db.reset_running_to_queued(_qid(task_id))   # worker will pick it up again

        task = self._build_task(task_id, row["org_id"], history=history + [message])
        return TaskHandle(task=task)

    async def cancel_task(self, task_id: TaskID) -> Task:
        row = db.get_query(_qid(task_id))
        if row is None:
            from a2a_protocol import A2AError, JSONRPCErrorCode
            raise A2AError(JSONRPCErrorCode.TASK_NOT_FOUND, f"task {task_id} not found")
        db.cancel_query(_qid(task_id))
        await self._event_bus.close(task_id)
        row = db.get_query(_qid(task_id))
        return self._build_task(task_id, row["org_id"], history=[])

    async def get_task(self, task_id: TaskID) -> Task | None:
        row = db.get_query(_qid(task_id))
        if row is None:
            return None
        # Build an A2A Task object from the row state
        return self._build_task(task_id, row["org_id"], history=[], db_row=row)

    async def stream_events(self, task_id: TaskID):
        """Subscribe to the per-task event bus."""
        async for ev in self._event_bus.subscribe(task_id):
            yield ev

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _extract_inputs(self, message: Message) -> tuple[str, str, str, str | None, list[str]]:
        """Pull (scenario, horizon, tier, deliver_to, perspectives) from an
        A2A Message. The message can be either:

        a) data-part with `{scenario, horizon, tier, deliver_to?, perspectives?}` — preferred
        b) text-part with the scenario text — we default horizon/tier and rely on the clarifier
        """
        d = message.data()
        scenario = (d.get("scenario") or message.text() or "").strip()
        horizon = d.get("horizon", "30d")
        tier = d.get("tier", "standard")
        deliver_to = d.get("deliver_to")
        perspectives = d.get("perspectives") or list(DEFAULT_PERSPECTIVES)

        if not scenario:
            from a2a_protocol import A2AError, JSONRPCErrorCode
            raise A2AError(
                JSONRPCErrorCode.INVALID_PARAMS,
                "message must contain either a scenario data-part or a non-empty text-part",
            )

        # Cheap validation
        if horizon not in {h.value for h in Horizon}:
            from a2a_protocol import A2AError, JSONRPCErrorCode
            raise A2AError(JSONRPCErrorCode.INVALID_PARAMS, f"unknown horizon {horizon!r}")
        if tier not in {t.value for t in Tier}:
            from a2a_protocol import A2AError, JSONRPCErrorCode
            raise A2AError(JSONRPCErrorCode.INVALID_PARAMS, f"unknown tier {tier!r}")

        return scenario, horizon, tier, deliver_to, perspectives

    def _build_task(
        self,
        task_id: TaskID,
        context_id: str,
        *,
        history: list[Message],
        db_row: dict | None = None,
    ) -> Task:
        row = db_row or db.get_query(_qid(task_id))
        if row is None:
            # Construct a synthetic submitted-state task for newly-enqueued items
            return Task(
                id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.SUBMITTED),
                history=history,
            )

        state = _status_to_a2a(row["status"])
        artifacts: list[Artifact] = []
        if row.get("result_json"):
            try:
                result = json.loads(row["result_json"])
                # Briefing as a markdown artifact (Premium); JSON result as a data artifact.
                if result.get("briefing_markdown"):
                    artifacts.append(Artifact(
                        name="briefing",
                        description="Human-readable scenario assessment briefing.",
                        parts=[TextPart(text=result["briefing_markdown"])],
                    ))
                artifacts.append(Artifact(
                    name="assessment",
                    description="Structured assessment payload.",
                    parts=[DataPart(data=result)],
                ))
                if row.get("audit_record_json") and row.get("audit_signature"):
                    artifacts.append(Artifact(
                        name="audit",
                        description="Ed25519-signed audit record.",
                        parts=[DataPart(data={
                            "audit_record": json.loads(row["audit_record_json"]),
                            "audit_signature": row["audit_signature"],
                        })],
                    ))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("could not deserialize result for task %s: %s", task_id, e)

        return Task(
            id=task_id,
            context_id=context_id,
            status=TaskStatus(state=state),
            artifacts=artifacts,
            history=history,
            metadata={
                "tier": row["tier"],
                "horizon": row["horizon"],
                "intelligence_base_hash": row.get("intel_base_hash"),
                "perspectives_invoked": json.loads(row["perspectives_invoked"]) if row.get("perspectives_invoked") else [],
                "perspectives_completed": json.loads(row["perspectives_completed"] or "[]"),
                "failed_perspectives": json.loads(row["failed_perspectives"] or "[]"),
            },
        )


# ── Helpers ──────────────────────────────────────────────────────────────────


def _qid(task_id: TaskID) -> UUID:
    return UUID(task_id) if not isinstance(task_id, UUID) else task_id


def _looks_like_uuid(s: str) -> bool:
    try:
        UUID(s)
        return True
    except ValueError:
        return False
