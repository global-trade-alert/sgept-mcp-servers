# iran-monitor-client

Minimal Python SDK for the Iran Monitor Inference API.

```bash
pip install httpx pynacl
# Copy iran_monitor_client.py into your project (or vendor it from the repo)
```

## Quick start

```python
from iran_monitor_client import Client

client = Client(
    api_key="your-pilot-key",
    base_url="https://a2a.globaltradealert.org",
)

# Submit
query = client.submit(
    scenario="Iran launches a cyber attack on German critical infrastructure within 30 days...",
    horizon="30d",
    tier="premium",
    deliver_to="risk-desk@your-fund.com",  # optional
)

# Wait (polls every 30s; ~25 min Premium)
result = client.wait(query.query_id, timeout_seconds=3600)

print(f"P = {result.p_point:.3f}")
print(result.briefing_markdown)

assert client.verify_audit(result), "audit signature failed verification"
```

## What you get back

- `result.p_point` / `result.p_interval` — aggregated probability
- `result.divergence_flag` — true if max-min spread > 15pp
- `result.perspectives[]` — per-framework reasoning + p_point
- `result.major_disagreements[]` — structured disagreement narratives
- `result.high_elasticity_events[]` — events that would shift P materially
- `result.briefing_markdown` — full human-readable briefing
- `result.audit_record` + `result.audit_signature` — Ed25519-signed envelope

The signature covers the audit record bytes after canonical JSON
serialization. Verify locally with `client.verify_audit(result)` before
relying on the number.
