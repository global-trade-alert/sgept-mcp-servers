"""Per-task message history — generic append-only store.

The backend persists the actual messages; this is a small helper for
backends that want a default implementation. Iran-monitor will use this
through SQLite; other backends might back it with Postgres or a key-value
store. The interface is what matters.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import Message, TaskID


@runtime_checkable
class MessageHistoryStore(Protocol):
    """What the protocol package expects when a backend supports multi-turn."""

    async def append(self, task_id: TaskID, message: Message) -> None: ...
    async def get_history(self, task_id: TaskID) -> list[Message]: ...
    async def round_trip_count(self, task_id: TaskID) -> int:
        """How many caller↔agent round-trips have occurred. Backends typically
        compute this by counting user-role messages after the first."""
        ...


class InMemoryMessageHistory:
    """A trivial in-memory store. Useful for tests, demos, single-process
    backends. Iran-monitor and real production backends should use a
    persistent store."""

    def __init__(self) -> None:
        self._h: dict[TaskID, list[Message]] = {}

    async def append(self, task_id: TaskID, message: Message) -> None:
        self._h.setdefault(task_id, []).append(message)

    async def get_history(self, task_id: TaskID) -> list[Message]:
        return list(self._h.get(task_id, []))

    async def round_trip_count(self, task_id: TaskID) -> int:
        msgs = self._h.get(task_id, [])
        # A round-trip = one user message after the first one.
        user_msgs = [m for m in msgs if m.role.value == "user"]
        return max(0, len(user_msgs) - 1)
