# Iran Monitor API — Full A2A Protocol Retrofit (as a generalizable pattern)

## Protocol-landscape verdict (mid-2026 research)

A2A is the right protocol to build against. Research before locking this plan returned:

- **Governance:** A2A moved to the Linux Foundation Agentic AI Foundation (Dec 2025), with Anthropic, OpenAI, Google, Microsoft, AWS, Block all co-founders/board. MCP (Anthropic) is a sibling project under the same foundation, scoped to model↔tool context — not a competitor.
- **Consolidation:** IBM ACP (the main 2025 competitor) was merged into A2A in Sept 2025. AGNTCY (Cisco-led) is positioned as a *complementary* discovery/identity layer under Linux Foundation too, not a competing wire protocol.
- **Spec stability:** A2A v1.0 released April 2026 with a 3-year compatibility guarantee. v1.2 added cryptographic agent cards.
- **Adoption:** 150+ production orgs; AWS Bedrock AgentCore, Azure AI Foundry, Google Vertex AI all integrate A2A first-class. Financial-services and supply-chain RFPs explicitly require A2A — that's exactly the buyer category for SGEPT's wedge.
- **Anthropic specifically:** AAIF co-founder, public stance that MCP + A2A are complementary. Claude Managed Agents is MCP-native (tools) but NOT yet A2A-native (orchestration) — we layer A2A on top as the inter-agent messaging surface. No architectural conflict.
- **Migration risk:** Without abstraction, post-launch pivot estimated $70K–$240K. With the `AgentBackend` abstraction already in this plan (originally for GTA/DPA transferability), migration cost drops to $20K–$50K. The generalization layer is also the protocol hedge.

