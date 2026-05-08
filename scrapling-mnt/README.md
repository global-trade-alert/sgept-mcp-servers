# scrapling-mnt

Stealth web scraping MCP server for Sancho Claudito (GTA + DPA author bot) and any other agent that needs reliable URL → markdown conversion.

Backed by [Scrapling](https://github.com/D4Vinci/Scrapling): cascading httpx → Camoufox (Firefox stealth) → Chromium fallback, with a PDF branch (pypdf → Gemini OCR fallback).

## Why

`cc-os/scripts/fetch-source.py` already covers static + Playwright + OCR, but Sancho Claudito hits operational blockers on:

- EU Commission Decision PDFs (JS SPA)
- Pakistani prior regulations (anti-bot)
- Korean / Chinese government portals (HTTP/2, locale)
- Paywalled news (Reuters, FT — for motive-quote extraction)
- Cloudflare-protected pages

Scrapling's `StealthyFetcher` (Camoufox-based) handles TLS-fingerprint and browser-fingerprint anti-bot defences that vanilla Playwright cannot.

## Tools

| Tool | Purpose |
|---|---|
| `scrape_url` | Single URL with auto cascade (static → stealth → pdf branch) |
| `scrape_pdf` | Explicit PDF path (pypdf, Gemini OCR fallback) |
| `scrape_batch` | Multi-URL harvest, server-clamped concurrency |
| `scrape_status` | Health snapshot |

## Install

```bash
cd jf-dev/sgept-dev/sgept-mcp-servers/scrapling-mnt
uv venv && source .venv/bin/activate
uv pip install -e .
python -m camoufox fetch     # downloads Camoufox Firefox build (~500MB)
```

Verify:

```bash
python -m scrapling_mnt.cli status
python -m scrapling_mnt.cli scrape-url https://www.example.com
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
      "args": ["-m", "scrapling_mnt"]
    },
    "scrapling-metis": {
      "command": "ssh",
      "args": ["deploy@204.168.141.21",
               "/home/deploy/scrapling-mnt/.venv/bin/python",
               "-m", "scrapling_mnt"]
    }
  }
}
```

Use `mcp__scrapling__scrape_url` for local fetches; `mcp__scrapling-metis__scrape_url` to offload to Metis.

## Configuration (env vars)

| Var | Default | Purpose |
|---|---|---|
| `SCRAPLING_BROWSER_MAX` | `1` | Max concurrent browser instances. Keep 1 on Metis (8GB). |
| `SCRAPLING_CACHE_DIR` | `~/.cache/scrapling-mnt` | Disk cache root |
| `SCRAPLING_CACHE_TTL_DAYS` | `30` | Cache freshness |
| `SCRAPLING_ALLOW_DOMAINS` | unset | Optional allowlist: `gov.uk,*.gov.au,regex:^.*\\.gov$`. If set, only matching hosts are fetched. |
| `GEMINI_API_KEY` | — | Required for OCR fallback on scanned PDFs |

## Safety

- **SSRF defence:** non-http(s) schemes, loopback, RFC1918, link-local, cloud metadata endpoints all rejected. DNS resolution is checked.
- **Concurrency:** server-side semaphore caps simultaneous browser fetches (default 1).
- **Memory cap:** deploy-time `ulimit -v` recommended to prevent OOM (see deployment docs).
- **No sensitive secrets in URLs:** the cache stores fetched bodies; do not pass URLs containing tokens you would not want on disk.

## Status

v0.1.0 — initial release.
