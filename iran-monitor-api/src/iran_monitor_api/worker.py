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

from . import db
from .config import get_settings
from .errors import ErrorCode
from .gather import run_premium_gather, GatherError
from .intel_base import read_sealed_hash
from .models import Status, Tier, utc_now
from .orchestrator import run_assess
from .signing import sign_audit_record

logger = logging.getLogger(__name__)


_shutdown = asyncio.Event()


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
