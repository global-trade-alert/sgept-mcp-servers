# Iran Monitor API — Developer Guide

You're looking at the queryable inference API that wraps the Iran Conflict Scenario Monitor. This guide is the entry point for engineers who'll be developing, maintaining, or extending it.

**Read this first.** It walks the architecture, sets up your local environment, points at the design docs that explain *why* things are the way they are, and gives a tour of the code in reading order.

---

## TL;DR

You have **two related codebases**:

| Repo | Purpose |
|---|---|
| `iran-monitor` (separate repo, jf-thought/sgept-analytics/iran-monitor) | The cron-driven analytics monitor. Runs every 6 hours, produces the canonical 8-scenario report. Owns the perspective-agent definitions in `.claude/agents/` and the verified intelligence base in `data/`. |
| `sgept-mcp-servers` (this repo) | Houses two Python packages: <br>`a2a-protocol/` — generic Google A2A protocol implementation<br>`iran-monitor-api/` — the queryable API that exposes the monitor's perspective stack over A2A (this directory) |

The iran-monitor *analytics monitor* and the iran-monitor *API* are different services. The API does NOT re-run the cron's GATHER → ASSESS pipeline. It runs ASSESS-only against the cron's verified intelligence base, for buyer-submitted novel scenarios. It also adds A2A protocol surfaces (JSON-RPC 2.0, SSE streaming, multi-turn clarification) plus a REST back-compat surface.

---

## The 3-minute architecture tour

```
                      ┌──────────────────────────────────────────────────┐
                      │  iran-monitor (analytics)                        │
                      │  Cron every 6h: GATHER → 14 perspectives →       │
                      │  AGGREGATE → WRITE → PUBLISH static report       │
                      │                                                  │
                      │  Produces (on disk):                             │
                      │    data/probabilities*.csv                       │
                      │    data/perspective-assessments/YYMMDD-HHMM/*    │
                      │    data/tracking/peripheral-watch-list.jsonl     │
                      │    .claude/agents/{14 perspective agents}.md     │
                      │                                                  │
                      │  Sealed at end of cron Phase 6:                  │
                      │    data/.intel-base-hash  (sha256)               │
                      └─────────────────┬────────────────────────────────┘
                                        │ read-only
                                        ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  iran-monitor-api  (this build)                                  │
   │                                                                  │
   │  Buyer query → FastAPI server (port 8080)                        │
   │                                                                  │
   │  Two transport surfaces:                                         │
   │    A. REST  (POST /v1/queries, GET /v1/queries/{id})             │
   │       — back-compat for the named pilot buyer                    │
   │    B. A2A   (/.well-known/agent-card.json,                       │
   │              POST /v1/jsonrpc, POST /v1/jsonrpc/stream)          │
   │       — Google A2A protocol; the canonical surface               │
   │                                                                  │
   │  Backend logic:                                                  │
   │    IranMonitorBackend (implements a2a_protocol.AgentBackend)     │
   │      ↓                                                           │
   │    SQLite queue (status: submitted → working → completed)        │
   │      ↓                                                           │
   │    Worker process                                                │
   │      ├── (A2A only) scenario clarifier — multi-turn if needed    │
   │      ├── (Premium only) scenario-targeted live GATHER            │
   │      ├── Tetlock-forecaster perspective FIRST (cold-start prior) │
   │      ├── Remaining N-1 perspectives SEQUENTIALLY                 │
   │      │      isolation via fresh `claude -p` subprocess per agent │
   │      ├── Aggregate: weighted mean + divergence flag              │
   │      ├── (Premium only) briefing-writer → markdown + structured  │
   │      │      disagreements + high-elasticity events               │
   │      ├── Ed25519-sign audit record                               │
   │      ├── Publish SSE events at every state transition            │
   │      └── (optional) SMTP email delivery                          │
   └──────────────────────────────────────────────────────────────────┘
```

The whole system is a thin orchestration layer. The *intelligence* lives in iran-monitor; this API exposes it on demand for novel scenarios.

---

## Local setup

```bash
# Clone the repo (already done if you're reading this)
git clone git@github.com:global-trade-alert/sgept-mcp-servers.git
cd sgept-mcp-servers/iran-monitor-api

# Install deps (uv is required — https://docs.astral.sh/uv/)
uv sync

# Run tests
uv run pytest                    # iran-monitor-api: 77 tests
cd ../a2a-protocol && uv run pytest   # a2a-protocol: 36 tests
```

You also need:

