# Iran Monitor API — Spike Test Protocol

**Purpose:** Mechanically validate that the production `subagent.invoke_perspective()`
code path (`src/iran_monitor_api/subagent.py`) delivers the isolation + output
quality that the cron's existing `/update` flow achieves via the in-CC Agent tool.

This is the gate the design doc names as Phase 1's first success criterion:

> **Spike gate (week 1):** subagent-invocation spike produces ≥3 perspective-agent
> assessments of a sample novel scenario with isolation verified (output of agent N
> is independent of agent N-1 — checkable by varying invocation order). Pass = build
> Phase 1. Fail = redesign invocation pattern before committing.

## What the spike exercises end-to-end

1. **`compute_intel_base_hash` + `seal`** — manifest of the iran-monitor data tree
   gets atomically sealed to `.intel-base-hash` so subsequent reads are deterministic.
2. **`build_intel_base_summary`** — terse digest of the intelligence base passed to
   each subagent prompt.
3. **`invoke_perspective`** — `claude -p` subprocess per perspective. Loads the
   agent definition from `.claude/agents/{name}.md`, embeds it in an isolated prompt
   that sandwiches the user scenario between `START_USER_SCENARIO`/`END_USER_SCENARIO`
   markers, captures stdout, parses JSON, writes per-perspective output file atomically.
4. **Cold-start prior propagation** — Tetlock runs first with no prior; its output
   becomes the prior fed to every other perspective.
5. **Aggregation + Ed25519 signing** — same `weighted_uniform_average_v1` math and
   `sign_audit_record` flow that the worker will run in production.

## Inputs

`spike/test-scenarios.json` carries 3 self-generated novel-scenario queries spanning
cyber, economic, and regional intelligence domains. Each is deliberately *outside* the
canonical 8 (A/V/B1–B4/C/D) so the perspective stack cannot fall back on existing
canonical-scenario priors.

Run with default `SPIKE_PERSPECTIVES = ["tetlock-forecaster", "schelling-bargaining",
"wack-strategic"]` — the smallest set that still exercises (a) Tetlock-first prior
propagation, (b) a bargaining-theory lens different from forecasting, and (c)
strategic-scenarios reasoning. Production runs use 12 perspectives; the spike's job
is to prove the *pattern*, not the full breadth.

## Procedure

```bash
cd iran-monitor-api

# One-off bootstrap (sign key locally; cron handles intel-base sealing in prod)
uv run iran-monitor-generate-key

# Smoke first (~3 min)
uv run python spike/run-spike.py --smoke --scenarios S1-cyber-germany

# Full run (~25 min): 3 scenarios × 3 perspectives + isolation probe on S1
uv run python spike/run-spike.py
```

Outputs land in `spike/runs/{YYYYMMDDTHHMMSSZ}/`:

```
{run-ts}/
├── spike-results.md                  # human-review artefact (this is what CEO + QA read)
├── S1-cyber-germany/
│   ├── perspectives/
│   │   ├── tetlock-forecaster.json
│   │   ├── schelling-bargaining.json
│   │   └── wack-strategic.json
│   ├── isolation/
│   │   └── perspectives/schelling-bargaining.json    # no-prior variant
│   ├── isolation-with-prior/
│   │   └── perspectives/schelling-bargaining.json    # distinctive-prior variant
│   └── audit-record.json                              # signed Ed25519 envelope
├── S2-oil-yuan/...
└── S3-houthi-redsea/...
```

## Pass/fail gates

A spike run is **PASS** iff *all* of the following hold:

| Gate | Mechanical check | Where to look |
|---|---|---|
| **Parseability** | All 9 perspective outputs (3 scenarios × 3 perspectives) parse as JSON with required fields `{p_point, key_reasoning}`. No `SubagentError`. | `spike-results.md` "Per-perspective outputs" tables; absence of FAILED rows |
| **Bounded probabilities** | Every `p_point ∈ [0, 1]`; every `p_interval` is `[lo, hi]` with `0 ≤ lo ≤ p_point ≤ hi ≤ 1`. | `spike-results.md` numeric columns |
| **Substantive reasoning** | Each `key_reasoning` field ≥ 200 chars, names ≥ 2 specific evidence items from the iran-monitor intelligence base. | "Reasoning (full text)" sections; QA-reviewed by codex+gemini |
| **Runtime** | Each perspective ≤ 5 min wall-clock on local Mac (production p50 budget for 12 perspectives is 25 min Premium). | `runtime_seconds` column |
| **Isolation** | The `ISOLATION PROBE` marker string from the distinctive prior does NOT appear in the no-prior run's reasoning. | "Isolation probe" section verdict |
| **Audit signature** | `verify_audit_record(audit, sig)` returns True against the public key at `keys/signing-key.pub`. | Per-scenario `audit-record.json`; verified by `uv run python -c "..."` snippet at bottom of this doc |
| **Aggregation correctness** | `result_summary.p_point ≈ mean(perspective.p_point)`; `divergence_flag == ((max - min) > 0.15)`. | `audit-record.json` per scenario |

