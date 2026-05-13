"""Async worker loop. Single concurrency for Phase 1.

Lifecycle per query:
  claim_next_query → (Premium: run_premium_gather) → run_assess → complete_query
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
from uuid import UUID

from a2a_protocol import (
    Artifact,
    DataPart,
    Message,
    MessageRole,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)

from . import db
from .config import get_settings
from .email_delivery import EmailDeliveryError, send_completion_email
from .errors import ErrorCode
from .gather import run_premium_gather, GatherError
from .intel_base import read_sealed_hash
from .models import Status, Tier, utc_now
from .orchestrator import run_assess
from .scenario_clarifier import ClarifierVerdict, run_clarifier
from .signing import sign_audit_record
from .subagent import SubagentError

logger = logging.getLogger(__name__)


_shutdown = asyncio.Event()


def _minimal_audit(
    qid: UUID, scenario: str, tier: Tier, intel_hash: str,
    perspectives: list[str], started, runtime: int, error: str,
) -> dict:
    """Build a minimal audit record for failure/reject paths so we always have
    a signed envelope even on the error branch."""
    return {
        "query_id": str(qid),
        "scenario_text": scenario,
        "horizon_days": -1,
        "tier": tier.value,
        "intelligence_base_hash": intel_hash,
        "query_delta_hash": None,
        "perspectives_invoked": perspectives,
        "perspectives_completed": [],
        "aggregation_method": "n/a",
        "result_summary": {"error": error[:500]},
        "evidence_urls": [],
        "started_at_utc": started.isoformat(),
        "runtime_seconds": runtime,
        "version": "1.0",
    }


def _install_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    def _handle(signum):
        logger.info("worker received signal %s — initiating shutdown", signum)
        _shutdown.set()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _handle, sig)
        except NotImplementedError:
            # Windows / restricted envs
            pass


async def _recover_running() -> None:
    """On worker startup, any RUNNING queries are aborted and re-queued.

    Phase 1 worker isn't tolerant of mid-flight resume; re-queue is the safe call.
    """
    rows = db.find_running_queries()
    for row in rows:
        qid = UUID(row["query_id"])
        logger.warning("crash recovery: re-queuing %s", qid)
        db.reset_running_to_queued(qid)


async def _publish(qid: UUID, event) -> None:
    """Publish an SSE event to the per-task event bus. Best-effort — if the
    backend isn't initialized (e.g. worker-only deployment), this is a no-op."""
    try:
        from .main import get_backend
        backend = get_backend()
        await backend.event_bus.publish(str(qid), event)
    except Exception as e:
        logger.debug("event publish skipped for %s: %s", qid, e)


async def _publish_status(
    qid: UUID, state: TaskState, *, final: bool = False, message_text: str | None = None,
) -> None:
    status = TaskStatus(
        state=state,
        message=(
            Message(role=MessageRole.AGENT, parts=[TextPart(text=message_text)])
            if message_text else None
        ),
    )
    await _publish(qid, TaskStatusUpdateEvent(
        task_id=str(qid), context_id=str(qid), status=status, final=final,
    ))


def _is_rest_submission(row: dict) -> bool:
    """The REST surface always supplies tier + horizon + a fleshed-out scenario
    in the original POST. A2A submissions may supply a thin scenario and rely
    on the clarifier. We detect REST by checking the scenario doesn't carry
    a CALLER CLARIFICATION marker AND the scenario is ≥ 60 chars (REST
    contract enforces min_length=10 but most production scenarios are >60)."""
    s = row.get("scenario", "")
    return "[CALLER CLARIFICATION]" not in s and len(s) >= 60


