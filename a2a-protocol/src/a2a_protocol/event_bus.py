"""In-process event bus for SSE streaming.

Per-task asyncio.Queue. Worker publishes events; SSE handler subscribes.

For multi-process deployment (Phase 2), swap this for Redis pub/sub —
same interface. The protocol package keeps the in-memory default since
Phase 1 worker concurrency is 1 and FastAPI runs in a single process.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import AsyncIterator

from .backend import TaskEvent
from .models import TaskID


class EventBus:
    """Per-task pub/sub. Subscribers get an AsyncIterator that yields until
    the task is closed (a sentinel None is published)."""

    def __init__(self) -> None:
        self._queues: dict[TaskID, list[asyncio.Queue]] = defaultdict(list)
        self._closed: set[TaskID] = set()
        self._lock = asyncio.Lock()

    async def publish(self, task_id: TaskID, event: TaskEvent) -> None:
        async with self._lock:
            for q in self._queues.get(task_id, []):
                await q.put(event)

    async def close(self, task_id: TaskID) -> None:
        """Signal end-of-stream to all subscribers for this task."""
        async with self._lock:
            self._closed.add(task_id)
            for q in self._queues.get(task_id, []):
                await q.put(None)

    async def subscribe(self, task_id: TaskID) -> AsyncIterator[TaskEvent]:
        """Yields events until close() is called for this task."""
        q: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            if task_id in self._closed:
                return
            self._queues[task_id].append(q)
        try:
            while True:
                item = await q.get()
                if item is None:
                    return
                yield item
        finally:
            async with self._lock:
                if q in self._queues.get(task_id, []):
                    self._queues[task_id].remove(q)


_default_bus: EventBus | None = None


def get_default_bus() -> EventBus:
    """Process-global default. Backends can construct their own bus instead."""
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus


def reset_default_bus_for_tests() -> None:
    global _default_bus
    _default_bus = None