A spike run is **FAIL** if any gate fails. CEO + advisory-round critique reviews the
*reasoning quality* dimension separately from these mechanical gates.

## Known limitations of the Phase 1 wrapper (record these, do not flag as bugs)

- **`evidence_urls` may be empty** even when reasoning references real intelligence
  items. The Phase 1 prompt asks for URLs but doesn't penalise the agent if it inlines
  evidence into `key_reasoning` instead. Phase 2 will tighten this with a strict
  schema validator.
- **No automated calibration check.** Novel scenarios have no ground truth, so we
  cannot Brier-score the spike output. Quality signal is reasoning-trace integrity
  + inter-perspective divergence, per design-doc premise #6.
- **Tetlock-first ordering is hard-coded.** Phase 2's routing classifier may select
  a different anchor perspective per scenario type.

## Advisory-round QA

After the spike completes, the captured `spike-results.md` is run through
`/advisory-round`:

```
/advisory-round spike/runs/{ts}/spike-results.md \
  --auto --topic iran-monitor-spike-{ts} \
  --out spike/runs/{ts}/advisory/
```

Stated objective for reviewers: *"Reviewer must reply with PASS in a Summary section
if the captured per-perspective reasoning (a) applies each perspective's stated
framework rigorously, (b) references at least two specific intelligence items from
the iran-monitor base per perspective, (c) shows independent reasoning chains across
perspectives (no copy-paste-feel between agents); else FAIL with reasoning."*

Codex (gpt-5.5 / high reasoning) + Gemini (gemini-3.1-pro-preview) review in parallel.
Opus synthesises with anti-bloat scoring.

## Verifying the audit signature manually

```bash
cd iran-monitor-api
uv run python <<'EOF'
import json
from iran_monitor_api.signing import verify_audit_record, load_verify_key
audit = json.load(open("spike/runs/<RUN_TS>/S1-cyber-germany/audit-record.json"))
ok = verify_audit_record(audit["audit_record"], audit["audit_signature"])
print("signature_valid =", ok)
EOF
```

Must print `signature_valid = True`.

## Failure-mode runbook

| If… | Then… |
|---|---|
| `SubagentError: agent definition not found` | The iran-monitor repo path is wrong. Set `IRAN_API_IRAN_MONITOR_REPO`. |
| `SubagentError: subagent X exited <non-zero>` | Likely `claude` CLI auth issue. Source `scripts/claude-with-env.sh`. Re-run smoke. |
| `SubagentError: output is not valid JSON` | The agent returned prose. Inspect the per-perspective directory for raw output; tighten the output contract in `subagent._build_prompt`. |
| Isolation gate fails (leak marker present) | Critical design issue. Fall back to fully fresh sessions per perspective (no shared CWD), or switch to the Claude Agent SDK with explicit context isolation. Block production deploy until resolved. |
| Runtime > 5 min for a single perspective | Token cap may be too high; tighten the agent definition or model param (`--model haiku` for non-critical perspectives). |

## When to re-run

- Before deploying any change to `subagent.py`, `gather.py`, `orchestrator.py`.
- Quarterly, alongside the canonical-8 calibration review.
- Whenever Claude CLI is upgraded (subprocess contract may change).
- When a new perspective agent is added or an existing definition is edited.

## What the CEO reviews

The spike's mechanical gates are checked by the script. The *qualitative* gate is:

1. Read `spike-results.md` → "Reasoning (full text)" sections.
2. For each perspective, does the reasoning read like that framework? (Tetlock should
   compute base rates and Fermi-decompose; Schelling should reason about coercion and
   credibility; Wack should name predetermined elements and signposts.)
3. Cross-perspective: do the three agents *disagree about the right things*? If all
   three agree mechanically, the prior may be over-influencing. If they disagree
   wildly with no thematic coherence, the prompt is leaking noise.
4. Check at least one cited intelligence item against `iran-monitor/data/` to confirm
   it's real (not fabricated).

If steps 2–4 read well to a domain expert, the spike passes the qualitative gate.
Combined with mechanical PASS, the gate is cleared and Phase 1 production deploy is
unblocked.