async def _process_one(row: dict) -> None:
    settings = get_settings()
    qid = UUID(row["query_id"])
    scenario = row["scenario"]
    horizon = row["horizon"]
    tier = Tier(row["tier"])
    perspectives = json.loads(row["perspectives_invoked"])

    started = utc_now()
    intel_hash = read_sealed_hash() or "sha256:UNSEALED"
    query_delta_path = None
    query_delta_hash = None

    await _publish_status(qid, TaskState.WORKING)

    # ── Layer 5: scenario clarifier (A2A path only) ──────────────────────────
    # REST submissions skip the clarifier (REST clients can't respond to
    # mid-task questions). A2A submissions go through the clarifier; if it
    # decides the scenario is underspecified, the worker transitions to
    # INPUT_REQUIRED and pauses.
    if not _is_rest_submission(row):
        try:
            history = [Message(role=MessageRole.USER, parts=[TextPart(text=scenario)])]
            verdict: ClarifierVerdict = await run_clarifier(history)
            if not verdict.ready:
                # Cap round-trips at 3 — beyond that, reject.
                roundtrips = scenario.count("[CALLER CLARIFICATION]")
                if roundtrips >= 3:
                    logger.info("query %s hit 3-round-trip cap; rejecting", qid)
                    await _publish_status(
                        qid, TaskState.REJECTED, final=True,
                        message_text="Maximum 3 clarification round-trips reached without resolving missing fields.",
                    )
                    audit = _minimal_audit(qid, scenario, tier, intel_hash, perspectives,
                                           started, runtime=int((utc_now() - started).total_seconds()),
                                           error=f"rejected after {roundtrips} clarifications")
                    sig = sign_audit_record(audit)
                    db.complete_query(
                        query_id=qid, status=Status.FAILED,
                        intel_base_hash=intel_hash, query_delta_hash=None,
                        result_json=None, audit_record_json=json.dumps(audit),
                        audit_signature=sig,
                        runtime_seconds=int((utc_now() - started).total_seconds()),
                        error_code=ErrorCode.MALFORMED_INPUT.value,
                    )
                    return
                logger.info("query %s needs clarification: %s", qid, verdict.missing)
                await _publish_status(
                    qid, TaskState.INPUT_REQUIRED,
                    message_text=verdict.question or "Please clarify the scenario.",
                )
                # Worker leaves the row in RUNNING state (so claim_next won't
                # re-pick it). The backend's continue_task call resets it to
                # QUEUED when the caller responds, at which point we re-enter
                # this loop with the augmented scenario.
                # Actually: we DO want claim_next not to re-pick it, AND we
                # want the next continue_task to wake the worker. The current
                # design relies on continue_task → reset_running_to_queued,
                # after which claim_next picks it up. So leave RUNNING.
                return
            # Use the augmented scenario from the clarifier going forward.
            scenario = verdict.augmented_scenario or scenario
            if verdict.horizon_days:
                horizon = f"{verdict.horizon_days}d"
        except SubagentError as e:
            logger.warning("clarifier failed for %s: %s — proceeding with original scenario", qid, e)

    try:
        if tier == Tier.PREMIUM:
            try:
                delta_path, delta_hash, gather_summary = await run_premium_gather(
                    query_id=qid, scenario=scenario
                )
                query_delta_path = delta_path
                query_delta_hash = delta_hash
                logger.info("GATHER for %s: %s", qid, gather_summary)
            except GatherError as e:
                logger.error("GATHER failed for %s: %s", qid, e)
                # Fall through with no delta — ASSESS still runs

        result, audit_dict, sig, status = await run_assess(
            query_id=qid,
            scenario=scenario,
            horizon=horizon,
            tier=tier,
            perspectives=perspectives,
            intel_base_hash=intel_hash,
            query_delta_path=query_delta_path,
            query_delta_hash=query_delta_hash,
        )
        runtime = int((utc_now() - started).total_seconds())
        db.complete_query(
            query_id=qid,
            status=status,
            intel_base_hash=intel_hash,
            query_delta_hash=query_delta_hash,
            result_json=json.dumps(result) if status != Status.FAILED else None,
            audit_record_json=json.dumps(audit_dict),
            audit_signature=sig,
            runtime_seconds=runtime,
            error_code=ErrorCode.QUORUM_FAILED.value if status == Status.FAILED else None,
        )
        logger.info("completed %s status=%s runtime=%ds", qid, status.value, runtime)

        # Publish artifact + final status to A2A streams.
        if isinstance(result, dict):
            # The briefing as a markdown artifact (Premium only — Standard
            # leaves briefing_markdown empty).
            briefing_md = result.get("briefing_markdown") or ""
            if briefing_md:
                await _publish(qid, TaskArtifactUpdateEvent(
                    task_id=str(qid), context_id=str(qid),
                    artifact=Artifact(
                        name="briefing",
                        description="Human-readable scenario assessment briefing.",
                        parts=[TextPart(text=briefing_md)],
                    ),
                ))
            # The structured assessment as a data artifact.
            await _publish(qid, TaskArtifactUpdateEvent(
                task_id=str(qid), context_id=str(qid),
                artifact=Artifact(
                    name="assessment",
                    description="Structured assessment + signed audit record.",
                    parts=[DataPart(data={
                        "result": result,
                        "audit_record": audit_dict,
                        "audit_signature": sig,
                    })],
                ),
            ))
        a2a_final_state = (
            TaskState.COMPLETED if status != Status.FAILED else TaskState.FAILED
        )
        await _publish_status(qid, a2a_final_state, final=True)
        from .main import get_backend
        try:
            await get_backend().event_bus.close(str(qid))
        except Exception:
            pass

        # Optional email delivery. Best-effort: a delivery failure does NOT
        # fail the query — the buyer can still poll. We just record the
        # delivery status so ops can spot patterns.
        deliver_to = row.get("deliver_to")
        if deliver_to and status != Status.FAILED:
            try:
                send_completion_email(
                    deliver_to=deliver_to,
                    scenario=scenario,
                    query_id=qid,
                    intelligence_base_hash=intel_hash,
                    briefing_markdown=(result.get("briefing_markdown") or "" if isinstance(result, dict) else ""),
                    full_result_json={
                        "query_id": str(qid),
                        "status": status.value,
                        "result": result,
                        "audit_record": audit_dict,
                        "audit_signature": sig,
                    },
                )
                db.update_delivery_status(qid, "delivered")
            except EmailDeliveryError as e:
                logger.warning("email delivery to %s failed for %s: %s", deliver_to, qid, e)
                db.update_delivery_status(qid, f"failed: {str(e)[:120]}")
    except Exception as e:
        logger.exception("worker crash on query %s: %s", qid, e)
        runtime = int((utc_now() - started).total_seconds())
        # Build a minimal audit + sign even on crash
        minimal_audit = {
            "query_id": str(qid),
            "scenario_text": scenario,
            "horizon_days": -1,
            "tier": tier.value,
            "intelligence_base_hash": intel_hash,
            "query_delta_hash": query_delta_hash,
            "perspectives_invoked": perspectives,
            "perspectives_completed": [],
            "aggregation_method": "n/a",
            "result_summary": {"error": str(e)[:500]},
            "evidence_urls": [],
            "started_at_utc": started.isoformat(),
            "runtime_seconds": runtime,
            "version": "1.0",
        }
        try:
            sig = sign_audit_record(minimal_audit)
        except Exception:
            sig = ""
        db.complete_query(
            query_id=qid,
            status=Status.FAILED,
            intel_base_hash=intel_hash,
            query_delta_hash=query_delta_hash,
            result_json=None,
            audit_record_json=json.dumps(minimal_audit),
            audit_signature=sig,
            runtime_seconds=runtime,
            error_code=ErrorCode.WORKER_DOWN.value,
        )


async def _loop() -> None:
    db.init_db()
    await _recover_running()
    logger.info("worker started")
    while not _shutdown.is_set():
        row = db.claim_next_query()
        if row is None:
            try:
                await asyncio.wait_for(_shutdown.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pass
            continue
        await _process_one(row)
    logger.info("worker stopped")


def run() -> None:
    logging.basicConfig(
        level=os.environ.get("IRAN_API_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _install_signal_handlers(loop)
    try:
        loop.run_until_complete(_loop())
    finally:
        loop.close()
