# iran-monitor-api

Queryable inference API for the Iran Conflict Scenario Monitor. Async novel-scenario assessment with reasoning trace and signed audit records.

**Status:** Phase 1 (wedge). See design doc at `~/.gstack/projects/johannesfritz-jf-metis/johannesfritz-main-design-iran-monitor-api-*.md` for full architecture, premises, and rationale.

## What it does

Risk desks POST a scenario description; the perspective stack (14 agents grounded in conflict theory, forecasting science, and intelligence tradecraft) runs against the latest verified intelligence base; a structured assessment with reasoning trace is returned by polling within 30–60 minutes.

Two tiers:
- **Standard** — binds to the latest cron-sealed intelligence base hash. Cheaper, faster.
- **Premium** — runs a scenario-targeted live GATHER pass (bounded web search + source verification) before ASSESS. Slower, more current.

Both share an identical ASSESS pipeline with independence enforcement.

## Architecture (Phase 1)

```
┌─────────┐    POST /v1/queries      ┌──────────┐
│ Buyer   ├───────────────────────────►          │
│ agent / │                          │ FastAPI  │   ┌──────────┐
│ analyst │    GET /v1/queries/{id}  │ + auth   ├──►│ SQLite   │
└─────────┘◄────────────────────────┤+ rate-lim│   │ queue +  │
                                     └────┬─────┘   │ outputs  │
                                          │         └────┬─────┘
                                          ▼              │
                                     ┌──────────┐        │
                                     │ Worker   ◄────────┘
                                     │ (single, │
                                     │ async)   │
                                     └────┬─────┘
                                          │
                                          ▼
                            ┌───────────────────────────────┐
                            │ Premium GATHER (optional)     │
                            │ ↓                             │
                            │ Tetlock cold-start prior      │
                            │ ↓                             │
                            │ Perspective subagents × N     │
                            │ (claude -p, isolated)         │
                            │ ↓                             │
                            │ Aggregate + divergence flag   │
                            │ ↓                             │
                            │ Sign audit record (Ed25519)   │
                            └───────────────────────────────┘
```

## Develop

```bash
cd iran-monitor-api
uv sync
uv run pytest

# Generate signing key (first time)
uv run iran-monitor-generate-key

# Run dev server
uv run iran-monitor-api  # HTTP on :8080
uv run iran-monitor-worker  # background worker
```

## Deploy on Metis

- Systemd unit at `systemd/iran-monitor-api.service` (HTTP + worker in one process).
- Caddy reverse-proxy on `a2a.globaltradealert.org`.
- API keys + signing key in SOPS-encrypted env.
- Seal intel-base hash from the cron's Phase 6 (COMMIT) via `iran-monitor-seal-intel-base`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v1/queries` | Submit scenario; returns 202 + query_id |
| `GET` | `/v1/queries/{id}` | Poll status; returns result + signed audit when complete |
| `GET` | `/.well-known/iran-monitor-signing-key.pub` | Public Ed25519 key for audit-record verification |
| `GET` | `/healthz` | Liveness |

## Out of scope (Phase 1)

MCP stdio wrapper, webhooks, programmable thresholds, web chat UI, full procurement pack, Postgres, worker pool, Cloudflare WAF, programmatic sanctions screening, counterfactuals, multi-conflict, free read-only tier. See Phase 1 vs Phase 2 split in the design doc.
