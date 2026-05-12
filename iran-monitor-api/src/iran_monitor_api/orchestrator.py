"""ASSESS pipeline orchestrator.

Steps per query:
1. Determine perspectives to invoke (from request, else DEFAULT_PERSPECTIVES).
2. Run Tetlock-forecaster FIRST to produce a cold-start prior.
3. Run the remaining perspectives sequentially with isolation (fresh process,
   sees scenario + intel base + Tetlock prior + its own framework — never another
   perspective's output).
4. Aggregate with weighted average (uniform weights Phase 1).
5. Flag divergence (max-min p_point >15pp).
6. Apply quorum rule (⌈2N/3⌉ required).
7. Assemble audit record + sign.

Returns (result_dict, audit_record_dict, signature_b64, status).
"""

from __future__ import annotations

import json
import logging
import statistics
from pathlib import Path
from typing import Any
from uuid import UUID

from . import db, signing
from .briefing_writer import parse_briefing_output, write_briefing
from .config import get_settings
from .errors import ErrorCode
from .gather import build_intel_base_summary
from .models import (
    AuditRecord,
    DEFAULT_PERSPECTIVES,
    PerspectiveOutput,
    QueryResult,
    Status,
    Tier,
    horizon_to_days,
    quorum_required,
    utc_now,
)
from .subagent import PerspectiveResult, SubagentError, invoke_perspective

logger = logging.getLogger(__name__)


DIVERGENCE_THRESHOLD_PP = 15.0  # design doc: weighted average flagged at >15pp


