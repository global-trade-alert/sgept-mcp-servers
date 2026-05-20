"""POST body + auth header shape on the submit call."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from scrapling_mnt.bastiat_client import BastiatScraper


BASE = "https://bastiat-api.test"


@pytest.fixture
def scraper() -> BastiatScraper:
    return BastiatScraper(api_key="K", base_url=BASE)


@respx.mock
async def test_submit_body_default_profile(scraper):
    submit = respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(200, json={"task_id": "t1"})
    )
    respx.get(f"{BASE}/bastiat/ric_task_status/t1/").mock(
        return_value=httpx.Response(200, json={
            "status": "completed",
            "message": json.dumps({"results": [
                {"url": "https://example.com", "text": "hi",
                 "strategy_used": "static", "from_cache": False},
            ]}),
        })
    )

    await scraper.scrape(["https://example.com"])

    assert submit.called
    sent = json.loads(submit.calls[0].request.content)
    assert sent["urls"] == ["https://example.com"]
    assert sent["agent"] is False
    assert sent["return_content"] is False
    assert sent["profile"] == "mcp_thorough"
    assert sent["strategy"] == "auto"
    assert sent["options_override"]["max_seconds_per_url"] == 30
    auth = submit.calls[0].request.headers["authorization"]
    assert auth == "APIKey K"


@respx.mock
async def test_submit_body_overrides_propagate(scraper):
    submit = respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(200, json={"task_id": "t2"})
    )
    respx.get(f"{BASE}/bastiat/ric_task_status/t2/").mock(
        return_value=httpx.Response(200, json={
            "status": "completed",
            "message": json.dumps({"results": [
                {"url": "https://a", "text": "x", "strategy_used": "stealth", "from_cache": True},
            ]}),
        })
    )

    await scraper.scrape(
        ["https://a"],
        strategy="stealth",
        profile="bastiat_batch_fast",
        options_override={"use_cache": False},
        timeout=45,
    )

    sent = json.loads(submit.calls[0].request.content)
    assert sent["strategy"] == "stealth"
    assert sent["profile"] == "bastiat_batch_fast"
    assert sent["options_override"]["use_cache"] is False
    assert sent["options_override"]["max_seconds_per_url"] == 45


@respx.mock
async def test_agent_mode_packs_url_objects(scraper):
    submit = respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(200, json={"task_id": "t3"})
    )
    respx.get(f"{BASE}/bastiat/ric_task_status/t3/").mock(
        return_value=httpx.Response(200, json={
            "status": "completed",
            "message": json.dumps({"results": [
                {"url": "https://seed", "text": "y",
                 "strategy_used": "static", "from_cache": False},
            ]}),
        })
    )

    await scraper.scrape(
        ["https://seed"],
        agent=True,
        instructions="dig deep",
    )

    sent = json.loads(submit.calls[0].request.content)
    assert sent["agent"] is True
    assert sent["return_content"] is True
    assert sent["urls"] == [{"url": "https://seed", "instructions": "dig deep"}]
