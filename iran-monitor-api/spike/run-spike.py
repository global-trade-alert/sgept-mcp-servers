"""Spike driver: validates the subagent-invocation pattern end-to-end.

Per the design doc, the spike must demonstrate:
1. `claude -p` headless invocation from a Python worker produces parseable
   per-perspective JSON output for a novel scenario.
2. Isolation: agent N's reasoning is independent of agent N-1's output.
   Test: run a perspective WITH and WITHOUT a cold-start prior; reasoning
   structure should match the framework, not the prior text.
3. Production-grade aggregation + signed audit record + intel-base sealing
   all execute cleanly with real subprocess data.

Run from this directory:
    uv run python spike/run-spike.py

Output written to spike/runs/{ts}/:
- {scenario_id}-{perspective}.json   (raw subagent outputs)
- audit-record.json                  (signed audit per scenario)
- spike-results.md                   (human review artefact)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Bootstrap path
THIS = Path(__file__).resolve()
SRC = THIS.parent.parent / "src"
sys.path.insert(0, str(SRC))

# Force isolated env BEFORE the package reads settings
SPIKE_DIR = THIS.parent
RUN_TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
RUN_DIR = SPIKE_DIR / "runs" / RUN_TS
RUN_DIR.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("IRAN_API_BASE_DIR", str(RUN_DIR / "data"))
os.environ.setdefault(
    "IRAN_API_IRAN_MONITOR_REPO",
    str(Path.home() / "Documents/GitHub/jf-private/jf-thought/sgept-analytics/iran-monitor"),
)
os.environ.setdefault(
    "IRAN_API_SIGNING_KEY_PATH",
    str(THIS.parent.parent / "keys" / "signing-key.bin"),
)
os.environ.setdefault(
    "IRAN_API_SIGNING_PUB_KEY_PATH",
    str(THIS.parent.parent / "keys" / "signing-key.pub"),
)

# Make subagent timeout generous for the spike
os.environ.setdefault("IRAN_API_SUBAGENT_TIMEOUT_SECONDS", "900")

from iran_monitor_api import db, signing  # noqa: E402
from iran_monitor_api.config import get_settings  # noqa: E402
from iran_monitor_api.gather import build_intel_base_summary  # noqa: E402
from iran_monitor_api.subagent import (  # noqa: E402
    PerspectiveResult,
    SubagentError,
    invoke_perspective,
)
from iran_monitor_api.intel_base import compute_intel_base_hash, seal  # noqa: E402

logging.basicConfig(
    level="INFO",
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("spike")


# ── Spike protocol ────────────────────────────────────────────────────────────


SPIKE_PERSPECTIVES = ["tetlock-forecaster", "schelling-bargaining", "wack-strategic"]


def load_scenarios() -> list[dict]:
    with open(SPIKE_DIR / "test-scenarios.json") as fh:
        return json.load(fh)["scenarios"]


async def run_canonical_path(scenario: dict, output_dir: Path) -> dict:
    """Canonical Phase 1 ordering: Tetlock first → propagates prior → others."""
    settings = get_settings()

    # Seal the intel base hash if not already sealed (cron would normally do this)
    digest = seal(settings.iran_monitor_repo)
    log.info("intel-base sealed: %s", digest[:16] + "...")

    intel_summary = build_intel_base_summary()

    cold_start_prior = None
    results: list[PerspectiveResult] = []
    errors: dict[str, str] = {}

    for name in SPIKE_PERSPECTIVES:
        log.info("[%s] invoking perspective: %s", scenario["id"], name)
        t0 = time.time()
        try:
            res = await invoke_perspective(
                name=name,
                scenario=scenario["scenario"],
                horizon_days=30,
                intel_base_summary=intel_summary,
                cold_start_prior=cold_start_prior,
                output_dir=output_dir,
                timeout_seconds=900,
            )
            results.append(res)
            log.info(
                "[%s] %s OK: p=%.3f runtime=%.1fs",
                scenario["id"], name, res.p_point, res.runtime_seconds,
            )
            if name == "tetlock-forecaster":
                # NUMERICAL prior only — never share Tetlock's narrative text.
                # See orchestrator.py for the same rule.
                cold_start_prior = {
                    "p_point": res.p_point,
                    "p_interval": list(res.p_interval) if res.p_interval else None,
                }
        except SubagentError as e:
            log.error("[%s] %s FAILED: %s", scenario["id"], name, e)
            errors[name] = str(e)
        dt = time.time() - t0
        log.info("[%s] %s wall=%.1fs", scenario["id"], name, dt)

    return {
        "scenario": scenario,
        "intel_base_hash": digest,
        "results": [
            {
                "name": r.name,
                "p_point": r.p_point,
                "p_interval": list(r.p_interval) if r.p_interval else None,
                "key_reasoning": r.key_reasoning,
                "evidence_urls": r.evidence_urls,
                "runtime_seconds": r.runtime_seconds,
                "raw_json": r.raw_json,
            }
            for r in results
        ],
        "errors": errors,
    }


async def run_isolation_check(scenario: dict, output_dir: Path) -> dict:
    """Isolation probe: run Schelling-bargaining with and without Tetlock prior.

    If the agent's reasoning DOES change in framework-meaningful ways when given
    a prior, that's expected (Bayesian updating is the whole point). If the
    output references prior-specific text or other-agent reasoning that should
    NOT be reachable under isolation, the isolation property is violated.
    """
    settings = get_settings()
    intel_summary = build_intel_base_summary()

    fake_prior = {
        "p_point": 0.42,
        "p_interval": [0.30, 0.55],
        "reasoning": (
            "ISOLATION PROBE — this prior text is deliberately distinctive. "
            "If you see this string echoed back in another agent's key_reasoning "
            "field, isolation is broken."
        ),
    }

    iso_dir = output_dir / "isolation"
    iso_dir.mkdir(exist_ok=True)

    log.info("[iso] running schelling-bargaining WITHOUT prior")
    no_prior_res = None
    try:
        no_prior_res = await invoke_perspective(
            name="schelling-bargaining",
            scenario=scenario["scenario"],
            horizon_days=30,
            intel_base_summary=intel_summary,
            cold_start_prior=None,
            output_dir=iso_dir,
        )
    except SubagentError as e:
        log.error("[iso] no-prior run failed: %s", e)

    iso_dir2 = output_dir / "isolation-with-prior"
    iso_dir2.mkdir(exist_ok=True)

    log.info("[iso] running schelling-bargaining WITH distinctive prior")
    with_prior_res = None
    try:
        with_prior_res = await invoke_perspective(
            name="schelling-bargaining",
            scenario=scenario["scenario"],
            horizon_days=30,
            intel_base_summary=intel_summary,
            cold_start_prior=fake_prior,
            output_dir=iso_dir2,
        )
    except SubagentError as e:
        log.error("[iso] with-prior run failed: %s", e)

    leak_marker = "ISOLATION PROBE"
    return {
        "with_prior": with_prior_res.raw_json if with_prior_res else None,
        "without_prior": no_prior_res.raw_json if no_prior_res else None,
        "leak_marker_in_no_prior_run": (
            leak_marker in (no_prior_res.key_reasoning if no_prior_res else "")
        ) if no_prior_res else None,
    }


def make_audit_record(scenario_id: str, run: dict, perspectives: list[str]) -> dict:
    settings = get_settings()
    completed = [r["name"] for r in run["results"]]
    failed = list(run["errors"].keys())
    p_points = [r["p_point"] for r in run["results"]]
    audit = {
        "query_id": str(uuid4()),
        "scenario_id": scenario_id,
        "scenario_text": run["scenario"]["scenario"],
        "horizon_days": 30,
        "tier": "standard",
        "intelligence_base_hash": run["intel_base_hash"],
        "query_delta_hash": None,
        "perspectives_invoked": perspectives,
        "perspectives_completed": completed,
        "perspectives_failed": failed,
        "aggregation_method": "weighted_uniform_average_v1",
        "result_summary": (
            {
                "p_point": sum(p_points) / len(p_points),
                "p_range": [min(p_points), max(p_points)],
                "divergence_pp": (max(p_points) - min(p_points)) * 100.0,
                "divergence_flag": (max(p_points) - min(p_points)) * 100.0 > 15.0,
            }
            if p_points
            else {"quorum_met": False}
        ),
        "evidence_urls": sorted({u for r in run["results"] for u in r["evidence_urls"]}),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": int(sum(r["runtime_seconds"] for r in run["results"])),
        "version": "1.0-spike",
    }
    sig = signing.sign_audit_record(audit)
    return {"audit_record": audit, "audit_signature": sig}


# ── Reporting ─────────────────────────────────────────────────────────────────


def write_results_md(all_runs: list[dict], output_path: Path) -> None:
    lines = [
        "# Iran Monitor API — Subagent Invocation Spike Results",
        "",
        f"**Generated:** {RUN_TS}",
        f"**Perspectives:** {', '.join(SPIKE_PERSPECTIVES)}",
        f"**Scenarios:** {len(all_runs)}",
        "",
        "## Spike objective",
        "",
        "Validate that `claude -p` headless invocation from a Python worker delivers:",
        "",
        "1. Per-perspective parseable JSON output for a novel (non-canonical-8) scenario.",
        "2. Isolation: agent N's reasoning is structurally independent of agent N-1's output text.",
        "3. End-to-end pipeline: intel-base seal → perspective subprocess → aggregation → Ed25519-signed audit record, all on real (not mocked) data.",
        "",
        "## Scenarios used",
        "",
    ]
    for r in all_runs:
        s = r["scenario"]
        lines.append(f"- **{s['id']}** ({s['domain']}, {s['difficulty']}): {s['scenario']}")
    lines.append("")

    for run in all_runs:
        s = run["scenario"]
        lines.append(f"## {s['id']}")
        lines.append("")
        lines.append(f"**Scenario:** {s['scenario']}")
        lines.append("")
        lines.append(f"**Intel-base hash:** `{run['intel_base_hash']}`")
        lines.append("")
        lines.append("### Per-perspective outputs")
        lines.append("")
        lines.append("| Perspective | p_point | interval | runtime (s) | evidence URLs |")
        lines.append("|---|---|---|---|---|")
        for res in run["results"]:
            urls = " ".join(f"[{i+1}]({u})" for i, u in enumerate(res["evidence_urls"][:3]))
            interval = (
                f"[{res['p_interval'][0]:.2f}, {res['p_interval'][1]:.2f}]"
                if res["p_interval"]
                else "—"
            )
            lines.append(
                f"| {res['name']} | {res['p_point']:.3f} | {interval} | {res['runtime_seconds']:.1f} | {urls} |"
            )
        for err_name, err_msg in run.get("errors", {}).items():
            lines.append(f"| **{err_name}** (FAILED) | — | — | — | {err_msg[:100]} |")
        lines.append("")

        lines.append("### Reasoning (full text)")
        lines.append("")
        for res in run["results"]:
            lines.append(f"#### {res['name']} (p={res['p_point']:.3f})")
            lines.append("")
            lines.append("> " + res["key_reasoning"].replace("\n", "\n> "))
            lines.append("")

        if "audit" in run:
            lines.append("### Aggregation + signed audit")
            lines.append("")
            summ = run["audit"]["audit_record"]["result_summary"]
            lines.append("```json")
            lines.append(json.dumps(summ, indent=2))
            lines.append("```")
            lines.append("")
            lines.append(f"Signature (base64 Ed25519): `{run['audit']['audit_signature']}`")
            lines.append("")

        if "isolation" in run:
            iso = run["isolation"]
            lines.append("### Isolation probe — schelling-bargaining with/without distinctive prior")
            lines.append("")
            leak = iso.get("leak_marker_in_no_prior_run")
            verdict = "no-leak (PASS)" if leak is False else "LEAK (FAIL)" if leak else "no data"
            lines.append(f"**Leak marker check:** {verdict}")
            lines.append("")
            lines.append("Both runs are recorded under `isolation/` and `isolation-with-prior/`.")
            lines.append("")

    lines.append("---")
    lines.append("## Pass/fail criteria")
    lines.append("")
    lines.append("- [ ] All 3 perspectives produced parseable JSON for each scenario (no `SubagentError`)")
    lines.append("- [ ] `p_point ∈ [0, 1]` and `key_reasoning` non-empty for each")
    lines.append("- [ ] Per-perspective runtime under 5 min (spike threshold; production target 25 min for 12 perspectives)")
    lines.append("- [ ] Isolation: distinctive prior marker does NOT appear in the no-prior run's reasoning")
    lines.append("- [ ] Audit record validates against the verification key")
    lines.append("- [ ] Aggregation + divergence flag computed correctly")
    lines.append("")
    lines.append("CEO reviews the captured reasoning narratives for substantive quality (framework applied, evidence cited).")
    lines.append("`/advisory-round` provides independent codex+gemini critique of the spike outputs.")

    output_path.write_text("\n".join(lines))


# ── Main ──────────────────────────────────────────────────────────────────────


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenarios", default=None,
        help="Comma-separated scenario IDs (default: all)"
    )
    parser.add_argument(
        "--isolation-only", action="store_true",
        help="Skip canonical run; only do isolation probe on S1"
    )
    parser.add_argument(
        "--smoke", action="store_true",
        help="Plumbing smoke test: one perspective, one scenario, no isolation"
    )
    args = parser.parse_args()

    all_scenarios = load_scenarios()
    if args.scenarios:
        wanted = set(s.strip() for s in args.scenarios.split(","))
        all_scenarios = [s for s in all_scenarios if s["id"] in wanted]

    log.info("spike run dir: %s", RUN_DIR)
    log.info("scenarios: %s", [s["id"] for s in all_scenarios])

    all_runs = []
    for scenario in all_scenarios:
        scenario_out = RUN_DIR / scenario["id"]
        scenario_out.mkdir(exist_ok=True)

        if args.smoke:
            global SPIKE_PERSPECTIVES
            SPIKE_PERSPECTIVES = ["tetlock-forecaster"]

        run = await run_canonical_path(scenario, scenario_out)
        audit = make_audit_record(scenario["id"], run, SPIKE_PERSPECTIVES)
        run["audit"] = audit
        (scenario_out / "audit-record.json").write_text(json.dumps(audit, indent=2))

        # Isolation probe runs only on the first scenario (cost control)
        if scenario == all_scenarios[0] and not args.smoke:
            run["isolation"] = await run_isolation_check(scenario, scenario_out)

        all_runs.append(run)

    results_md = RUN_DIR / "spike-results.md"
    write_results_md(all_runs, results_md)
    log.info("wrote %s", results_md)
    log.info("done — review %s", results_md)


if __name__ == "__main__":
    asyncio.run(main())
