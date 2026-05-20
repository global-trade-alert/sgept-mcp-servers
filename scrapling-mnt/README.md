# scrapling-mnt

Thin MCP client over **bastiat-api** `/scrape_urls/`. Every agent host that registers this MCP server gets URL → markdown conversion without hosting a browser locally — the Scrapling cascade (Tier 1 static → DynamicFetcher → Camoufox stealth), the filesystem cache, the SSRF gate, the SPA-PDF interceptor, and the Gemini OCR fallback all live on the shared bastiat server.

## Why thin?

Until v0.1, every agent that loaded `scrapling` paid the cost of a local Camoufox install plus ~500MB of browser binaries plus per-call browser startup time. The bastiat-scraper-edge-cases PRD shipped every capability this package needed into bastiat-api proper, so v0.2 drops the heavy stack and proxies straight to it.

Compute moves from N agent hosts to one shared bastiat server. The MCP tool name stays `scrapling`, so existing `.mcp.json` registrations keep working.

## Tools

| Tool | Purpose |
|---|---|
| `scrape_url` | Single URL, returns FetchResult dict |
| `scrape_batch` | Multi-URL batch (≤50) in one bastiat request |

`scrape_pdf` and `scrape_status` were removed in v0.2. Migrate callers:

```python
# before
scrape_pdf(url="https://example.com/doc.pdf")
# after
scrape_url(url="https://example.com/doc.pdf", strategy="pdf")
```

No `scrape_status`-equivalent is exposed — a thin HTTP client has no meaningful health probe distinct from "the bastiat server is up".

## FetchResult shape

Both tools return dicts shaped like the legacy v0.1 result, so any caller still reading by dict-key keeps working:

```python
{
    "url": "https://example.com",
    "content": "...",
    "status": 200,
    "strategy_used": "static",        # static | js | stealth | pdf | ocr | cache
    "content_type": "text/html; charset=utf-8",
    "fetched_at": 1747663200.0,
    "from_cache": False,
    "error": None,
}
```

`scrape_batch` wraps the per-URL dicts in `{results, total, successes, failures}`.

## Install

```bash
cd sgept-mcp-servers/scrapling-mnt
uv venv && source .venv/bin/activate
uv pip install -e .
```

No Camoufox, no Chromium, no model weights — just `httpx`, `pydantic`, `mcp`.

Verify:

```bash
GTA_API_KEY=... python -m scrapling_mnt.cli scrape-url https://www.example.com
```

## Run as MCP server

```bash
python -m scrapling_mnt
```

Workspaces declare in `.mcp.json`:

```json
{
  "mcpServers": {
    "scrapling": {
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "scrapling_mnt"],
      "env": {
        "GTA_API_KEY": "...",
        "BASTIAT_BASE_URL": "https://bastiat-api.globaltradealert.org"
      }
    }
  }
}
```

## Configuration (env vars)

| Var | Default | Purpose |
|---|---|---|
| `GTA_API_KEY` | — (required) | APIKey-auth header for bastiat-api |
| `BASTIAT_BASE_URL` | `https://bastiat-api.globaltradealert.org` | Override for local dev (`https://bastiat-api.gta.local`) or staging |
| `BASTIAT_PROFILE` | `mcp_thorough` | Named profile from bastiat's `scrape_profile.py` (also `bastiat_batch_fast`, `bastiat_batch_thorough`) |
| `BASTIAT_MAX_WAIT_S` | `600` | Client-side poll budget (input default; per-call `max_wait_s` overrides) |
| `BASTIAT_VERIFY_TLS` | `true` | Set to `false` only for local dev against a self-signed cert (e.g. `bastiat-api.gta.local`). |

`timeout` (per-request budget) and `max_wait_s` (poll budget) are split:

- `timeout` is forwarded to bastiat as `options_override.max_seconds_per_url`. Bounds the time bastiat spends on any one URL inside the task.
- `max_wait_s` is the client-side patience window — how long we keep polling `/ric_task_status/<id>/` before giving up. Should usually be larger than `timeout * len(urls)`.

## Safety

SSRF defence, allowlist enforcement, cache TTL, and OCR rate-limiting are all bastiat-api concerns now. See `bastiat-api`'s `url_safety.py` and `scrape_profile.py`.

## Status

v0.2.0 — internal rewrite. Public surface (`scrape_url`, `scrape_batch`) is API-compatible with v0.1; `scrape_pdf` and `scrape_status` removed.
