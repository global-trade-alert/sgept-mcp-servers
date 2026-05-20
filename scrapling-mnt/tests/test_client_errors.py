"""Error surfaces: task failed, network mid-poll, 401, malformed JSON."""

from __future__ import annotations

import httpx
import pytest
import respx

from scrapling_mnt.bastiat_client import BastiatScraper


BASE = "https://bastiat-api.test"


@pytest.fixture
def scraper() -> BastiatScraper:
    return BastiatScraper(api_key="K", base_url=BASE)


@pytest.fixture
def fake_sleep(monkeypatch):
    async def _sleep(d):
        return None
    monkeypatch.setattr("scrapling_mnt.bastiat_client.asyncio.sleep", _sleep)


def test_construct_rejects_empty_api_key():
    with pytest.raises(ValueError):
        BastiatScraper(api_key="")


@respx.mock
async def test_submit_401_returns_error_results(scraper, fake_sleep):
    respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(401, text="unauthorized")
    )
    results = await scraper.scrape(["https://a", "https://b"])
    assert len(results) == 2
    assert all("submit failed: HTTP 401" in r["error"] for r in results)
    assert all(r["status"] == 0 for r in results)


@respx.mock
async def test_task_failed_propagates_message(scraper, fake_sleep):
    respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(200, json={"task_id": "tf"})
    )
    respx.get(f"{BASE}/bastiat/ric_task_status/tf/").mock(
        return_value=httpx.Response(200, json={
            "status": "failed",
            "message": "internal scraper boom",
        })
    )
    [r] = await scraper.scrape(["https://a"])
    assert r["status"] == 0
    assert "task tf failed" in r["error"]
    assert "internal scraper boom" in r["error"]


@respx.mock
async def test_malformed_message_json_surfaces_as_error(scraper, fake_sleep):
    respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(200, json={"task_id": "tm"})
    )
    respx.get(f"{BASE}/bastiat/ric_task_status/tm/").mock(
        return_value=httpx.Response(200, json={
            "status": "completed",
            "message": "{not valid json",
        })
    )
    [r] = await scraper.scrape(["https://a"])
    assert "malformed task message JSON" in r["error"]


@respx.mock
async def test_network_error_during_poll_exhausts_retries(scraper, fake_sleep):
    respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(200, json={"task_id": "tn"})
    )
    respx.get(f"{BASE}/bastiat/ric_task_status/tn/").mock(
        side_effect=httpx.ConnectError("conn refused")
    )
    [r] = await scraper.scrape(["https://a"])
    # After 3 retry backoffs (1/2/4), the next ConnectError re-raises and
    # surfaces as a poll network error.
    assert "poll network error" in r["error"]


@respx.mock
async def test_no_task_id_in_submit_response(scraper, fake_sleep):
    respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(200, json={"oops": "no id"})
    )
    [r] = await scraper.scrape(["https://a"])
    assert "submit failed" in r["error"]
    assert "no task_id" in r["error"]


async def test_empty_url_list_returns_empty(scraper):
    assert await scraper.scrape([]) == []