- The `iran-monitor` repo cloned at `~/Documents/GitHub/jf-private/jf-thought/sgept-analytics/iran-monitor` (or set `IRAN_API_IRAN_MONITOR_REPO`). The API reads the intelligence base from there.
- The Claude CLI (`claude`) on `$PATH`, configured against your Claude auth (Max subscription or API key). The worker spawns `claude -p` subprocesses for each perspective agent.

Generate a local signing key (one-off, ignored by .gitignore):

```bash
uv run iran-monitor-generate-key
```

### Running locally

Three processes, in three terminals:

```bash
# Terminal 1 — HTTP API on :8080
uv run iran-monitor-api

# Terminal 2 — Background worker (polls SQLite queue, runs the pipeline)
uv run iran-monitor-worker

# Terminal 3 — End-to-end demo against both servers
uv run python spike/local-demo.py
```

Optional: a fast mock A2A agent on :8081 (echo-only, completes in <1s, demonstrates the protocol surface without LLM calls):

```bash
cd ../a2a-protocol && uv run python -m a2a_protocol._mock_server
```

### Running the spike

The subagent-invocation spike is what validated `claude -p` as the right primitive for orchestration:

```bash
uv run python spike/run-spike.py            # full spike (~25 min, 3 scenarios × 3 perspectives)
uv run python spike/run-spike.py --smoke    # smoke (~3 min, 1 scenario, 1 perspective)
```

Read `spike/test-protocol.md` for the pass/fail criteria. Outputs land in `spike/runs/{YYYYMMDDTHHMMSSZ}/`. Re-run the spike (and `spike/qa-advisory-round.sh` for codex+gemini independent QA) whenever you change `subagent.py`, `gather.py`, `orchestrator.py`, or `briefing_writer.py`.

---

## Code tour (in reading order)

Read these files in this order to understand the system fastest.

### 1. The contract — `a2a-protocol/src/a2a_protocol/backend.py`

The Protocol interface any A2A-enabled asset implements. Six methods: `submit_task`, `continue_task`, `cancel_task`, `get_task`, `stream_events`, `authenticate`. **The single most important file.** Once you understand this, everything else falls into place.

### 2. The bridge — `iran-monitor-api/src/iran_monitor_api/backend.py`

`IranMonitorBackend` — Iran-monitor's implementation of `AgentBackend`. Translates A2A `Message` → internal `CreateQueryRequest`; translates the internal `QueryResult` → A2A `Task` + `Artifact`. This is where the protocol layer meets the business logic.

### 3. The worker — `iran-monitor-api/src/iran_monitor_api/worker.py`

The async loop that drains the queue. Runs the clarifier (A2A only), the Premium GATHER (Premium only), the ASSESS pipeline, the briefing writer (Premium only), audit signing, and email delivery. Also publishes SSE events at every state transition.

### 4. The ASSESS pipeline — `iran-monitor-api/src/iran_monitor_api/orchestrator.py`

Sequentially invokes perspective subagents with isolation. Tetlock-forecaster runs first to produce a numerical cold-start prior; subsequent perspectives receive only the prior's `{p_point, p_interval}` (NOT Tetlock's reasoning text — see commit `3cec901` for why that matters). Aggregates with weighted-uniform mean; flags divergence at >15pp.

### 5. The subagent invocation — `iran-monitor-api/src/iran_monitor_api/subagent.py`

The spike's load-bearing primitive. Loads an agent definition (`.claude/agents/{name}.md`), builds a prompt that sandwiches the user scenario between `START_USER_SCENARIO`/`END_USER_SCENARIO` markers, spawns `claude -p` in a fresh subprocess, parses JSON output, writes atomically. **Isolation by process boundary, not by prompt convention.**

### 6. The briefing writer — `iran-monitor-api/src/iran_monitor_api/briefing_writer.py`

(Premium tier only.) After aggregation, one more `claude -p` synthesis step that takes the per-perspective outputs and produces structured `major_disagreements`, `high_elasticity_events`, and a 500–1500 word `briefing_markdown`.

### 7. The clarifier — `iran-monitor-api/src/iran_monitor_api/scenario_clarifier.py`

