"""MCP server for scrapling-mnt — thin client to bastiat-api `/scrape_urls/`.

Exposes:
  scrape_url    — single URL, returns FetchResult dict
  scrape_batch  — multi-URL, returns {results, total, successes, failures}

Both tools delegate to `BastiatScraper`. Heavy lifting (cascade, cache,
PDF, OCR, SSRF gate) happens server-side in bastiat-api; this package is
process-local only for the MCP transport and the auth header.
"""

from __future__ import annotations

import os
from typing import List

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import BaseModel, ConfigDict, Field

from .bastiat_client import BastiatScraper


mcp = FastMCP("scrapling_mnt")


class _StrictInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )


class ScrapeUrlInput(_StrictInput):
    url: str = Field(description="URL to fetch (http or https only)")
    strategy: str = Field(
        default="auto",
        description="Fetch strategy: auto | static | stealth | js | pdf",
    )
    timeout: int = Field(
        default=30, ge=5, le=180,
        description="Per-request budget forwarded to bastiat as options_override.timeout",
    )
    max_wait_s: int = Field(
        default=600, ge=10, le=1800,
        description="Client-side poll budget — how long to wait for the bastiat task to finish",
    )


class ScrapeBatchInput(_StrictInput):
    urls: List[str] = Field(description="URLs to fetch", min_length=1, max_length=50)
    strategy: str = Field(default="auto")
    timeout: int = Field(default=30, ge=5, le=180)
    max_wait_s: int = Field(default=600, ge=10, le=1800)


def _build_scraper() -> BastiatScraper:
    api_key = os.environ.get("GTA_API_KEY")
    if not api_key:
        raise ToolError("GTA_API_KEY environment variable is required")
    return BastiatScraper(
        api_key=api_key,
        base_url=os.environ.get("BASTIAT_BASE_URL") or None,
        default_profile=os.environ.get("BASTIAT_PROFILE", "mcp_thorough"),
        verify_tls=os.environ.get("BASTIAT_VERIFY_TLS", "true").lower() != "false",
    )


@mcp.tool()
async def scrape_url(input: ScrapeUrlInput) -> dict:
    """Fetch a single URL via bastiat-api. Returns FetchResult dict with
    keys: url, content, status, strategy_used, content_type, fetched_at,
    from_cache, error."""
    scraper = _build_scraper()
    results = await scraper.scrape(
        [input.url],
        strategy=input.strategy,
        timeout=input.timeout,
        max_wait_s=input.max_wait_s,
    )
    return results[0]


@mcp.tool()
async def scrape_batch(input: ScrapeBatchInput) -> dict:
    """Fetch multiple URLs in one bastiat request. Partial successes are
    returned alongside per-URL errors via the `error` field on each result."""
    scraper = _build_scraper()
    results = await scraper.scrape(
        input.urls,
        strategy=input.strategy,
        timeout=input.timeout,
        max_wait_s=input.max_wait_s,
    )
    successes = sum(1 for r in results if not r.get("error"))
    return {
        "results": results,
        "total": len(results),
        "successes": successes,
        "failures": len(results) - successes,
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
