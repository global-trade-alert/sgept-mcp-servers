# Example: A2A-enabling the GTA database

Sketch of what a future `gta-a2a` service looks like once this experiment is validated. **Not implementation — just signatures + decisions.** Confirms the protocol package transfers cleanly to a fundamentally different domain.

## What buyers would query

The Global Trade Alert database tracks 80,000+ government interventions in international trade since 2008 — tariffs, export bans, subsidies, sanctions, etc. The natural agent-to-agent queries against GTA:

- "List all Chinese export-restriction measures targeting semiconductors enacted in the last 90 days."
- "Show interventions by Vietnam that affect EU-bound textile exports."
- "Has there been a measure I should know about given my exposure to {sector, country}?"

These map to skills like `query_measures`, `summarize_measures`, `assess_exposure` — the GTA equivalent of Iran-monitor's `assess_scenario`.

## What the backend would look like

```python
# gta-a2a/src/gta_a2a/backend.py
from a2a_protocol import (
    AgentBackend, AgentCard, AgentCapabilities, AgentSkill,
    AgentAuthentication, AuthContext, Message, Task, TaskContext,
    TaskHandle, TaskID, TaskState, TaskStatus,
)
from a2a_protocol.event_bus import EventBus

class GTABackend:
    def __init__(self, db_client, query_engine):
        self._db = db_client                    # existing GTA database connection
        self._query = query_engine              # existing GTA query/summarization stack
        self._bus = EventBus()
        self._card = AgentCard(
            name="gta",
            description=(
                "Queryable access to the Global Trade Alert database — every "
                "government intervention in international trade since 2008. "
                "Submit natural-language queries about measures, jurisdictions, "
                "sectors, products, or HS codes. Returns structured intervention "
                "records, summaries, and exposure assessments."
            ),
            url="https://a2a-gta.globaltradealert.org",
            version="0.1.0",
            capabilities=AgentCapabilities(streaming=True, streaming_granularity="event"),
            authentication=AgentAuthentication(schemes=["bearer"]),
            skills=[
                AgentSkill(
                    id="query_measures",
                    name="Query interventions",
                    description="Natural-language query over the GTA database. Filters by jurisdiction, sector, time, product, instrument.",
                    examples=["Chinese export restrictions on semiconductors in last 90d"],
                ),
                AgentSkill(
                    id="summarize_measures",
                    name="Summarize a set of measures",
                    description="Returns a structured summary + briefing for a set of interventions identified by query or explicit IDs.",
                    examples=["Summarize Vietnam's textile policies affecting EU exports"],
                ),
                AgentSkill(
                    id="assess_exposure",
                    name="Exposure assessment",
                    description="Given a buyer-stated exposure (sector + country + counterparty list), returns relevant GTA interventions + risk briefing.",
                ),
            ],
        )

    @property
    def agent_card(self) -> AgentCard: return self._card

    def authenticate(self, token: str) -> AuthContext | None:
        # GTA already has an API-key system; reuse it.
        return self._gta_api_keys.lookup(token)

    async def submit_task(self, message: Message, task_id: TaskID, ctx: TaskContext) -> TaskHandle:
        # Parse skill + params from the Message's data parts.
        params = message.data()
        skill = params.get("skill", "query_measures")
        # Enqueue work in GTA's existing async query engine.
        await self._query.enqueue(task_id=task_id, skill=skill, params=params)
        return TaskHandle(task=Task(id=task_id, context_id=ctx.context_id,
                                    status=TaskStatus(state=TaskState.SUBMITTED)))

    async def continue_task(self, task_id, message, history) -> TaskHandle: ...
    async def cancel_task(self, task_id) -> Task: ...
    async def get_task(self, task_id) -> Task | None: ...
    async def stream_events(self, task_id):
        async for ev in self._bus.subscribe(task_id):
            yield ev
```

## Multi-turn for GTA

The Iran-monitor clarifier checks for horizon + actor + capability. A GTA clarifier would check for different fields:

- **Jurisdiction** (countries/regions/blocs) — required
- **Time window** — required
- **Either sector OR HS code** — required (without one of these, the query returns 80,000 results)
- **Instrument type** (tariff, ban, subsidy, etc.) — optional but if omitted, query may need to chunk results

If any required field is missing, the backend transitions to `input-required` exactly as Iran-monitor does. The reusable Layer-5 machinery (message history, 3-round-trip cap, SSE clarification event) carries over without changes.

## What gets reused unchanged

From `a2a_protocol/`:
- `create_app(GTABackend())` — produces the FastAPI app
- `/.well-known/agent-card.json` — the GTA card is served correctly by `build_card_router`
- `POST /v1/jsonrpc` — the dispatcher handles `message/send`, `tasks/get`, `tasks/cancel` against GTABackend
- `POST /v1/jsonrpc/stream` — SSE streaming
- `EventBus` — per-task pub/sub
- `lifecycle.py` — the 8-state machine + transition validator
- `models.py` — A2A Task/Message/Part/Artifact
- `errors.py` — JSON-RPC error mapping
- `auth.py` — Bearer auth wiring (GTABackend provides the actual key check)
- `client.py` — generic A2AClient

From `iran-monitor-api/`:
- **Zero.** GTA's backend does not import anything from `iran_monitor_api`.

## Estimated effort

Based on the Iran-monitor build:

- GTABackend.{submit, continue, cancel, get_task, stream_events}: ~1.5 days (mostly bridging to GTA's existing query engine)
- GTA-specific clarifier (different missing-field checks than Iran-monitor): ~1 day
- Agent card with skill definitions + examples: ~½ day
- Deployment (Caddy + DNS + SOPS env + systemd): ~½ day
- Tests against GTABackend (mirroring the Iran-monitor test_backend.py): ~½ day

**Total: ~4 days** — versus ~11 days for Iran-monitor (which had to build the protocol package itself). The leverage from the abstraction is roughly 3×, validating the experiment.

## What the experiment would prove

If `gta-a2a` ships in ~4 days using the protocol package without modifications, the answer to the CEO's question — "what does it take to A2A-enable our main databases?" — is:

> ~½ a working week per asset, once the protocol package exists. Most of the work is bridging to the asset's existing query engine + writing a domain-specific clarifier + an agent card. The protocol itself is solved.

That's the deliverable the CEO is funding the Iran-monitor experiment to learn.
