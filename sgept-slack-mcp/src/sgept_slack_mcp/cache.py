"""TTL cache implementation for caching Slack API responses."""

import time
from typing import TypeVar, Generic, Optional, Callable, Any
from dataclasses import dataclass, field

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """A cached value with expiration time."""
    value: T
    expires_at: float


class TTLCache(Generic[T]):
    """Simple TTL (Time-To-Live) cache for storing values that expire."""

    def __init__(self, ttl_seconds: float = 300.0):
        """
        Initialize cache with TTL.

        Args:
            ttl_seconds: How long cached values remain valid (default: 5 minutes)
        """
        self._ttl = ttl_seconds
        self._cache: dict[str, CacheEntry[T]] = {}

    def get(self, key: str) -> Optional[T]:
        """
        Get a cached value if it exists and hasn't expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        entry = self._cache.get(key)
        if entry is None:
            return None

        if time.time() > entry.expires_at:
            # Entry has expired, remove it
            del self._cache[key]
            return None

        return entry.value

    def set(self, key: str, value: T) -> None:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = CacheEntry(
            value=value,
            expires_at=time.time() + self._ttl
        )

    def invalidate(self, key: str) -> None:
        """
        Remove a specific key from the cache.

        Args:
            key: Cache key to remove
        """
        self._cache.pop(key, None)

    def invalidate_all(self) -> None:
        """Remove all entries from the cache."""
        self._cache.clear()

    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        """
        Get cached value or compute and cache it.

        Args:
            key: Cache key
            factory: Function to compute value if not cached

        Returns:
            Cached or newly computed value
        """
        value = self.get(key)
        if value is not None:
            return value

        value = factory()
        self.set(key, value)
        return value

    async def get_or_set_async(self, key: str, factory: Callable[[], Any]) -> T:
        """
        Async version of get_or_set.

        Args:
            key: Cache key
            factory: Async function to compute value if not cached

        Returns:
            Cached or newly computed value
        """
        value = self.get(key)
        if value is not None:
            return value

        value = await factory()
        self.set(key, value)
        return value

    @property
    def ttl(self) -> float:
        """Get the cache TTL in seconds."""
        return self._ttl

    def __len__(self) -> int:
        """Return number of entries (including possibly expired ones)."""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None
