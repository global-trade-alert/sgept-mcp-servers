"""Cache write/read round-trip. No network."""

import time

import pytest

from scrapling_mnt import cache


@pytest.fixture
def cache_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SCRAPLING_CACHE_DIR", str(tmp_path))
    return tmp_path


def test_write_then_read(cache_dir):
    url = "https://example.com/x"
    meta = cache.write(url, "hello world", strategy="static",
                       status=200, content_type="text/html")
    assert meta.url == url
    got = cache.read(url, ext="md")
    assert got is not None
    body, meta2 = got
    assert body == "hello world"
    assert meta2.strategy == "static"
    assert meta2.status == 200


def test_miss_returns_none(cache_dir):
    assert cache.read("https://example.com/never-fetched") is None


def test_ttl_expiry(cache_dir, monkeypatch):
    monkeypatch.setenv("SCRAPLING_CACHE_TTL_DAYS", "0")  # 0 days = always stale
    cache.write("https://example.com/y", "stale", strategy="static",
                status=200, content_type="text/html")
    # 0 days → ttl is 0s → any read after a microsecond is stale
    time.sleep(0.001)
    assert cache.read("https://example.com/y") is None