**What would change this verdict** (we'd re-evaluate if any of these landed):
- AGNTCY captures >25% of financial-services RFPs vs. A2A (currently <5%).
- Anthropic ships a proprietary agent-interop protocol (extremely unlikely — they're AAIF co-founder).
- A2A introduces a breaking v2.0 inside the 3-year LTS window.

Net: build A2A. The `AgentBackend` abstraction below doubles as the migration hedge if the landscape shifts unexpectedly in 2027+.

## Context

What's currently deployed at `a2a.globaltradealert.org` is an async-task REST API. The CEO chose the `a2a` subdomain to position the service in the Google A2A (Agent-to-Agent) ecosystem, but the implementation is REST-async-task, not A2A. Specifically missing:

- No agent card at `/.well-known/agent-card.json`
- No JSON-RPC 2.0 transport (pure POST/GET)
- Task lifecycle has 5 states (queued, running, completed, partial, failed); A2A specifies 8 (submitted, working, input-required, completed, failed, canceled, rejected, auth-required)
- No SSE streaming (polling only)
- No multi-turn within a task (caller cannot send a second Message to clarify; worker cannot ask back)

A2A is a real growing standard (Google + Anthropic + LangChain + IBM + Spring AI). The reputation cost of squatting `a2a.` without supporting the protocol is real — any sophisticated A2A-native client will look for the agent card first and find nothing.

**Strategic intent (from CEO, 2026-05-13):** the Iran-monitor build is *an experiment to understand what it takes to A2A-enable SGEPT's other assets* — most importantly the Global Trade Alert database, but also DPA, philanthropy queries, and any future analytic surface. The retrofit must be authored such that the A2A protocol layer is a **reusable module**, not Iran-monitor-coupled. The Iran-monitor service is the first consumer of this module; GTA, DPA, etc. should be the second, third, fourth — without re-implementing the protocol each time.

**Outcome:** an A2A-spec-compliant service at `a2a.globaltradealert.org`. Existing REST endpoints remain as a backward-compatible transport for the named pilot buyer (who has already been onboarded against REST). New A2A surface lives alongside, not as a replacement. Critically, the A2A code is structured so that a future `a2a-gta` service can reuse the same modules with a different `AgentBackend` implementation.

## Spec reference

- Spec: <https://a2a-protocol.org/latest/specification/>
- Repo: <https://github.com/a2aproject/A2A>
- Agent Card location: `/.well-known/agent-card.json`
- Wire: HTTPS + JSON-RPC 2.0 + Server-Sent Events
- Methods: `message/send`, `message/stream`, `tasks/get`, `tasks/cancel`, `tasks/resubscribe`, `tasks/pushNotificationConfig/set` (optional)
- Lifecycle: `submitted → working → (input-required ↔ working)* → (completed | failed | canceled | rejected)`; also `auth-required` if the agent needs credentials mid-task

## Generalization: the AgentBackend abstraction

The single biggest design choice in this plan: **all A2A protocol code goes into a new top-level package** (`a2a_protocol/` next to `iran_monitor_api/`) **that knows nothing about Iran scenarios.** Iran-monitor wires its existing business logic into A2A by implementing a single `AgentBackend` interface; a future GTA-a2a service implements the same interface against the GTA backend.

```python
# a2a_protocol/backend.py — the only Iran-monitor-shaped thing is the implementation
class AgentBackend(Protocol):
    """What an A2A-enabled asset must implement. Protocol-agnostic."""

    agent_card: AgentCard               # static card describing skills + auth

    async def submit_task(
        self, message: Message, task_id: TaskID, context: TaskContext,
    ) -> TaskHandle: ...

    async def continue_task(
        self, task_id: TaskID, message: Message, history: list[Message],
    ) -> TaskHandle: ...

    async def cancel_task(self, task_id: TaskID) -> None: ...

    async def get_task(self, task_id: TaskID) -> Task: ...

    async def stream_events(self, task_id: TaskID) -> AsyncIterator[TaskEvent]: ...

    def authenticate(self, token: str) -> AuthContext | None: ...
```

Everything else in `a2a_protocol/` — JSON-RPC dispatcher, SSE streaming, agent-card serving, task lifecycle, message-history persistence, multi-turn clarification machinery — is generic. The protocol package depends on `AgentBackend`; Iran-monitor depends on the protocol package and provides an `IranMonitorBackend`. The future `gta-a2a` service depends on the same protocol package and provides a `GTABackend`.

This means **layers 1–4 of the implementation are GTA-reusable as-is.** Layer 5 (the scenario clarifier) is Iran-monitor-specific in *content* but its *shape* (pre-flight LLM clarifier that runs before the main backend work) is reusable; GTA-a2a will need its own clarifier with different fields to check.

```
sgept-mcp-servers/
├── iran-monitor-api/                   ← this build
│   └── src/iran_monitor_api/
│       ├── ...                         ← existing
│       └── backend.py                  ← NEW: implements AgentBackend
└── a2a-protocol/                       ← NEW reusable package
    └── src/a2a_protocol/
        ├── __init__.py
        ├── backend.py                  ← AgentBackend Protocol
        ├── card.py                     ← AgentCard model + /.well-known route
        ├── jsonrpc.py                  ← JSON-RPC 2.0 dispatcher
        ├── sse.py                      ← SSE streaming endpoint + event bus
        ├── models.py                   ← A2A Task/Message/Part/Artifact (per spec)
        ├── lifecycle.py                ← 8-state machine
        ├── auth.py                     ← Bearer scheme (delegates to backend)
        ├── errors.py                   ← JSON-RPC error mapping
        ├── server.py                   ← FastAPI app factory: take a backend → returns app
        └── client.py                   ← Generic A2A client (JSON-RPC + SSE)
```

A future GTA service is therefore ~3 days of work, not ~10: implement `GTABackend`, write a few config lines, point Caddy at `a2a-gta.globaltradealert.org`. That's the test of whether this experiment succeeded.

## Approach

Retrofit in five layers. Layers 1–4 live in the new `a2a-protocol/` package and are generic. Layer 5 lives in `iran-monitor-api/` and is the Iran-specific consumer.

### Layer 1 — Agent Card + AgentBackend Protocol (~1 day)

**Where**: `a2a-protocol/`

**Files**:
- New: `a2a-protocol/pyproject.toml`, README, etc.
- New: `a2a-protocol/src/a2a_protocol/backend.py` (the `AgentBackend` Protocol)
- New: `a2a-protocol/src/a2a_protocol/card.py` (AgentCard pydantic model + FastAPI route factory)
- New: `a2a-protocol/src/a2a_protocol/models.py` (A2A `Task`, `Message`, `Part`, `Artifact`, etc., per spec)
- New: `iran-monitor-api/src/iran_monitor_api/backend.py` (`IranMonitorBackend` skeleton implementing `AgentBackend`)
- Modified: `iran-monitor-api/src/iran_monitor_api/main.py` (compose the FastAPI app from `a2a_protocol.server.create_app(IranMonitorBackend())`)

**What ships**:
- `AgentBackend` Protocol with method signatures (no implementations yet — those land in later layers via Iran-monitor's backend).
- `AgentCard` Pydantic model matching the A2A schema.
- `GET /.well-known/agent-card.json` route mounted via the protocol package, but the card *content* comes from the backend's `agent_card` property.
- Iran-monitor's card declares one skill (`assess_scenario`) with description, examples, input/output modes. Capabilities: `streaming: true`, `pushNotifications: false` (Phase 2), `stateTransitionHistory: true`.

### Layer 2 — JSON-RPC 2.0 dispatcher (~2 days)

**Where**: `a2a-protocol/`

**Files**:
- New: `a2a-protocol/src/a2a_protocol/jsonrpc.py`
- New: `a2a-protocol/src/a2a_protocol/errors.py`
- New: `a2a-protocol/src/a2a_protocol/auth.py`
- Modified: `iran-monitor-api/src/iran_monitor_api/backend.py` (implement `submit_task`, `get_task`, `cancel_task`, `authenticate`)

**What ships**:
- `POST /v1/jsonrpc` accepts JSON-RPC 2.0 envelopes. Single endpoint, method dispatch by `method` field.
- Methods implemented:
  - `message/send` — submit a new task OR continue an existing task (continuation handled in layer 5)
  - `tasks/get` — retrieve task by id, return A2A `Task` object
  - `tasks/cancel` — transition to `canceled`
- Bearer-token auth on the JSON-RPC route; delegates the actual auth check to `backend.authenticate`.
- JSON-RPC error mapping: validation → -32602, auth → -32001 (custom), rate-limit → -32002, internal → -32603.
- Iran-monitor's backend implements these by calling the **existing** `orchestrator.run_assess`, `db.enqueue_query`, `api.rate_limit.check_and_record`, `api.auth.require_api_key` — translating A2A `Message` ↔ our existing `CreateQueryRequest` and translating `QueryResult` ↔ A2A `Task` + `Artifact`.

### Layer 3 — Extended task lifecycle (~½ day)

**Where**: both packages

**Files**:
- New: `a2a-protocol/src/a2a_protocol/lifecycle.py` (TaskState enum with the 8 A2A states + a transition validator)
- Modified: `iran-monitor-api/src/iran_monitor_api/models.py` (extend existing `Status` enum to alias new A2A states)
- Modified: `iran-monitor-api/src/iran_monitor_api/db.py` (no destructive change — status is TEXT)
- New: `tests/test_lifecycle.py` in both packages

**What ships**:
- A2A `TaskState` enum: `submitted`, `working`, `input-required`, `completed`, `failed`, `canceled`, `rejected`, `auth-required`.
- Iran-monitor's existing `Status` enum gains aliases: `QUEUED` ≡ `SUBMITTED`, `RUNNING` ≡ `WORKING`. Backend translation layer renders the right value depending on transport (REST clients keep seeing `queued / running`; A2A clients see `submitted / working`).
- Transition validator: `is_valid_transition(from_state, to_state) -> bool`. Used by the worker before transitioning.

### Layer 4 — SSE streaming + event bus (~1.5 days)

**Where**: `a2a-protocol/`

**Files**:
- New: `a2a-protocol/src/a2a_protocol/sse.py`
- New: `a2a-protocol/src/a2a_protocol/event_bus.py` (in-process asyncio.Queue-based pub/sub keyed by task_id; subclassable for Redis later)
- Modified: `iran-monitor-api/src/iran_monitor_api/worker.py` (publish status events to the bus at every transition)
- Modified: `iran-monitor-api/src/iran_monitor_api/db.py` (new `task_events` table for crash-safe resubscribe)

**What ships**:
- `message/stream` JSON-RPC method returns SSE stream (`Content-Type: text/event-stream`).
- `tasks/resubscribe` re-attaches a stream to a previously-streaming task. Replays from `task_events`.
- Event types: `task-status-update`, `task-artifact-update`. Heartbeat events every 30s.
- Iran-monitor's worker publishes events as the existing pipeline progresses:
  - `submitted → working` after `db.claim_next_query`
  - `working → working` with progress metadata at each `db.mark_perspective_completed` (per perspective completed)
  - `working → working` with artifact-fragment event when `briefing_writer.write_briefing` produces the briefing
  - `working → completed | partial | failed` at the end
- Granularity: **event-level**, not token-level. Documented on the agent card as `capabilities.streamingGranularity: "event"` (extension — A2A allows it). Reason: `claude -p --output-format text` captures stdout once at the end; we don't get token streaming from perspective agents.

### Layer 5 — Multi-turn input-required (~2.5 days)

**Where**: protocol + Iran-monitor

**Files**:
- New: `a2a-protocol/src/a2a_protocol/message_history.py` (generic per-task append-only message store)
- New: `iran-monitor-api/src/iran_monitor_api/scenario_clarifier.py` (Iran-specific clarifier subagent — checks horizon, named actor, named capability/instrument)
- Modified: `iran-monitor-api/src/iran_monitor_api/worker.py` (call clarifier; transition to `input-required` if needed; resume on caller's next message)
- Modified: `iran-monitor-api/src/iran_monitor_api/orchestrator.py` (accept resumed-task context with message history)
- Modified: `iran-monitor-api/src/iran_monitor_api/db.py` (new `task_messages` table)
- Modified: `a2a-protocol/src/a2a_protocol/jsonrpc.py` (`message/send` continuation handling: detect `taskId` in params → call `backend.continue_task` instead of `submit_task`)
- New: `tests/test_clarifier.py`, `tests/test_multi_turn.py`

**What ships**:
- Pre-flight clarifier runs as the first worker step. Checks for Iran-monitor: horizon present and ∈ {7,14,30,60,90}; at least one named actor; at least one named capability/instrument; optional probability-action threshold.
- If clarifier flags missing fields, worker writes a `Message` to `task_messages` with the clarification question and transitions to `input-required`. SSE stream emits the question.
- The caller's next `message/send` (with matching `taskId`) is appended to the task's history. Worker resumes `input-required → working` and re-runs the clarifier with the augmented context.
- Up to 3 round-trips; beyond that, task → `rejected` with explanation.
- **REST path unaffected**: if `tier`, `horizon`, and a non-trivial scenario are present in the original REST request, the REST path skips the clarifier (REST clients can't respond to clarifications mid-task).
- The generic `message_history` module is reusable by GTA-a2a; the *clarifier* itself is Iran-monitor-specific because the validation criteria are different per domain.

## Documentation + buyer-facing surface (~1 day, parallel to layers 1–5)

**Files**:
- `ONBOARDING.md` — add "A2A protocol" section above the existing "Three integration patterns" section. Patterns become four (curl REST / SDK REST / SDK A2A / their A2A-native agent via agent-card discovery). Show agent-card URL, sample JSON-RPC envelope, SSE example.
- `landing/index.html` — replace the "How a query looks" example with a tabbed view (A2A JSON-RPC first, REST second). Lead value cards with "A2A-native protocol surface". Update differentiation section.
- `client/iran_monitor_client.py` — extend with `A2AClient` class alongside `Client`. Same business logic; different transport.
- `DEPLOY.md` — add smoke tests for the new endpoints.
- New: `a2a-protocol/README.md` — the generalizable pattern doc: how to wrap a new asset in A2A by implementing `AgentBackend`. The "experiment outcome" deliverable.
- New: `a2a-protocol/docs/EXAMPLE-GTA-BACKEND.md` — sketch of how a `GTABackend` would look (no code, just signatures + decisions). Validates that the pattern actually transfers.

## Critical files

| Layer | Path | Action |
|---|---|---|
| pkg | `a2a-protocol/pyproject.toml`, etc. | NEW package scaffold |
| 1 | `a2a-protocol/src/a2a_protocol/backend.py` | NEW (`AgentBackend` Protocol) |
| 1 | `a2a-protocol/src/a2a_protocol/card.py` | NEW (card model + FastAPI route factory) |
| 1, 2 | `a2a-protocol/src/a2a_protocol/models.py` | NEW (A2A Task/Message/Part/Artifact) |
| 1, 2 | `a2a-protocol/src/a2a_protocol/server.py` | NEW (FastAPI app factory: `create_app(backend) → FastAPI`) |
| 2 | `a2a-protocol/src/a2a_protocol/jsonrpc.py` | NEW |
| 2, 3 | `a2a-protocol/src/a2a_protocol/errors.py` | NEW (JSON-RPC error codes) |
| 3 | `a2a-protocol/src/a2a_protocol/lifecycle.py` | NEW |
| 4 | `a2a-protocol/src/a2a_protocol/sse.py` | NEW |
| 4 | `a2a-protocol/src/a2a_protocol/event_bus.py` | NEW |
| 5 | `a2a-protocol/src/a2a_protocol/message_history.py` | NEW |
| client | `a2a-protocol/src/a2a_protocol/client.py` | NEW (generic A2A client — JSON-RPC + SSE) |
| 1+ | `iran-monitor-api/src/iran_monitor_api/backend.py` | NEW (`IranMonitorBackend`) |
| 1 | `iran-monitor-api/src/iran_monitor_api/main.py` | MODIFY (compose app from protocol package) |
| 3 | `iran-monitor-api/src/iran_monitor_api/models.py` | MODIFY (Status enum extensions) |
| 4, 5 | `iran-monitor-api/src/iran_monitor_api/db.py` | MODIFY (additive schema: task_events, task_messages) |
| 4, 5 | `iran-monitor-api/src/iran_monitor_api/worker.py` | MODIFY (publish events; call clarifier) |
| 5 | `iran-monitor-api/src/iran_monitor_api/scenario_clarifier.py` | NEW |
| 5 | `iran-monitor-api/src/iran_monitor_api/orchestrator.py` | MODIFY (multi-turn context) |
| docs | `ONBOARDING.md`, `landing/index.html`, `DEPLOY.md` | MODIFY |
| sdk | `client/iran_monitor_client.py` | MODIFY |
| docs | `a2a-protocol/README.md`, `a2a-protocol/docs/EXAMPLE-GTA-BACKEND.md` | NEW |
| tests | `tests/test_agent_card.py`, `test_jsonrpc.py`, `test_sse.py`, `test_clarifier.py`, `test_multi_turn.py`, `test_lifecycle.py`, `test_backend_contract.py` (in both packages) | NEW |

## Reuse map (existing code)

| Existing function | Reused via | Why |
|---|---|---|
| `orchestrator.run_assess` | `IranMonitorBackend.submit_task / continue_task` | Business logic is protocol-agnostic. JSON-RPC translates the envelope; orchestrator does the work. |
| `briefing_writer.write_briefing` | Layer 4 (SSE artifact-update event) | The briefing IS the artifact. Stream it as completion event. |
| `subagent.invoke_perspective` + prompt-builder pattern | `scenario_clarifier.py` reuses the same pattern | One more `claude -p` invocation with a different prompt. Same isolation. |
| `db.enqueue_query`, `db.claim_next_query`, `db.complete_query` | Layers 2, 3, 5 (via backend) | Queue + state machine survive untouched. New transitions add to the existing graph. |
| `db.mark_perspective_completed` | Layer 4 (publish on perspective completion) | Hook the SSE publish in here so per-perspective progress is reported. |
| `signing.sign_audit_record` | Layer 2 (A2A artifacts can carry signatures) | Reuse the Ed25519 path. |
| `api.auth.require_api_key` | Bearer-on-JSON-RPC via `IranMonitorBackend.authenticate` | Same header, same key store. |
| `api.rate_limit.check_and_record` | Backend layer | Same rate-limit semantics on the JSON-RPC route. |
| `email_delivery.send_completion_email` | Layer 5 | If buyer set `deliver_to` AND task hit `input-required`, email them the question. |

## Out of scope

- Push notifications (webhook callbacks for state changes) — `capabilities.pushNotifications: false` on the agent card; defer to Phase 2.
- Token-level streaming inside perspective agent reasoning — blocked by `claude -p` output mode; revisit when Claude SDK exposes streaming. Event-level streaming is what ships.
- gRPC binding — JSON-RPC over HTTPS covers the vast majority of clients. Defer.
- Agent card discovery via DNS / registry — wait for the ecosystem to settle.
- A2A "skill-based routing" (where a buyer's agent calls `getCapabilities` to plan multi-skill calls) — defer; single skill is enough.
- Actually building the GTA-a2a service — out of scope here. The plan delivers the **pattern** + an `EXAMPLE-GTA-BACKEND.md` sketch. The CEO commissions the GTA build separately once the pattern is validated.

## Verification

Order: unit tests pass first, then integration smoke, then external compliance, then **the generalization smoke**.

1. **Unit tests** — `uv run pytest` in both packages. Target: 65 existing in iran-monitor-api + ~45 new = ~110 green.
   - L1: AgentBackend Protocol shape, agent card schema, capabilities flags, skills listing
   - L2: JSON-RPC envelope parsing, method dispatch, error mapping, Bearer auth on RPC route, rate limit
   - L3: each new state appears in TaskState, transition graph correctness, REST + JSON-RPC see different state labels appropriately
   - L4: SSE event emission per state change, heartbeat, resubscribe replay from task_events
   - L5: clarifier identifies missing horizon / actor / capability; multi-turn message history persists; 3-round-trip cap; REST path skips clarifier
   - **Backend contract** test: a `MockBackend` implementing `AgentBackend` runs all the protocol-package tests without any Iran-monitor imports. This is the test that proves the protocol package is generic.

2. **Local end-to-end smoke** — `uv run iran-monitor-api` + `uv run iran-monitor-worker`:
   - `curl https://localhost:8080/.well-known/agent-card.json` returns valid agent card
   - `curl -X POST localhost:8080/v1/jsonrpc -d '{"jsonrpc":"2.0","method":"message/send",...,"id":1}'` returns a task
   - `curl -N -X POST localhost:8080/v1/jsonrpc -d '{"jsonrpc":"2.0","method":"message/stream",...}'` streams SSE events
   - Submit a vague scenario; receive `input-required`; send follow-up `message/send` with missing field; task completes

3. **External A2A compliance** — point Google's reference A2A client / inspector (from <https://github.com/a2aproject/A2A>) at our endpoint and complete one round-trip. **Binding evidence** that we're A2A-compliant, not A2A-shaped.

4. **Existing-behavior regression**:
   - Re-run `spike/run-spike.py` to confirm orchestrator hasn't regressed.
   - Re-run advisory-round QA on the spike output.
   - REST endpoints still pass their 65 existing tests.

5. **Manual third-party validation** — paste agent-card URL into a LangChain A2A integration / Spring AI A2A / IBM watsonx orchestrate; confirm discovery + task submission works without us shipping client-specific code.

6. **Generalization smoke (the experiment's verdict)** — implement a 1-skill `MockGTABackend` that just echoes the input as a fake "trade-policy lookup", wire it into the protocol package, point the server at `localhost:8081`, run the full A2A inspector test against it. If it passes without ANY changes to `a2a-protocol/`, the pattern is reusable. If it requires patches, the abstraction leaked and the plan needs to come back for refactoring before declaring the experiment a success.

## Estimate

- Package scaffold + Layer 1 (agent card + AgentBackend Protocol): 1 day
- Layer 2 (JSON-RPC dispatcher + A2A models + Iran backend wiring): 2 days
- Layer 3 (lifecycle states): ½ day
- Layer 4 (SSE streaming + task_events): 1.5 days
- Layer 5 (multi-turn clarifier + message history): 2.5 days
- Docs + landing + SDK + ONBOARDING + EXAMPLE-GTA-BACKEND.md: 1 day
- Tests across both packages (~45 new): 1 day
- Generalization smoke (MockGTABackend + verify pattern transfers): ½ day
- Buffer (A2A inspector debugging, spec edge cases): 1 day

**Total: ~11 working days** (~2¼ weeks with one engineer, no parallelism). Each layer is independently shippable.

## Risk register

| Risk | Probability | Mitigation |
|---|---|---|
| Abstraction leaks — protocol package ends up depending on Iran-monitor types | High if not enforced | Lint rule + the `MockGTABackend` smoke (step 6 of verification). Forces the boundary to be real. |
| A2A spec evolves before we ship | Medium | Pin to a specific spec version on the agent card; re-validate before pilot launch. |
| SSE breaks behind Cloudflare / corporate proxies | Medium | Caddy disables buffering on `text/event-stream` (standard); fall back to polling for clients that can't SSE. |
| Multi-turn clarifier loops badly | Medium | Cap at 3 round-trips; persist full message history so clarifier sees prior context. Adversarial test scenarios. |
| `claude -p` doesn't expose mid-task progress | Confirmed | Document on agent card: `streamingGranularity: "event"`, not token-level. |
| Buyer pilot promised REST and now has to migrate | Low | REST endpoints stay live as back-compat transport. ONBOARDING.md keeps REST section; adds A2A above it. |
| External A2A clients don't actually adopt yet | Low (downgraded after May 2026 research — 150+ production orgs; financial-services RFPs already require A2A) | Build it anyway. Brand + buyer-RFP alignment + generalization payoff justify even at modest external adoption. |
| Generalization payoff doesn't materialise — GTA backend needs significant protocol changes anyway | Medium | The `MockGTABackend` smoke catches this early. If the experiment fails, we still have a working Iran-monitor A2A service; we just don't get the leverage we hoped for. |
| Protocol losing battle in 12-24 months to AGNTCY or proprietary alternative | Low | AgentBackend abstraction is the hedge — switching cost ~$20K–$50K vs. $70K–$240K without it. Re-evaluate annually against the "what would change the verdict" triggers above. |
| Claude Managed Agents gains native A2A orchestration → our adapter becomes redundant | Low/Medium | Net positive if it happens — we can deprecate adapter layer and call CMA-native A2A directly. AgentBackend interface insulates the protocol details either way. |

## What this experiment is *really* testing

Three questions, ranked:

1. **Is the A2A protocol stable + usable enough that a real SGEPT asset can ship A2A-compliant in ~2 weeks?** (Tests SGEPT's bet on the ecosystem.)
2. **Can the protocol layer be authored once and reused across multiple SGEPT assets?** (Tests the generalization design — the `AgentBackend` abstraction.)
3. **Do A2A-native buyers / agents actually discover and use our service?** (Tests whether the ecosystem positioning matters commercially — this is a 90-day question, not a 2-week question.)

Q1 + Q2 are answered by the end of this build. Q3 is answered later by adoption metrics on `a2a.globaltradealert.org`.
