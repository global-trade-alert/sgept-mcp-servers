# Iran Monitor Inference API — Pilot Onboarding

You've been granted pilot access to the Iran Monitor Inference API. This document is everything you need to integrate.

## A2A protocol surface

The service is A2A-spec-compliant. Buyers running A2A-native agents (Claude, LangChain A2A integration, Spring AI, IBM watsonx, etc.) can discover the agent automatically:

```
GET https://a2a.globaltradealert.org/.well-known/agent-card.json
```

This returns the [A2A Agent Card](https://a2a-protocol.org/latest/specification/#agent-card) declaring our single skill (`assess_scenario`), capabilities (streaming = yes, push notifications = no), authentication scheme (Bearer), and example queries.

For A2A-native integration, point your client at `https://a2a.globaltradealert.org`. The REST surface below remains available as a back-compat transport.

Sample JSON-RPC envelope:

```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{
        "kind": "data",
        "data": {
          "scenario": "Iran launches a meaningfully disruptive cyber attack on German critical infrastructure within 30 days, with German government public attribution.",
          "horizon": "30d",
          "tier": "premium"
        }
      }]
    }
  },
  "id": "<your request id>"
}
```

POST that to `https://a2a.globaltradealert.org/v1/jsonrpc` with `Authorization: Bearer <your-key>`. The response is an A2A `Task` object.

For streaming (`message/stream`) — POST to `https://a2a.globaltradealert.org/v1/jsonrpc/stream` and consume Server-Sent Events. Each event is a `TaskStatusUpdateEvent` or `TaskArtifactUpdateEvent` per the A2A spec.

**Multi-turn:** if you submit an underspecified scenario (e.g. missing time horizon or actor), the task transitions to `input-required` and the SSE stream emits a clarification question from the agent. Reply with another `message/send` carrying the same `taskId` to continue. Up to 3 round-trips per task.

## What this is

A queryable inference layer over the Iran Monitor's perspective stack — 14 agents grounded in conflict theory, forecasting science, and intelligence tradecraft. Submit a novel scenario; get back a probability + reasoning trace + signed audit record drawn from the same verified intelligence base the cron-driven canonical-8 report uses.

Two tiers, same perspective stack and same independence safeguards, different freshness of evidence:

- **Standard** — perspective agents read from the standing intelligence base assembled by the monitor's 6-hourly cron (canonical sources, peripheral-signal watch list, cross-cycle reasoning history). No fresh web search per query. Faster (p50 ~8 min), cheaper. Evidence is at most ~6 hours old.
- **Premium** — before the perspective agents reason about your scenario, the system runs a focused web search keyed off the specific terms in your scenario (e.g. a "cyber attack on Germany" query triggers searches like "IRGC cyber unit Germany", "BfV Iran attribution 2026", "Iran cyber operations EU targets"). Up to 20 queries and 60 page fetches; each result is verified (source URL resolvable, publication date present) and appended to the standing intelligence base for this query only. The agents then assess against the freshest available evidence. Slower (p50 ~25 min, p99 ≤60 min). Only Premium produces the `briefing_markdown` + `major_disagreements` + `high_elasticity_events` synthesis fields.

## Your credentials

| | |
|---|---|
| **Base URL** | `https://a2a.globaltradealert.org` |
| **API key** | _delivered out-of-band (encrypted attachment / 1Password vault link)_ |
| **Verify key** | `https://a2a.globaltradealert.org/.well-known/iran-monitor-signing-key.pub` |
| **Status** | `https://a2a.globaltradealert.org/healthz` |

Authentication is HTTP Bearer:

```
Authorization: Bearer <YOUR_KEY>
```

Rotate keys quarterly; ping the operations contact for a rotation window.

## Three integration patterns

Pick whichever fits your infrastructure. All three hit the same REST surface.

### 1. Curl (eval / debug)

```bash
KEY="your-pilot-key"
BASE="https://a2a.globaltradealert.org"

# Submit
QID=$(curl -s -X POST $BASE/v1/queries \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "Iran launches a meaningfully disruptive cyber attack on German critical infrastructure (energy, water, or rail) attributable to Iran within the next 30 days.",
    "horizon": "30d",
    "tier": "premium"
  }' | jq -r .query_id)

echo "Query ID: $QID"

# Poll (~25 min for Premium)
while true; do
  STATE=$(curl -s -H "Authorization: Bearer $KEY" $BASE/v1/queries/$QID)
  echo "$STATE" | jq -r '.status'
  echo "$STATE" | jq -e '.status == "completed" or .status == "partial" or .status == "failed"' && break
  sleep 30
done

echo "$STATE" | jq .
```

### 2. Python SDK (backend integration)

Copy `client/iran_monitor_client.py` into your project (or pip install the
package when published).

```python
import os
from iran_monitor_client import Client

client = Client(api_key=os.environ["IRAN_MONITOR_API_KEY"])

query = client.submit(
    scenario="...",
    horizon="30d",
    tier="premium",
    deliver_to="desk@your-fund.com",  # optional — email on completion
)

result = client.wait(query.query_id, timeout_seconds=3600)

assert client.verify_audit(result), "audit signature failed"

print(f"P = {result.p_point:.3f} ({result.p_interval[0]:.3f}–{result.p_interval[1]:.3f})")
for d in result.major_disagreements:
    print(f"  Disagreement on '{d.topic}': spread {d.spread_pp:.1f}pp")
for ev in result.high_elasticity_events:
    print(f"  {ev.shift_direction.upper()} {ev.magnitude_pp}: {ev.event}")
```

### 3. LLM agent tool (agent-to-agent)

If your buyer-side workflow includes an LLM agent (Claude, GPT-5, etc.), register our API as a tool the agent can invoke. Example for the Anthropic tool-use API:

```python
tools = [{
    "name": "iran_monitor_assess_scenario",
    "description": (
        "Submit a novel geopolitical scenario about Iran or its proxies to "
        "the Iran Monitor Inference API. Returns a probability point estimate, "
        "uncertainty interval, per-framework reasoning, and a signed audit "
        "record drawn from a verified intelligence base updated every 6 hours."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "scenario": {
                "type": "string",
                "description": "Concrete scenario description (≤1500 chars)",
            },
            "horizon": {"enum": ["7d", "14d", "30d", "60d", "90d"]},
            "tier": {"enum": ["standard", "premium"]},
        },
        "required": ["scenario", "horizon", "tier"],
    },
}]
```

Your agent's tool runtime handles the POST + polling against `https://a2a.globaltradealert.org/v1/queries`.

## Delivery options

By default, the only delivery is polling — your client checks `GET /v1/queries/{id}` until it returns `completed`.

Set `deliver_to` on the request body to additionally get an HTML email with:

- The full `briefing_markdown` rendered to HTML in the body
- The complete JSON response + signed audit record as an attachment

Email is best-effort. A delivery failure does not affect polling availability.

Webhook delivery is on the Phase 2 roadmap — let us know if you'd like to be in the design conversation.

## Response shape

`GET /v1/queries/{id}` with `status: completed`:

```json
{
  "query_id": "uuid",
  "status": "completed",
  "partial": false,
  "result": {
    "p_point": 0.018,
    "p_interval": [0.015, 0.025],
    "divergence_flag": false,
    "consensus_summary": "Weighted-uniform average across 14 perspectives: P = 0.018 (range 0.013–0.025, spread 1.2pp). Within tolerance.",
    "perspectives": [
      {
        "name": "tetlock-forecaster",
        "p_point": 0.020,
        "p_interval": [0.015, 0.030],
        "key_reasoning": "Fermi decomposition yields...",
        "evidence_urls": [...],
        "divergence_from_consensus_pp": 0.2
      }
      // 13 more
    ],
    "major_disagreements": [
      {
        "topic": "Likelihood of German government public attribution",
        "spread_pp": 12.0,
        "high_side": ["red-team-adversarial"],
        "low_side": ["tetlock-forecaster", "wack-strategic"],
        "narrative": "Tetlock and Wack treat attribution as structurally near-impossible within 30d; Red-Team argues an aggressive ministry could attribute faster if domestic politics demand it."
      }
    ],
    "high_elasticity_events": [
      {
        "event": "Germany openly provides ISR or basing support to US forces",
        "shift_direction": "up",
        "magnitude_pp": "+8 to +12",
        "monitor": "Bundeswehr deployment announcements; Pistorius public statements"
      }
    ],
    "briefing_markdown": "# Scenario assessment — ...\\n\\n**Probability:** 1.8%..."
  },
  "audit_record": {
    "query_id": "uuid",
    "scenario_text": "...",
    "horizon_days": 30,
    "tier": "premium",
    "intelligence_base_hash": "sha256:...",
    "query_delta_hash": "sha256:... (premium only)",
    "perspectives_invoked": [...],
    "perspectives_completed": [...],
    "aggregation_method": "weighted_uniform_average_v1",
    "result_summary": {...},
    "evidence_urls": [...],
    "started_at_utc": "2026-05-12T18:00:00Z",
    "runtime_seconds": 1432,
    "version": "1.0"
  },
  "audit_signature": "base64-Ed25519"
}
```

## Verifying the signature

Every completed audit record is signed with our Ed25519 private key. The public verify key is published at `/.well-known/iran-monitor-signing-key.pub`. Verify locally before trusting the result:

**Python:**

```python
from nacl.signing import VerifyKey
from nacl.encoding import RawEncoder
import base64, json, requests

vk_bytes = requests.get("https://a2a.globaltradealert.org/.well-known/iran-monitor-signing-key.pub").content
vk = VerifyKey(vk_bytes, encoder=RawEncoder)

msg = json.dumps(response["audit_record"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
sig = base64.b64decode(response["audit_signature"])

vk.verify(msg, sig)  # raises BadSignatureError if tampered
```

**Bash (with `signify` or similar):** ask for the script.

If verification fails, the audit record has been tampered or the signing key has rotated. Check the [signing-key rotation page](https://a2a.globaltradealert.org/.well-known/iran-monitor-signing-key.versions.json) (when published) for current key versions.

## Rate limits

Per organisation, sliding window. Premium tier has higher entitlement because it's the higher-priced tier; both caps are admission limits, not throughput guarantees — the worker is single-concurrency in Phase 1, so a flood of submissions queues serially.

| Tier | Limit | 429 response |
|---|---|---|
| Standard | 10 / hour | with `Retry-After` header |
| Premium  | 30 / hour | with `Retry-After` header |

If you anticipate burst usage above these caps, ping the pilot contact 24h ahead for a temporary lift.

## Error taxonomy

| HTTP | Error code | Meaning |
|---|---|---|
| 400 | `malformed_input` | Bad JSON / out-of-range field |
| 401 | `missing_api_key` / `invalid_api_key` | Auth |
| 403 | `insufficient_tier` | Your key isn't tier-authorised |
| 404 | `query_not_found` | Unknown `query_id` (also returned cross-org for isolation) |
| 410 | `query_archived` | Beyond retention window |
| 429 | `rate_limited` | See Retry-After |
| 503 | `worker_down` / `quorum_failed` | Pipeline issue or fewer than ⌈2N/3⌉ perspectives succeeded |
| 504 | `query_timeout` | Hit the p99 ceiling |

Every error returns:

```json
{"error": "<code>", "message": "<human-readable>", ...extra}
```

## Out of scope for the pilot

- Synchronous chat surface (humans typing into a textarea)
- Webhook callbacks (polling + optional email only)
- Self-serve signup / Stripe billing
- Multi-conflict (the current intelligence base is Iran-focused — Ukraine, Taiwan, etc. would each need their own monitor)
- Counterfactual queries ("what if X had happened…")

If any of these matter for your use case, let us know — we're sequencing the Phase 2 roadmap against pilot feedback.

## Data handling

We retain:

- Scenario text + audit records: 24 months (auditability)
- Per-query intelligence deltas (the scenario-targeted web-search results from Premium queries): 90 days, then archived

We do not share your scenario text with third parties or use it for model training. A standalone data-handling note covering DPA-style obligations is available on request.

## Escalation

- **Pilot contact (product, methodology, commercial):** `johannes.fritz@sgept.org`
- **Technical lead:** `liubomyr.garvyliv@sgept.org`
