"""Scrapling-backed cascade fetcher.

Single-URL strategy auto-cascade:
  1. static  — Scrapling.Fetcher (httpx-based, fast, follows redirects)
  2. stealth — Scrapling.StealthyFetcher (Camoufox/Firefox, anti-bot, JS)
  3. js      — Scrapling.DynamicFetcher (Chromium/Playwright; full JS execution).
                When the URL hints at PDF, registers a network-response listener
                and returns the intercepted PDF binary instead of the rendered
                HTML — handles SPA wrappers like the EAEU document portal where
                /filestorage/foo.pdf serves an Angular shell that fetches the
                real PDF from a separate /platformsvc/filestorage/get endpoint.
  4. pdf     — pypdf for native, OCR fallback for scanned

Outputs: markdown (via BeautifulSoup text extraction) for HTML, raw text for PDF.

Concurrency: an asyncio.Semaphore caps simultaneous browser-backed fetches at 1
(Metis 8GB RAM constraint). Static fetches do not consume the semaphore.

Heavy-weight imports (scrapling, camoufox, pypdf) are deferred until needed so
that `scrape_status` and import-time costs stay minimal.
"""

from __future__ import annotations

import asyncio
import io
import os
import re
import time
from dataclasses import dataclass
from typing import Optional

from . import cache
from .allowlist import URLRejected, check_url


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_BROWSER_SEMAPHORE: Optional[asyncio.Semaphore] = None
_STATIC_FETCHER = None  # lazy
_STEALTH_FETCHER = None  # lazy
_DYNAMIC_FETCHER = None  # lazy
_LAST_FETCH_AT: float = 0.0
_FETCH_COUNT: int = 0


def browser_semaphore() -> asyncio.Semaphore:
    global _BROWSER_SEMAPHORE
    if _BROWSER_SEMAPHORE is None:
        # Default 1; never raised above 1 on Metis. Mac dev can opt-in higher.
        cap = int(os.environ.get("SCRAPLING_BROWSER_MAX", "1"))
        _BROWSER_SEMAPHORE = asyncio.Semaphore(cap)
    return _BROWSER_SEMAPHORE


# ---------------------------------------------------------------------------
# Outputs
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
# Helpers
# ---------------------------------------------------------------------------

_JS_PLACEHOLDER_RE = re.compile(
    r"(please enable javascript|enable js|noscript)",
    re.IGNORECASE,
)


def _looks_blocked(html: str, status: int) -> bool:
    """Heuristic: does this response indicate we should escalate to stealth?"""
    if status in (403, 405, 406, 429, 503):
        return True
    if not html or len(html.strip()) < 200:
        return True
    return bool(_JS_PLACEHOLDER_RE.search(html[:4000]))


