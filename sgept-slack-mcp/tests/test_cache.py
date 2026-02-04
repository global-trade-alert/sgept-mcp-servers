"""Tests for TTL cache implementation."""

import time
import pytest
from unittest.mock import patch

from sgept_slack_mcp.cache import TTLCache


class TestTTLCache:
    """Tests for TTLCache class."""

    def test_cache_stores_and_retrieves_value(self):
        """Test that cache stores and retrieves values correctly."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=300)
        cache.set("key1", "value1")

        assert cache.get("key1") == "value1"

    def test_cache_returns_none_for_missing_key(self):
        """Test that cache returns None for missing keys."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=300)

        assert cache.get("nonexistent") is None

    def test_cache_expires_after_ttl(self):
        """Test that cached values expire after TTL."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=1)
        cache.set("key1", "value1")

        # Value should be present immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Value should be expired
        assert cache.get("key1") is None

    def test_cache_invalidate_removes_key(self):
        """Test that invalidate removes a specific key."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=300)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.invalidate("key1")

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_cache_invalidate_all_clears_cache(self):
        """Test that invalidate_all clears the entire cache."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=300)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.invalidate_all()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_get_or_set_returns_cached_value(self):
        """Test that get_or_set returns cached value if present."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=300)
        cache.set("key1", "cached_value")

        # Factory should not be called
        factory_called = False

        def factory():
            nonlocal factory_called
            factory_called = True
            return "new_value"

        result = cache.get_or_set("key1", factory)

        assert result == "cached_value"
        assert not factory_called

    def test_cache_get_or_set_computes_missing_value(self):
        """Test that get_or_set computes and caches missing values."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=300)

        def factory():
            return "computed_value"

        result = cache.get_or_set("key1", factory)

        assert result == "computed_value"
        assert cache.get("key1") == "computed_value"

    def test_cache_contains_operator(self):
        """Test the __contains__ operator."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=300)
        cache.set("key1", "value1")

        assert "key1" in cache
        assert "nonexistent" not in cache

    def test_cache_len_returns_entry_count(self):
        """Test that len returns the number of entries."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=300)

        assert len(cache) == 0

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert len(cache) == 2

    def test_cache_ttl_property(self):
        """Test that ttl property returns configured TTL."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=600)

        assert cache.ttl == 600


@pytest.mark.asyncio
class TestTTLCacheAsync:
    """Async tests for TTLCache."""

    async def test_cache_get_or_set_async(self):
        """Test async get_or_set."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=300)

        async def async_factory():
            return "async_value"

        result = await cache.get_or_set_async("key1", async_factory)

        assert result == "async_value"
        assert cache.get("key1") == "async_value"

    async def test_cache_get_or_set_async_returns_cached(self):
        """Test async get_or_set returns cached value."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=300)
        cache.set("key1", "cached_value")

        factory_called = False

        async def async_factory():
            nonlocal factory_called
            factory_called = True
            return "new_value"

        result = await cache.get_or_set_async("key1", async_factory)

        assert result == "cached_value"
        assert not factory_called
