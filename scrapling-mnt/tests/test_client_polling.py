"""Task-lifecycle polling: running → completed, FetchResult translation, backoff schedule."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from scrapling_mnt.bastiat_client import BastiatScraper, _poll_interval


BASE = "https://bastiat-api.test"


@pytest.fixture
def scraper() -> BastiatScraper:
    return BastiatScraper(api_key="K", base_url=BASE)


@pytest.fixture
def fake_sleep(monkeypatch):
    """Replace asyncio.sleep inside bastiat_client with a coroutine that records
    invocations and returns immediately."""
    recorded: list[float] = []

    async def _sleep(d):
        recorded.append(d)

    monkeypatch.setattr("scrapling_mnt.bastiat_client.asyncio.sleep", _sleep)
    return recorded


def test_poll_interval_buckets():
    assert _poll_interval(0) == 2.0
    assert _poll_interval(29.9) == 2.0
    assert _poll_interval(30.0) == 5.0
    assert _poll_interval(119.9) == 5.0
    assert _poll_interval(120.0) == 10.0
    assert _poll_interval(1000.0) == 10.0


@respx.mock
async def test_running_then_completed_translates_to_fetchresult(scraper, fake_sleep):
    """Two `running` polls then `completed`. Result fields land in FetchResult."""
    respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(200, json={"task_id": "t1"})
    )

    status_responses = iter([
        httpx.Response(200, json={"status": "running"}),
        httpx.Response(200, json={"status": "running"}),
        httpx.Response(200, json={
            "status": "completed",
            "message": json.dumps({"results": [{
                "url": "https://example.com",
                "text": "hello world",
                "strategy_used": "static",
                "from_cache": False,
            }]}),
        }),
    ])
    respx.get(f"{BASE}/bastiat/ric_task_status/t1/").mock(
        side_effect=lambda req: next(status_responses)
    )

    results = await scraper.scrape(["https://example.com"])

    assert len(results) == 1
    r = results[0]
    assert r["url"] == "https://example.com"
    assert r["content"] == "hello world"
    assert r["status"] == 200
    assert r["strategy_used"] == "static"
    assert r["content_type"] == "text/html; charset=utf-8"
    assert r["from_cache"] is False
    assert r["error"] is None
    # two `running` responses → two sleeps; both early so 2.0s each
    assert fake_sleep == [2.0, 2.0]


@respx.mock
async def test_pdf_strategy_yields_pdf_content_type(scraper, fake_sleep):
    respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(200, json={"task_id": "tp"})
    )
    respx.get(f"{BASE}/bastiat/ric_task_status/tp/").mock(
        return_value=httpx.Response(200, json={
            "status": "completed",
            "message": json.dumps({"results": [{
                "url": "https://example.com/doc.pdf",
                "text": "page1",
                "strategy_used": "pdf",
                "from_cache": True,
            }]}),
        }),
    )

    [r] = await scraper.scrape(["https://example.com/doc.pdf"], strategy="pdf")
    assert r["content_type"] == "application/pdf"
    assert r["strategy_used"] == "pdf"
    assert r["from_cache"] is True


@respx.mock
async def test_url_not_in_bastiat_response_gets_synthetic_error(scraper, fake_sleep):
    respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(200, json={"task_id": "tm"})
    )
    respx.get(f"{BASE}/bastiat/ric_task_status/tm/").mock(
        return_value=httpx.Response(200, json={
            "status": "completed",
            "message": json.dumps({"results": [{
                "url": "https://a",
                "text": "a-text",
                "strategy_used": "static",
                "from_cache": False,
            }]}),
        })
    )

    results = await scraper.scrape(["https://a", "https://missing"])
    by_url = {r["url"]: r for r in results}
    assert by_url["https://a"]["content"] == "a-text"
    assert by_url["https://missing"]["error"] == "bastiat returned no result for this URL"
