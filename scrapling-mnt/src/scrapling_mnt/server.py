"""MCP server for Scrapling-based web scraping.

Exposes:
  scrape_url    — single URL with auto cascade (static → stealth → pdf)
  scrape_pdf    — explicit PDF branch (pypdf → Gemini OCR fallback)
  scrape_batch  — multi-URL harvest with concurrency clamp
  scrape_status — health snapshot

Concurrency is clamped server-side: at most 1 browser-backed fetch at a time
(configurable via SCRAPLING_BROWSER_MAX, default 1). Static httpx fetches do
not hit the cap. SSRF defence via allowlist module.
"""

from __future__ import annotations

import asyncio
from typing import List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import BaseModel, ConfigDict, Field

from . import fetcher
from .allowlist import URLRejected


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
    timeout: int = Field(default=30, ge=5, le=120,
                         description="Per-request timeout in seconds")
    use_cache: bool = Field(default=True,
                            description="Return cached result if fresh (TTL via SCRAPLING_CACHE_TTL_DAYS)")


class ScrapePdfInput(_StrictInput):
    url: str = Field(description="PDF URL")
    ocr_fallback: bool = Field(default=True,
                               description="If native text extraction returns empty, try Gemini OCR")
    timeout: int = Field(default=60, ge=10, le=180)
    use_cache: bool = Field(default=True)


class ScrapeBatchInput(_StrictInput):
    urls: List[str] = Field(description="URLs to fetch", min_length=1, max_length=50)
    strategy: str = Field(default="auto")
    timeout: int = Field(default=30, ge=5, le=120)
    use_cache: bool = Field(default=True)
    max_concurrency: int = Field(
        default=1, ge=1, le=8,
        description="Caller hint; server clamps to SCRAPLING_BROWSER_MAX.",
    )


@mcp.tool()
async def scrape_url(input: ScrapeUrlInput) -> dict:
    """Fetch a single URL and return clean text. Auto-cascades from static
    httpx to Camoufox stealth on signs of blocking; routes to PDF branch on
    application/pdf content-type."""
    try:
        result = await fetcher.scrape_url(
            input.url,
            strategy=input.strategy,
            timeout=input.timeout,
            use_cache=input.use_cache,
        )
    except URLRejected as exc:
        raise ToolError(f"URL rejected: {exc}")
    except Exception as exc:
        raise ToolError(f"scrape_url failed: {exc}")
    return result.to_dict()


@mcp.tool()
async def scrape_pdf(input: ScrapePdfInput) -> dict:
    """Fetch a PDF: native text extraction via pypdf, fall back to Gemini OCR
    for scanned/image-only documents."""
    try:
        result = await fetcher.scrape_url(
            input.url,
            strategy="pdf",
            timeout=input.timeout,
            use_cache=input.use_cache,
            ocr_fallback=input.ocr_fallback,
        )
    except URLRejected as exc:
        raise ToolError(f"URL rejected: {exc}")
    except Exception as exc:
        raise ToolError(f"scrape_pdf failed: {exc}")
    return result.to_dict()


@mcp.tool()
async def scrape_batch(input: ScrapeBatchInput) -> dict:
    """Fetch multiple URLs. Concurrency is clamped server-side; partial
    successes are returned alongside per-URL errors."""
    sem = asyncio.Semaphore(min(
        input.max_concurrency,
        int(__import__("os").environ.get("SCRAPLING_BROWSER_MAX", "1")) + 2,
    ))

    async def _one(u: str) -> dict:
        async with sem:
            try:
                r = await fetcher.scrape_url(
                    u, strategy=input.strategy,
                    timeout=input.timeout, use_cache=input.use_cache,
                )
                return r.to_dict()
            except URLRejected as exc:
                return {"url": u, "error": f"rejected: {exc}", "status": 0}
            except Exception as exc:
                return {"url": u, "error": str(exc), "status": 0}

    results = await asyncio.gather(*[_one(u) for u in input.urls])
    successes = sum(1 for r in results if not r.get("error"))
    return {
        "results": results,
        "total": len(results),
        "successes": successes,
        "failures": len(results) - successes,
    }


@mcp.tool()
async def scrape_status() -> dict:
    """Return server health and counters."""
    return {
        "ok": True,
        **fetcher.status_snapshot(),
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
