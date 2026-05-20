"""Scrapling MCP Server — thin client to bastiat-api `/scrape_urls/`.

Exposes `scrape_url` and `scrape_batch` MCP tools that forward requests to
the bastiat-api scraper endpoint (tiered fetcher, SSRF gate, cache, SPA-PDF
interception, Gemini OCR fallback all live there).
"""

__version__ = "0.2.0"
