"""CLI exit codes and JSON output."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
import pytest
import respx

from scrapling_mnt import cli


BASE = "https://bastiat-api.test"


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("GTA_API_KEY", "K")
    monkeypatch.setenv("BASTIAT_BASE_URL", BASE)
    monkeypatch.setenv("BASTIAT_PROFILE", "mcp_thorough")


@pytest.fixture
def fake_sleep(monkeypatch):
    async def _sleep(d):
        return None
    monkeypatch.setattr("scrapling_mnt.bastiat_client.asyncio.sleep", _sleep)


@respx.mock
def test_scrape_url_success_exit_0(env, fake_sleep, capsys):
    respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(200, json={"task_id": "t"})
    )
    respx.get(f"{BASE}/bastiat/ric_task_status/t/").mock(
        return_value=httpx.Response(200, json={
            "status": "completed",
            "message": json.dumps({"results": [{
                "url": "https://example.com",
                "text": "hello",
                "strategy_used": "static",
                "from_cache": False,
            }]}),
        })
    )

    rc = cli.main(["scrape-url", "https://example.com", "--json"])
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["content"] == "hello"
    assert payload["strategy_used"] == "static"


@respx.mock
def test_scrape_url_empty_with_error_exit_1(env, fake_sleep, capsys):
    respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(401, text="bad key")
    )
    rc = cli.main(["scrape-url", "https://example.com", "--json"])
    assert rc == 1


def test_missing_api_key_exit_2(monkeypatch, capsys):
    monkeypatch.delenv("GTA_API_KEY", raising=False)
    rc = cli.main(["scrape-url", "https://example.com"])
    err = capsys.readouterr().err
    assert rc == 2
    assert "GTA_API_KEY" in err


@respx.mock
def test_scrape_batch_emits_per_line_json(env, fake_sleep, capsys, tmp_path: Path):
    urls_file = tmp_path / "urls.txt"
    urls_file.write_text("https://a\n# comment line\nhttps://b\n")

    respx.post(f"{BASE}/bastiat/scrape_urls/").mock(
        return_value=httpx.Response(200, json={"task_id": "tb"})
    )
    respx.get(f"{BASE}/bastiat/ric_task_status/tb/").mock(
        return_value=httpx.Response(200, json={
            "status": "completed",
            "message": json.dumps({"results": [
                {"url": "https://a", "text": "Atext",
                 "strategy_used": "static", "from_cache": False},
                {"url": "https://b", "text": "Btext",
                 "strategy_used": "stealth", "from_cache": True},
            ]}),
        })
    )

    rc = cli.main(["scrape-batch", str(urls_file)])
    out = capsys.readouterr().out.strip().splitlines()
    assert rc == 0
    assert len(out) == 2
    assert json.loads(out[0])["url"] == "https://a"
    assert json.loads(out[1])["url"] == "https://b"