(A2A tier only — REST clients can't reply mid-task.) Pre-flight LLM check for horizon + named actor + named capability. If underspecified, the worker transitions to `input-required`; caller's next `message/send` is folded into the scenario via `db.update_scenario_after_clarification` and the clarifier re-runs. Cap at 3 round-trips → `rejected`.

### 8. The Premium GATHER — `iran-monitor-api/src/iran_monitor_api/gather.py`

(Premium tier only.) Scenario-targeted live web search before ASSESS. Keyword extraction → ≤20 WebSearch + ≤60 WebFetch → URL+publication-date verification → query-scoped intel delta JSONL appended to the standing intelligence base for this query only.

### 9. The protocol — the rest of `a2a-protocol/src/a2a_protocol/`

- `card.py` — `AgentCard` model + `/.well-known/agent-card.json` route factory
- `models.py` — A2A wire models (`Task`, `Message`, `Part` discriminated, `Artifact`, status-update events)
- `lifecycle.py` — 8-state task lifecycle enum + `is_valid_transition` validator
- `jsonrpc.py` — JSON-RPC 2.0 dispatcher (`message/send`, `tasks/get`, `tasks/cancel`)
- `sse.py` — SSE streaming for `message/stream` + `tasks/resubscribe`
- `event_bus.py` — async pub/sub per task; in-memory now, Redis later (same interface)
- `auth.py` — Bearer dependency delegating to backend
- `errors.py` — JSON-RPC + A2A error codes
- `server.py` — FastAPI app factory: `create_app(backend) → FastAPI`
- `client.py` — Generic A2AClient (JSON-RPC + SSE) for any A2A endpoint
- `message_history.py` — generic per-task message store for multi-turn

### 10. The REST surface — `iran-monitor-api/src/iran_monitor_api/api/`

Back-compat for the named pilot buyer. `routes.py` (POST /v1/queries, GET /v1/queries/{id}), `auth.py` (Bearer), `rate_limit.py` (per-org sliding window). The REST path skips the clarifier; A2A path runs it. Both share the same orchestrator/worker/DB.

### 11. The persistence — `iran-monitor-api/src/iran_monitor_api/db.py`

SQLite (WAL). One `queries` table + one `rate_limit_events` table. Atomic claim/complete; crash-recovery via `find_running_queries` + `reset_running_to_queued` on worker startup.

### 12. The signing — `iran-monitor-api/src/iran_monitor_api/signing.py`

Ed25519 over canonical JSON. Public key at `/.well-known/iran-monitor-signing-key.pub`. Buyer-side verification snippet in `client/iran_monitor_client.py` and `ONBOARDING.md`.

### 13. The Python SDK — `iran-monitor-api/client/iran_monitor_client.py`

Single-file SDK. Two classes: `Client` (REST) and (by extension) usage of the generic `a2a_protocol.client.A2AClient` (JSON-RPC + SSE). Both return typed dataclass results with audit-verification helpers.

---

## Documentation map

Everything is in this repo. Self-contained.

| Document | What it answers |
|---|---|
| `README.md` (this directory) | What the service is and the high-level shape |
| `DEVELOPING.md` (this file) | How the codebase is organised + setup + code tour |
| `ONBOARDING.md` | What a pilot buyer receives on day 1 (REST + A2A + SDK + signature verification) |
| `DEPLOY.md` | Production deploy checklist for Metis (DNS, Caddy, systemd, env, smoke tests) |
| `spike/test-protocol.md` | Subagent-invocation spike — pass/fail criteria, failure runbook, when to re-run |
| `spike/runs/20260512T183909Z/` | The v2 spike that passed (after the v1 isolation fix) — includes the codex+gemini advisory-round QA |
| `documentation/01-design-doc.md` | The original office-hours design doc — premises, alternatives considered, recommended approach. **Read for the why.** |
| `documentation/02-access-surface-proposal.md` | The 5-archetype strategy review that chose "concierge + landing + extensions + email" over self-serve / chat / pure-MCP |
| `documentation/03-a2a-retrofit-plan.md` | The implementation plan that drove the A2A retrofit. Layers, files, reuse map, generalization, verification. |
| `../a2a-protocol/README.md` | The protocol package's own README |
| `../a2a-protocol/docs/EXAMPLE-GTA-BACKEND.md` | Sketch of how to A2A-enable the GTA database next, using the same protocol package. Validates the generalization payoff. |
| `landing/index.html` | Public marketing page (served at `iran-monitor.sgept.org/`) |
| `client/README.md` | SDK consumer doc |

---

## How to extend this

### Adding a new perspective agent

Perspective agents live in the **iran-monitor repo** at `.claude/agents/{name}.md`. To add one:

1. Write the agent definition in markdown (model + tools + framework description). Use existing agents as templates (`tetlock-forecaster.md`, `schelling-bargaining.md`, etc.).
2. Add the name to `iran-monitor-api/src/iran_monitor_api/models.py::ALL_PERSPECTIVES`.
3. Decide whether it should be in `DEFAULT_PERSPECTIVES` (invoked unless the buyer overrides).
4. Re-run the spike (`spike/run-spike.py`) and the advisory-round QA. Verify the new agent's reasoning is framework-distinct and grounded in the intelligence base.

### A2A-enabling a different asset (GTA, DPA, etc.)

Read `../a2a-protocol/docs/EXAMPLE-GTA-BACKEND.md`. The recipe:

1. Create a new package alongside iran-monitor-api (e.g. `gta-a2a/`).
2. Implement `a2a_protocol.AgentBackend` — submit/continue/cancel/get/stream/authenticate. Reuse your asset's existing query engine.
3. Define your `AgentCard` with the skills your asset exposes.
4. Compose `create_app(YourBackend())` and run it behind Caddy at `a2a-{your-asset}.globaltradealert.org`.

The generalization smoke (`a2a-protocol/tests/test_generalization_smoke.py`) gates that the protocol package stays asset-agnostic — if your changes break that test, the abstraction has leaked and the test should fail.

### Changing the protocol surface

A2A spec evolves. Pin the version on the `AgentCard.protocolVersion` field. Update `a2a-protocol/src/a2a_protocol/models.py` for any new wire fields. Re-run all tests in both packages; the generalization smoke is your canary.

### Deploying changes

Production runs on the Metis VPS (`204.168.141.21`). See `DEPLOY.md` for the checklist. The short version:

```bash
ssh deploy@204.168.141.21
cd ~/jf-private && ./scripts/pull-all.sh
cd jf-dev/sgept-dev/sgept-mcp-servers/iran-monitor-api
bash scripts/install-on-metis.sh
sudo systemctl restart iran-monitor-api iran-monitor-worker
```

---

## Where to learn more about A2A

- **Spec:** <https://a2a-protocol.org/latest/specification/>
- **GitHub:** <https://github.com/a2aproject/A2A>
- **Linux Foundation Agentic AI Foundation (governance):** <https://www.linuxfoundation.org/agentic-ai>

`documentation/03-a2a-retrofit-plan.md` includes a verdict section on the May 2026 protocol landscape (why A2A is the right pick over ACP/AGNTCY/MCP-as-agent-protocol/etc.) and a `documentation/02-access-surface-proposal.md` covers the five access-surface archetypes considered before settling on the current shape.

---

## Test counts (as of the latest commit)

- `iran-monitor-api`: **77 tests** (models, db, signing, intel-hash, orchestrator, routes, backend, briefing-writer, email-delivery)
- `a2a-protocol`: **36 tests** (lifecycle, models, card, jsonrpc, generalization-smoke)
- **Total: 113 green.**

Run both before opening any PR:

```bash
cd iran-monitor-api && uv run pytest
cd ../a2a-protocol && uv run pytest
```

---

## Production gates remaining

These gate Phase 1 production deployment (not part of the build itself):

1. **DNS** — point `a2a.globaltradealert.org` → `204.168.141.21` (CEO action, pending colleague availability)
2. **First pilot buyer call** — collect three verbatim pilot scenarios + probability-action thresholds (tracked as JCC-956)
3. **SMTP provider** — pick one (Postmark / Resend / Mailgun / Metis's existing infrastructure) and populate `IRAN_API_SMTP_*` in the env file
4. **Hook iran-monitor cron Phase 6** to call `iran-monitor-seal-intel-base` so Standard-tier queries see real intelligence-base hashes
5. **Mint pilot keys** via `scripts/add-pilot-key.py add <org>`; deliver out-of-band to the buyer

After those, the service is live. `DEPLOY.md` is the operational manual.

---

## Style + conventions

- **Python ≥ 3.11.** uv for deps. FastAPI + Pydantic v2.
- **No comments that describe what the code does** — names + types do that. Comments explain *why* (a non-obvious invariant, a workaround, a constraint).
- **Tests are evidence, not ceremony.** When a behaviour is load-bearing for safety (isolation, signing, audit integrity), there's a test that fails if you break it.
- **Editing across both packages?** Both pass pytest before commit. `git push` to origin. The `sgept-mcp-servers` repo is the system of record.

---

## Asking for help

- **Methodology questions** (what does each perspective agent do, why this aggregation rule, why these scenario fields): `johannes.fritz@sgept.org`
- **Architecture / code questions:** `liubomyr.garvyliv@sgept.org`
- **Operations / deployment:** Metis runbook in `~/jf-private/jf-metis/`