def _html_to_markdown(html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    # collapse runs of blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _is_pdf(content_type: str, url: str) -> bool:
    return "application/pdf" in (content_type or "").lower() or url.lower().endswith(".pdf")


# ---------------------------------------------------------------------------
# Strategy implementations
# ---------------------------------------------------------------------------

async def _fetch_static(url: str, timeout: int) -> tuple[Optional[str], int, str]:
    """Static fetch via Scrapling.Fetcher."""
    global _STATIC_FETCHER
    if _STATIC_FETCHER is None:
        from scrapling.fetchers import Fetcher
        _STATIC_FETCHER = Fetcher

    def _go():
        return _STATIC_FETCHER.get(url, timeout=timeout, follow_redirects=True)

    page = await asyncio.to_thread(_go)
    status = getattr(page, "status", 0) or 0
    body = getattr(page, "body", None) or getattr(page, "text", "") or ""
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    headers = getattr(page, "headers", {}) or {}
    content_type = headers.get("content-type") or headers.get("Content-Type") or ""
    return body, status, content_type


async def _fetch_stealth(url: str, timeout: int) -> tuple[Optional[str], int, str]:
    """Stealth fetch via Scrapling.StealthyFetcher (Camoufox)."""
    global _STEALTH_FETCHER
    if _STEALTH_FETCHER is None:
        from scrapling.fetchers import StealthyFetcher
        _STEALTH_FETCHER = StealthyFetcher

    def _go():
        return _STEALTH_FETCHER.fetch(
            url,
            headless=True,
            network_idle=True,
            humanize=True,
            timeout=timeout * 1000,
        )

    async with browser_semaphore():
        page = await asyncio.to_thread(_go)
    status = getattr(page, "status", 0) or 0
    body = getattr(page, "body", None) or getattr(page, "html_content", "") or ""
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    return body, status, "text/html; charset=utf-8"


def _dynamic_fetcher():
    """Lazy import of scrapling.fetchers.DynamicFetcher (Chromium/Playwright)."""
    global _DYNAMIC_FETCHER
    if _DYNAMIC_FETCHER is None:
        from scrapling.fetchers import DynamicFetcher
        _DYNAMIC_FETCHER = DynamicFetcher
    return _DYNAMIC_FETCHER


async def _fetch_js(url: str, timeout: int) -> tuple[Optional[str], int, str]:
    """JS-rendered fetch via Scrapling.DynamicFetcher (Chromium/Playwright).

    Use when stealth (Camoufox) can't bootstrap the page or when the page is
    a single-page app whose initial HTML is empty until JS runs.
    """
    fetcher = _dynamic_fetcher()

    def _go():
        return fetcher.fetch(
            url,
            headless=True,
            network_idle=True,
            timeout=timeout * 1000,
        )

    async with browser_semaphore():
        page = await asyncio.to_thread(_go)
    status = getattr(page, "status", 0) or 0
    body = getattr(page, "body", None) or getattr(page, "html_content", "") or ""
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    return body, status, "text/html; charset=utf-8"


def _looks_like_pdf(b: bytes) -> bool:
    return isinstance(b, (bytes, bytearray)) and b[:4] == b"%PDF"


async def _fetch_js_intercept_pdf(
    url: str, timeout: int
) -> tuple[Optional[bytes], int, str, Optional[str]]:
    """Render `url` with DynamicFetcher and intercept any PDF binary the page
    fetches via XHR. Returns (pdf_bytes, status, content_type, intercepted_url).

    Designed for SPA wrappers: a URL like /dimd/filestorage/foo.pdf returns the
    Angular shell, which then fetches the real PDF from /platformsvc/.../get.
    We register a `response` listener via `page_setup` so it's installed BEFORE
    navigation, then read `resp.body()` (sync API) for any PDF/octet-stream
    response with PDF magic bytes.

    Falls back to (None, status, "text/html", None) if no PDF was intercepted —
    caller can then treat it as a regular JS-rendered page.
    """
    fetcher = _dynamic_fetcher()
    captured: list[tuple[str, str, bytes]] = []  # (url, content_type, body)

    def setup(page):
        def on_response(resp):
            try:
                ct = (resp.headers or {}).get("content-type", "") or ""
                low = ct.lower()
                if "pdf" not in low and "octet-stream" not in low:
                    return
                body = resp.body()  # sync Playwright API → bytes
                if not body or not _looks_like_pdf(body):
                    return
                captured.append((resp.url, ct, body))
            except Exception:
                # Response may be torn down or non-buffered; ignore and keep going.
                return
        page.on("response", on_response)

    def _go():
        return fetcher.fetch(
            url,
            headless=True,
            network_idle=True,
            timeout=timeout * 1000,
            page_setup=setup,
        )

    async with browser_semaphore():
        page = await asyncio.to_thread(_go)
    status = getattr(page, "status", 0) or 0

    if captured:
        # Prefer the first PDF response that isn't trivially small.
        captured.sort(key=lambda c: -len(c[2]))
        pdf_url, ct, body = captured[0]
        return body, status, (ct or "application/pdf"), pdf_url

    return None, status, "text/html; charset=utf-8", None


async def _fetch_pdf(
    url: str,
    timeout: int,
    ocr_fallback: bool,
    *,
    prefetched: Optional[bytes] = None,
    prefetched_status: int = 200,
    prefetched_content_type: str = "application/pdf",
    strategy_label: str = "pdf",
) -> FetchResult:
    """PDF branch: extract via pypdf, OCR fallback if empty.

    If `prefetched` is provided, skip the HTTP download — used by the
    JS-intercept path which already captured the PDF binary via Playwright.
    """
    from pypdf import PdfReader

    if prefetched is not None:
        pdf_bytes = prefetched
        status = prefetched_status
        content_type = prefetched_content_type
    else:
        import httpx
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "scrapling-mnt/0.1"})
        status = resp.status_code
        content_type = resp.headers.get("content-type", "application/pdf")
        pdf_bytes = resp.content

    cache.write_bytes(
        url, pdf_bytes,
        strategy="pdf-bytes", status=status,
        content_type=content_type, ext="pdf",
    )

    text_chunks = []
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            chunk = page.extract_text() or ""
            text_chunks.append(chunk)
    except Exception as exc:
        return FetchResult(
            url=url, content="", status=status,
            strategy_used=strategy_label, content_type=content_type,
            fetched_at=time.time(),
            error=f"pypdf failed: {exc}",
        )

    text = "\n\n".join(c for c in text_chunks if c.strip())

    if text.strip() or not ocr_fallback:
        return FetchResult(
            url=url, content=text, status=status,
            strategy_used=strategy_label, content_type=content_type,
            fetched_at=time.time(),
        )

    # OCR fallback
    try:
        from . import ocr
        ocr_text = await ocr.gemini_ocr_pdf(pdf_bytes)
        return FetchResult(
            url=url, content=ocr_text, status=status,
            strategy_used="ocr", content_type=content_type,
            fetched_at=time.time(),
        )
    except Exception as exc:
        return FetchResult(
            url=url, content=text, status=status,
            strategy_used=strategy_label, content_type=content_type,
            fetched_at=time.time(),
            error=f"OCR fallback failed: {exc}",
        )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def scrape_url(
    url: str,
    *,
    strategy: str = "auto",
    timeout: int = 30,
    use_cache: bool = True,
    ocr_fallback: bool = True,
) -> FetchResult:
    """Fetch a single URL with cascade.

    Strategy:
      - "auto"    — static → stealth → (pdf branch if content-type pdf);
                    additionally: if URL hints PDF but static returned HTML,
                    escalate to JS+intercept which renders the page in
                    Chromium and captures the real PDF binary off the wire
                    (handles SPA-wrapped PDF viewers like the EAEU portal).
      - "static"  — Scrapling.Fetcher only
      - "stealth" — StealthyFetcher (Camoufox) only
      - "js"      — DynamicFetcher (Chromium) only
      - "pdf"     — direct PDF branch (httpx download)
    """
    global _LAST_FETCH_AT, _FETCH_COUNT

    check_url(url)

    if use_cache:
        cached = cache.read(url, ext="md")
        if cached:
            body, meta = cached
            return FetchResult(
                url=url, content=body, status=meta.status,
                strategy_used="cache", content_type=meta.content_type,
                fetched_at=meta.fetched_at, from_cache=True,
            )

    _FETCH_COUNT += 1
    _LAST_FETCH_AT = time.time()

    # Forced strategies
    if strategy == "pdf":
        result = await _fetch_pdf(url, timeout, ocr_fallback)
        if result.content:
            cache.write(url, result.content, strategy=result.strategy_used,
                        status=result.status, content_type=result.content_type)
        return result

    if strategy == "stealth":
        body, status, ct = await _fetch_stealth(url, timeout)
        text = _html_to_markdown(body or "")
        result = FetchResult(url=url, content=text, status=status,
                             strategy_used="stealth", content_type=ct,
                             fetched_at=time.time())
        if text:
            cache.write(url, text, strategy="stealth", status=status, content_type=ct)
        return result

    if strategy == "js":
        # If URL hints PDF, try JS+intercept first; otherwise plain JS render.
        if url.lower().endswith(".pdf"):
            pdf_bytes, status, ct, intercepted = await _fetch_js_intercept_pdf(url, timeout)
            if pdf_bytes is not None:
                result = await _fetch_pdf(
                    url, timeout, ocr_fallback,
                    prefetched=pdf_bytes,
                    prefetched_status=status,
                    prefetched_content_type=ct,
                    strategy_label="js-pdf",
                )
                if result.content:
                    cache.write(url, result.content, strategy=result.strategy_used,
                                status=result.status, content_type=result.content_type)
                return result
            # No PDF intercepted; fall through to plain JS render.
        body, status, ct = await _fetch_js(url, timeout)
        text = _html_to_markdown(body or "")
        result = FetchResult(url=url, content=text, status=status,
                             strategy_used="js", content_type=ct,
                             fetched_at=time.time())
        if text:
            cache.write(url, text, strategy="js", status=status, content_type=ct)
        return result

    if strategy == "static":
        body, status, ct = await _fetch_static(url, timeout)
        if _is_pdf(ct, url):
            return await _fetch_pdf(url, timeout, ocr_fallback)
        text = _html_to_markdown(body or "")
        result = FetchResult(url=url, content=text, status=status,
                             strategy_used="static", content_type=ct,
                             fetched_at=time.time())
        if text:
            cache.write(url, text, strategy="static", status=status, content_type=ct)
        return result

    # auto cascade
    body, status, ct = await _fetch_static(url, timeout)
    ct_lower = (ct or "").lower()
    is_html_response = "html" in ct_lower
    is_pdf_response = "application/pdf" in ct_lower

    if is_pdf_response:
        # Real PDF — re-download via httpx in _fetch_pdf to keep bytes intact.
        # We could try to reuse the static fetcher's body, but Scrapling.Fetcher
        # decodes responses to str, which corrupts binary PDF data on round-trip.
        result = await _fetch_pdf(url, timeout, ocr_fallback)
        if result.content:
            cache.write(url, result.content, strategy=result.strategy_used,
                        status=result.status, content_type=result.content_type)
        return result

    # SPA-wrapped PDF detector: URL ends in .pdf but server returned HTML.
    # Static and stealth will both get the SPA shell; only Chromium can render
    # the page and trigger the XHR that fetches the real PDF binary.
    if url.lower().endswith(".pdf") and is_html_response:
        pdf_bytes, status_js, ct_js, intercepted = await _fetch_js_intercept_pdf(url, timeout)
        if pdf_bytes is not None:
            result = await _fetch_pdf(
                url, timeout, ocr_fallback,
                prefetched=pdf_bytes,
                prefetched_status=status_js,
                prefetched_content_type=ct_js,
                strategy_label="js-pdf",
            )
            if result.content:
                cache.write(url, result.content, strategy=result.strategy_used,
                            status=result.status, content_type=result.content_type)
            return result
        # JS+intercept didn't find a PDF — fall through to normal HTML cascade.

    text = _html_to_markdown(body or "")
    # Escalate to stealth on either (a) hostile raw response (status codes,
    # JS placeholder) or (b) extracted text is too thin — catches SPAs whose
    # raw HTML is large but renders almost nothing without JS.
    if not _looks_blocked(body or "", status) and len(text.strip()) >= 200:
        cache.write(url, text, strategy="static", status=status, content_type=ct)
        return FetchResult(url=url, content=text, status=status,
                           strategy_used="static", content_type=ct,
                           fetched_at=time.time())

    # Escalate to stealth
    body2, status2, ct2 = await _fetch_stealth(url, timeout)
    text2 = _html_to_markdown(body2 or "")
    if text2:
        cache.write(url, text2, strategy="stealth", status=status2, content_type=ct2)
        return FetchResult(url=url, content=text2, status=status2,
                           strategy_used="stealth", content_type=ct2,
                           fetched_at=time.time())

    # Last resort: surface what we have with a soft error
    return FetchResult(
        url=url, content=_html_to_markdown(body or "") or "",
        status=status, strategy_used="static",
        content_type=ct, fetched_at=time.time(),
        error="static returned thin/blocked content; stealth also failed",
    )


def status_snapshot() -> dict:
    return {
        "fetch_count": _FETCH_COUNT,
        "last_fetch_at": _LAST_FETCH_AT,
        "browser_max": int(os.environ.get("SCRAPLING_BROWSER_MAX", "1")),
        "cache_dir": str(cache.cache_root()),
    }
