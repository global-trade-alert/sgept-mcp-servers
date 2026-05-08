"""Scrapling MCP Server - Stealth web scraping for Sancho Claudito.

Exposes a small MCP tool surface (scrape_url, scrape_pdf, scrape_batch,
scrape_status) backed by Scrapling's Fetcher / StealthyFetcher cascade with a
PDF branch and Gemini OCR fallback. Concurrency-clamped (1 browser at a time)
and SSRF-guarded by URL allowlist.
"""

__version__ = "0.1.0"
