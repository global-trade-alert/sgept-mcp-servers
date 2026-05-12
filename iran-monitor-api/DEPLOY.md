# Iran Monitor API — Metis Deployment Checklist

Go-live checklist for production deployment on the Hetzner CPX32 VPS at `204.168.141.21`. Run these in order; each step is idempotent.

## Pre-flight (one-time, CEO actions)

- [ ] **DNS:** Add A records at the SGEPT DNS provider:
  - `api.iran-monitor.sgept.org` → `204.168.141.21`
  - `iran-monitor.sgept.org` → `204.168.141.21`
- [ ] **SMTP (optional but recommended):** Choose an SMTP provider for email delivery — Postmark, Resend, Mailgun, or the existing `metis@jfritz.xyz` IMAP/SMTP. Capture host + port + username + password.
- [ ] **Cloudflare (optional):** If routing through Cloudflare proxy, set the DNS records as proxied and ensure SSL/TLS mode is "Full (strict)". Caddy already handles Let's Encrypt origin certs.

## On Metis: install service

```bash
ssh deploy@204.168.141.21
cd ~/jf-private && ./scripts/pull-all.sh
cd jf-dev/sgept-dev/sgept-mcp-servers/iran-monitor-api
bash scripts/install-on-metis.sh
```

This runs `uv sync`, generates a signing key if missing, and provisions the env-file template at `~/.config/iran-monitor-api.env`.

## Configure env file

Edit `~/.config/iran-monitor-api.env` and replace:

- `IRAN_API_API_KEYS_JSON` — for the first deploy, use `{}` (empty). Use the `add-pilot-key.py` script (below) to mint keys.
- `IRAN_API_SMTP_HOST`, `IRAN_API_SMTP_PORT`, `IRAN_API_SMTP_USERNAME`, `IRAN_API_SMTP_PASSWORD`, `IRAN_API_SMTP_FROM` — if email delivery is enabled.
- `IRAN_API_IRAN_MONITOR_REPO=/home/deploy/jf-private/jf-thought/sgept-analytics/iran-monitor`

Recommended posture: put the env file under SOPS encryption. The existing `safeguard.sh` `source_env` helper supports both plaintext and `.env.enc` patterns — match the convention used by other Metis services.

## Mint the first pilot key

```bash
cd ~/jf-private/jf-dev/sgept-dev/sgept-mcp-servers/iran-monitor-api
uv run python scripts/add-pilot-key.py add <pilot-org-slug>
# → prints the new key. Capture it; deliver to the buyer out-of-band.

# Update the env file with the new IRAN_API_API_KEYS_JSON:
uv run python scripts/add-pilot-key.py export-env >> ~/.config/iran-monitor-api.env
# (Manually clean up duplicate lines; the export-env command always writes
#  IRAN_API_API_KEYS_JSON=... so older entries should be removed.)
```

## Caddy reverse-proxy

```bash
sudo mkdir -p /etc/caddy/Caddyfile.d
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile.d/iran-monitor.caddy
# Ensure /etc/caddy/Caddyfile includes the Caddyfile.d/ directory:
#   import /etc/caddy/Caddyfile.d/*.caddy
sudo systemctl reload caddy
sudo systemctl status caddy
```

Watch the Caddy log for the cert provisioning:

```bash
sudo journalctl -u caddy -f
# Look for: "obtain certificate finished" with the API + landing hostnames
```

## Start the API + worker

```bash
sudo systemctl enable --now iran-monitor-api iran-monitor-worker
sudo systemctl status iran-monitor-api iran-monitor-worker
```

Tail the logs:

```bash
sudo journalctl -u iran-monitor-api -f
sudo journalctl -u iran-monitor-worker -f
```

## Smoke test

From your local machine (NOT on Metis):

```bash
# Liveness
curl https://api.iran-monitor.sgept.org/healthz
# → "ok"

# Public verify key
curl -sI https://api.iran-monitor.sgept.org/.well-known/iran-monitor-signing-key.pub
# → 200 OK; Content-Type: application/octet-stream

# Auth check
curl -s https://api.iran-monitor.sgept.org/v1/queries -X POST \
  -H "Content-Type: application/json" -d '{"scenario":"x","horizon":"30d","tier":"standard"}'
# → 401 with error: missing_api_key

# Submit a real Standard query
KEY="imk-..."   # the minted pilot key
curl -s -X POST https://api.iran-monitor.sgept.org/v1/queries \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"scenario":"Iran formally announces resumption of uranium enrichment above 60% within 30 days","horizon":"30d","tier":"standard"}' \
| jq .
# → 202 with query_id

# Poll (Standard p50 ~8 min)
QID="..."
curl -s -H "Authorization: Bearer $KEY" https://api.iran-monitor.sgept.org/v1/queries/$QID | jq .status
```

## Hook the cron's Phase 6 to seal intel-base hash

The Standard tier binds to the intelligence base sealed at the end of each cron cycle. Edit `~/jf-private/jf-thought/sgept-analytics/iran-monitor/.claude/commands/update.md` (or wherever Phase 6 / COMMIT lives) to add a final step:

```bash
cd /home/deploy/jf-private/jf-dev/sgept-dev/sgept-mcp-servers/iran-monitor-api
uv run iran-monitor-seal-intel-base
```

Until this is wired, queries will see `intel_base_hash: "sha256:UNSEALED"` in the audit record. Worker still functions; auditability is reduced. Seal it before first paying use.

## Smoke the email path

If SMTP is configured:

```bash
curl -s -X POST https://api.iran-monitor.sgept.org/v1/queries \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"scenario":"...","horizon":"30d","tier":"premium","deliver_to":"johannes.fritz@sgept.org"}'
```

After the Premium query completes, check the inbox + the `delivery_status` column in `data/queries.sqlite`.

## Rollback

```bash
sudo systemctl stop iran-monitor-api iran-monitor-worker
sudo rm /etc/caddy/Caddyfile.d/iran-monitor.caddy
sudo systemctl reload caddy
```

API keys remain in the env file; nothing destructive. To re-enable later, restart the services.

## What good looks like after deploy

- `https://iran-monitor.sgept.org` loads the landing page over TLS.
- `https://api.iran-monitor.sgept.org/healthz` returns `ok`.
- `journalctl -u iran-monitor-api -f` shows `Uvicorn running on 127.0.0.1:8080`.
- `journalctl -u iran-monitor-worker -f` shows `worker started`.
- A pilot query submitted from outside Metis returns 202 immediately and completes within the latency SLO.
- The signed audit record verifies against the published public key.
- If `deliver_to` is set, the email arrives within ~1 minute of completion.

## Operational ongoing

- Quarterly: rotate API keys (`add-pilot-key.py revoke-org` + re-mint).
- Annually: rotate signing key (procedure: generate new key, publish new public key at `/.well-known/iran-monitor-signing-key.v{N}.pub`, keep old key valid for verification of historical records, document the rotation in `out-of-scope/` if any pilot raises questions).
- On every cron deploy / major iran-monitor pipeline change: re-run the spike (`spike/run-spike.py`) and the `/advisory-round` QA to confirm the perspective outputs remain framework-true.
