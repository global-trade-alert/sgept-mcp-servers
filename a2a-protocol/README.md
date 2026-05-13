# a2a-protocol

Reusable Python implementation of Google's [A2A (Agent-to-Agent) protocol](https://a2a-protocol.org/latest/specification/) — agent card publication, JSON-RPC 2.0 task dispatch, SSE event streaming, the 8-state task lifecycle, and multi-turn `input-required` clarification machinery.

**Backend-agnostic.** Implement the `AgentBackend` Protocol with your domain logic; this package provides the protocol surface. First consumer is `iran-monitor-api`; designed to be transferable to GTA, DPA, and any future SGEPT analytic asset that needs an A2A endpoint.

## Why a sibling package

Iran-monitor's business logic (perspective stack, intelligence base, briefing writer) is unrelated to A2A. Likewise the future GTA backend will have its own logic. The A2A protocol layer (cards, JSON-RPC envelopes, SSE plumbing, lifecycle state machine) is shared. Isolating it here means:

1. New A2A-enabled assets land in days, not weeks.
2. Protocol upgrades (A2A spec evolves) propagate to all consumers in one place.
3. A clean abstraction line — if the protocol landscape shifts (AGNTCY captures finance RFPs, etc.), only this package needs to migrate; consumer backends stay put.

## How to wrap a new asset in A2A

```python
from a2a_protocol import AgentBackend, AgentCard, create_app

class MyAssetBackend:
    agent_card = AgentCard(
        name="my-asset",
        description="...",
        url="https://my-asset.example.com",
        skills=[...],
        capabilities=...,
    )

    async def submit_task(self, message, task_id, context): ...
    async def continue_task(self, task_id, message, history): ...
    async def cancel_task(self, task_id): ...
    async def get_task(self, task_id): ...
    async def stream_events(self, task_id): ...
    def authenticate(self, token): ...

app = create_app(MyAssetBackend())
```

Run with uvicorn. Caddy in front for TLS. That's the surface.

## Status

Phase 1 build (alongside iran-monitor-api Phase 1.5). Layers ship incrementally:

- [ ] Layer 1: AgentBackend Protocol + AgentCard + A2A model classes + FastAPI app factory
- [ ] Layer 2: JSON-RPC 2.0 dispatcher + Bearer auth + error mapping
- [ ] Layer 3: 8-state lifecycle + transition validator
- [ ] Layer 4: SSE streaming + event bus + crash-safe resubscribe
- [ ] Layer 5: Multi-turn `input-required` + generic message history

See `docs/EXAMPLE-GTA-BACKEND.md` for the transferability sketch.
