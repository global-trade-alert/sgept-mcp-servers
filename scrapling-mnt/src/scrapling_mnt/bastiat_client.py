"""Thin async client for bastiat-api `/scrape_urls/`.

Owns the full POST → poll lifecycle and translates the bastiat response into
the `FetchResult` shape this package's MCP tools and CLI have always emitted.

Polling schedule (per task):
  - 2s for the first 30s of wall time
  - 5s up to 120s wall time
  - 10s thereafter, until `max_wait_s` elapses
A transient 5xx on the status poll is retried up to 3× with 1/2/4s backoff
before the call gives up and surfaces an `error` on every URL in the batch.

Errors are surfaced via the `error:` field on a `FetchResult` rather than as
Python exceptions — the legacy `scrape_batch` tool always returned partial
successes plus per-URL error dicts, and this module preserves that contract.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx


# ---------------------------------------------------------------------------
# Output dataclass — kept verbatim from the legacy fetcher.FetchResult so any
# caller still talking to scrapling-mnt by dict-key sees the same shape.
# ---------------------------------------------------------------------------

@dataclass
class FetchResult:
    url: str
    content: str
    status: int
    strategy_used: str  # static | stealth | js | pdf | ocr | cache
    content_type: str
    fetched_at: float
    from_cache: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "content": self.content,
            "status": self.status,
            "strategy_used": self.strategy_used,
            "content_type": self.content_type,
            "fetched_at": self.fetched_at,
            "from_cache": self.from_cache,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Polling schedule
# ---------------------------------------------------------------------------

def _poll_interval(elapsed: float) -> float:
    if elapsed < 30:
        return 2.0
    if elapsed < 120:
        return 5.0
    return 10.0


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class BastiatScraper:
    """HTTP client over bastiat-api `/scrape_urls/`.

    All public methods are async. A single instance is safe to share across
    concurrent calls — each `scrape()` opens its own `AsyncClient` so
    `httpx` connection pools are not held open for the lifetime of an MCP
    server process.
    """

    DEFAULT_BASE_URL = "https://bastiat-api.globaltradealert.org"

    def __init__(
        self,
        api_key: str,
        *,
        base_url: Optional[str] = None,
        default_profile: str = "mcp_thorough",
        verify_tls: bool = True,
    ) -> None:
        if not api_key:
            raise ValueError("BastiatScraper requires a non-empty api_key")
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.default_profile = default_profile
        self.verify_tls = verify_tls
        self.headers = {
            "Authorization": f"APIKey {api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------ public

    async def scrape(
        self,
        urls: list[str],
        *,
        strategy: str = "auto",
        agent: bool = False,
        instructions: str = "",
        profile: Optional[str] = None,
        options_override: Optional[dict] = None,
        timeout: int = 30,
        max_wait_s: float = 600.0,
    ) -> list[dict]:
        """POST a batch to bastiat, poll until terminal, return FetchResult dicts.

        `timeout` is the per-request budget bastiat applies inside the task;
        forwarded as `options_override.timeout`. `max_wait_s` is the
        client-side poll budget — how long we keep asking for the task's
        status before giving up on it.

        Agent mode is accepted but the agent-mode response is not modelled by
        FetchResult; this method always emits scrape-shaped dicts. Callers
        wanting the richer agent payload can add a separate entry point later.
        """
        if not urls:
            return []

        merged_overrides = dict(options_override or {})
        # bastiat's per-URL budget field is `max_seconds_per_url`; expose it
        # under the friendlier name `timeout` at this layer.
        merged_overrides.setdefault("max_seconds_per_url", timeout)

        payload: dict[str, Any] = {
            "urls": [
                {"url": u, "instructions": instructions} for u in urls
            ] if (agent or instructions) else list(urls),
            "agent": agent,
            "return_content": agent,  # only meaningful when agent=True
            "profile": profile or self.default_profile,
            "options_override": merged_overrides,
            "strategy": strategy,
        }

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, read=60.0),
            verify=self.verify_tls,
        ) as client:
            try:
                task_id = await self._submit(client, payload)
            except httpx.HTTPStatusError as exc:
                return self._error_batch(urls, f"submit failed: HTTP {exc.response.status_code} {exc.response.text[:200]}")
            except (httpx.RequestError, RuntimeError) as exc:
                return self._error_batch(urls, f"submit failed: {exc}")

            try:
                bastiat_results = await self._poll(client, task_id, max_wait_s)
            except asyncio.TimeoutError as exc:
                return self._error_batch(urls, f"poll timed out: {exc}")
            except RuntimeError as exc:
                return self._error_batch(urls, str(exc))
            except httpx.RequestError as exc:
                return self._error_batch(urls, f"poll network error: {exc}")

        return self._translate_results(urls, bastiat_results)

    # ---------------------------------------------------------------- helpers

    async def _submit(self, client: httpx.AsyncClient, payload: dict) -> str:
        resp = await client.post(
            f"{self.base_url}/bastiat/scrape_urls/",
            headers=self.headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        task_id = data.get("task_id")
        if not task_id:
            raise RuntimeError(f"bastiat /scrape_urls/ returned no task_id: {data!r}")
        return task_id

    async def _poll(
        self,
        client: httpx.AsyncClient,
        task_id: str,
        max_wait_s: float,
    ) -> list[dict]:
        status_url = f"{self.base_url}/bastiat/ric_task_status/{task_id}/"
        start = time.monotonic()
        retry_backoffs = [1.0, 2.0, 4.0]
        retry_idx = 0

        while True:
            elapsed = time.monotonic() - start
            if elapsed > max_wait_s:
                raise asyncio.TimeoutError(
                    f"task {task_id} did not complete in {max_wait_s}s"
                )

            try:
                resp = await client.get(status_url, headers=self.headers)
            except httpx.RequestError:
                if retry_idx >= len(retry_backoffs):
                    raise
                await asyncio.sleep(retry_backoffs[retry_idx])
                retry_idx += 1
                continue

            if 500 <= resp.status_code < 600:
                if retry_idx >= len(retry_backoffs):
                    raise RuntimeError(
                        f"poll exhausted retries on HTTP {resp.status_code}: {resp.text[:200]}"
                    )
                await asyncio.sleep(retry_backoffs[retry_idx])
                retry_idx += 1
                continue

            resp.raise_for_status()
            retry_idx = 0
            data = resp.json()
            status = data.get("status")

            if status == "completed":
                message = data.get("message") or "{}"
                try:
                    parsed = json.loads(message) if isinstance(message, str) else message
                except json.JSONDecodeError as exc:
                    raise RuntimeError(f"malformed task message JSON: {exc}") from exc
                return parsed.get("results", []) or []

            if status == "failed":
                raise RuntimeError(f"task {task_id} failed: {data.get('message')}")

            if status == "not_found":
                raise RuntimeError(f"task {task_id} not found on bastiat")

            await asyncio.sleep(_poll_interval(elapsed))

    def _translate_results(
        self,
        urls: list[str],
        bastiat_results: list[dict],
    ) -> list[dict]:
        by_url = {r.get("url"): r for r in bastiat_results if r.get("url")}
        out: list[dict] = []
        for u in urls:
            r = by_url.get(u)
            if r is None:
                out.append(FetchResult(
                    url=u, content="", status=0,
                    strategy_used="", content_type="",
                    fetched_at=time.time(),
                    error="bastiat returned no result for this URL",
                ).to_dict())
                continue
            text = r.get("text") or ""
            strategy_used = r.get("strategy_used") or ""
            from_cache = bool(r.get("from_cache", False))
            content_type = (
                "application/pdf" if strategy_used == "pdf"
                else "text/html; charset=utf-8"
            )
            out.append(FetchResult(
                url=r.get("url", u),
                content=text,
                status=200 if text else 0,
                strategy_used=strategy_used,
                content_type=content_type,
                fetched_at=time.time(),
                from_cache=from_cache,
                error=None if text else "empty result",
            ).to_dict())
        return out

    def _error_batch(self, urls: list[str], reason: str) -> list[dict]:
        now = time.time()
        return [
            FetchResult(
                url=u, content="", status=0,
                strategy_used="", content_type="",
                fetched_at=now, error=reason,
            ).to_dict()
            for u in urls
        ]