async def run_assess(
    *,
    query_id: UUID,
    scenario: str,
    horizon: str,
    tier: Tier,
    perspectives: list[str],
    intel_base_hash: str,
    query_delta_path: Path | None,
    query_delta_hash: str | None,
) -> tuple[dict, dict, str, Status]:
    """Run the ASSESS pipeline. Returns (result_dict, audit_dict, sig_b64, status)."""
    settings = get_settings()
    started_at = utc_now()
    horizon_days = horizon_to_days_str(horizon)

    output_dir = settings.query_outputs_dir / str(query_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    intel_summary = build_intel_base_summary(include_delta_path=query_delta_path)

    # Cold-start prior from Tetlock (always first, always part of the set)
    tetlock_name = "tetlock-forecaster"
    cold_start_prior: dict | None = None
    completed: list[PerspectiveResult] = []
    failed: list[str] = []

    # Make sure tetlock is at the head; preserve user-requested order otherwise.
    ordered = [tetlock_name] + [p for p in perspectives if p != tetlock_name]

    for name in ordered:
        try:
            res = await invoke_perspective(
                name=name,
                scenario=scenario,
                horizon_days=horizon_days,
                intel_base_summary=intel_summary,
                cold_start_prior=cold_start_prior,
                output_dir=output_dir,
            )
            completed.append(res)
            db.mark_perspective_completed(query_id, name)
            if name == tetlock_name:
                # Independence: pass ONLY the numerical prior to subsequent
                # perspectives. Including Tetlock's reasoning text caused
                # verbatim-phrase leakage in the spike (codex+gemini caught
                # it). Bayesian updating needs the prior probability, not
                # the predecessor's narrative.
                cold_start_prior = {
                    "p_point": res.p_point,
                    "p_interval": list(res.p_interval) if res.p_interval else None,
                }
        except SubagentError as e:
            logger.warning("perspective %s failed: %s", name, e)
            failed.append(name)
            db.mark_perspective_failed(query_id, name)

    # Quorum check
    needed = quorum_required(len(perspectives))
    if len(completed) < needed:
        # Failed: no result body
        audit = _build_audit_record(
            query_id=query_id,
            scenario=scenario,
            horizon_days=horizon_days,
            tier=tier,
            intel_base_hash=intel_base_hash,
            query_delta_hash=query_delta_hash,
            perspectives_invoked=perspectives,
            perspectives_completed=[r.name for r in completed],
            result_summary={"quorum_required": needed, "quorum_met": False},
            evidence_urls=_collect_evidence_urls(completed),
            started_at=started_at,
        )
        audit_dict = audit.model_dump(mode="json")
        sig = signing.sign_audit_record(audit_dict)
        return ({"failed_perspectives": failed}, audit_dict, sig, Status.FAILED)

    # Aggregate
    result = _aggregate(completed)
    status = Status.PARTIAL if failed else Status.COMPLETED

    # Briefing-writer pass: synthesise the per-perspective outputs into a
    # buyer-facing briefing. Value-add, not load-bearing — if it fails, the
    # query still returns with the raw aggregation. Run for Premium tier
    # always; for Standard tier the buyer chose the cheap path so we skip
    # this compute step.
    if tier == Tier.PREMIUM:
        try:
            briefing_dir = settings.query_outputs_dir / str(query_id)
            briefing_raw = await write_briefing(
                query_id=query_id,
                scenario=scenario,
                horizon_days=horizon_days,
                p_point=result.p_point,
                p_interval=result.p_interval,
                divergence_flag=result.divergence_flag,
                consensus_summary=result.consensus_summary,
                perspectives=[
                    {
                        "name": p.name,
                        "p_point": p.p_point,
                        "p_interval": list(p.p_interval) if p.p_interval else None,
                        "key_reasoning": p.key_reasoning,
                        "evidence_urls": p.evidence_urls,
                        "divergence_from_consensus_pp": p.divergence_from_consensus_pp,
                    }
                    for p in result.perspectives
                ],
                intel_base_hash=intel_base_hash,
                output_dir=briefing_dir,
            )
            disagreements, elasticity, briefing_md = parse_briefing_output(briefing_raw)
            result = result.model_copy(update={
                "major_disagreements": disagreements,
                "high_elasticity_events": elasticity,
                "briefing_markdown": briefing_md,
            })
        except SubagentError as e:
            logger.warning("briefing writer failed for %s: %s — returning raw aggregation", query_id, e)
            # result keeps its default empty briefing fields

    audit = _build_audit_record(
        query_id=query_id,
        scenario=scenario,
        horizon_days=horizon_days,
        tier=tier,
        intel_base_hash=intel_base_hash,
        query_delta_hash=query_delta_hash,
        perspectives_invoked=perspectives,
        perspectives_completed=[r.name for r in completed],
        result_summary={
            "p_point": result.p_point,
            "p_interval": list(result.p_interval),
            "divergence_flag": result.divergence_flag,
        },
        evidence_urls=_collect_evidence_urls(completed),
        started_at=started_at,
    )
    audit_dict = audit.model_dump(mode="json")
    sig = signing.sign_audit_record(audit_dict)
    result_dict = result.model_dump(mode="json")
    result_dict["failed_perspectives"] = failed
    return (result_dict, audit_dict, sig, status)


def horizon_to_days_str(horizon: str) -> int:
    return {"7d": 7, "14d": 14, "30d": 30, "60d": 60, "90d": 90}[horizon]


def _aggregate(completed: list[PerspectiveResult]) -> QueryResult:
    p_points = [r.p_point for r in completed]
    p_mean = statistics.fmean(p_points)
    p_lo = min(p_points)
    p_hi = max(p_points)
    divergence = (p_hi - p_lo) * 100.0  # in percentage points
    divergence_flag = divergence > DIVERGENCE_THRESHOLD_PP

    # consensus_summary: one-line synthesis derived deterministically
    consensus_summary = (
        f"Weighted-uniform average across {len(completed)} perspectives: "
        f"P = {p_mean:.3f} (range {p_lo:.3f}–{p_hi:.3f}, spread {divergence:.1f}pp). "
        f"{'Divergence flagged.' if divergence_flag else 'Within tolerance.'}"
    )

    perspectives = [
        PerspectiveOutput(
            name=r.name,
            p_point=r.p_point,
            p_interval=r.p_interval,
            key_reasoning=r.key_reasoning,
            evidence_urls=r.evidence_urls,
            divergence_from_consensus_pp=(r.p_point - p_mean) * 100.0,
        )
        for r in completed
    ]

    return QueryResult(
        p_point=p_mean,
        p_interval=(p_lo, p_hi),
        divergence_flag=divergence_flag,
        consensus_summary=consensus_summary,
        perspectives=perspectives,
    )


def _build_audit_record(
    *,
    query_id: UUID,
    scenario: str,
    horizon_days: int,
    tier: Tier,
    intel_base_hash: str,
    query_delta_hash: str | None,
    perspectives_invoked: list[str],
    perspectives_completed: list[str],
    result_summary: dict[str, Any],
    evidence_urls: list[str],
    started_at,
) -> AuditRecord:
    runtime = int((utc_now() - started_at).total_seconds())
    return AuditRecord(
        query_id=query_id,
        scenario_text=scenario,
        horizon_days=horizon_days,
        tier=tier,
        intelligence_base_hash=intel_base_hash,
        query_delta_hash=query_delta_hash,
        perspectives_invoked=perspectives_invoked,
        perspectives_completed=perspectives_completed,
        aggregation_method="weighted_uniform_average_v1",
        result_summary=result_summary,
        evidence_urls=evidence_urls,
        started_at_utc=started_at,
        runtime_seconds=runtime,
    )


def _collect_evidence_urls(results: list[PerspectiveResult]) -> list[str]:
    seen: list[str] = []
    seen_set: set[str] = set()
    for r in results:
        for u in r.evidence_urls:
            if u not in seen_set:
                seen.append(u)
                seen_set.add(u)
    return seen


def resolve_perspectives(requested: list[str] | None) -> list[str]:
    """Phase 1: frozen default if caller didn't override. Routing LLM is Phase 2."""
    if requested is None:
        return list(DEFAULT_PERSPECTIVES)
    return list(requested)
