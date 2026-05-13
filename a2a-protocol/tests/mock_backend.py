"""MockBackend — minimal AgentBackend used by protocol tests AND by the
generalization smoke (proves the protocol is reusable without Iran-monitor
imports).
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator
from uuid import uuid4

from a2a_protocol import (
    AgentBackend,
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    AgentAuthentication,
    Artifact,
    AuthContext,
    DataPart,
    Message,
    MessageRole,
    Task,
    TaskContext,
    TaskHandle,
    TaskID,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    TextPart,
)
from a2a_protocol.event_bus import EventBus


class MockBackend:
    """A minimal echo backend. Used by tests + the generalization smoke."""

    def __init__(self, *, allowed_tokens: dict[str, str] | None = None):
        self._tokens = allowed_tokens or {"mock-key": "mock-org"}
        self._tasks: dict[TaskID, Task] = {}
        self._bus = EventBus()
        self._card = AgentCard(
            name="mock-agent",
            description="Test echo backend. Not for production.",
            url="http://localhost",
            skills=[
                AgentSkill(
                    id="echo",
                    name="Echo",
                    description="Returns the submitted message as an artifact.",
                    examples=["hello world"],
                ),
            ],
            capabilities=AgentCapabilities(streaming=True),
            authentication=AgentAuthentication(schemes=["bearer"]),
        )

    @property
    def agent_card(self) -> AgentCard:
        return self._card

    @property
    def event_bus(self) -> EventBus:
        return self._bus

    def authenticate(self, token: str) -> AuthContext | None:
        org = self._tokens.get(token)
        if org is None:
            return None
        return AuthContext(principal=org, scopes=frozenset({"echo"}), raw_token=token)

    async def submit_task(
        self, message: Message, task_id: TaskID, context: TaskContext,
    ) -> TaskHandle:
        task = Task(
            id=task_id,
            context_id=context.context_id,
            status=TaskStatus(state=TaskState.SUBMITTED),
            history=[message],
        )
        self._tasks[task_id] = task
        # Drive it to completion asynchronously
        asyncio.create_task(self._echo_workflow(task_id, message))
        return TaskHandle(task=task)

    async def continue_task(
        self, task_id: TaskID, message: Message, history: list[Message],
    ) -> TaskHandle:
        task = self._tasks.get(task_id)
        if task is None:
            from a2a_protocol import A2AError, JSONRPCErrorCode
            raise A2AError(JSONRPCErrorCode.TASK_NOT_FOUND, f"unknown task {task_id}")
        task.history.append(message)
        return TaskHandle(task=task)

    async def cancel_task(self, task_id: TaskID) -> Task:
        task = self._tasks.get(task_id)
        if task is None:
            from a2a_protocol import A2AError, JSONRPCErrorCode
            raise A2AError(JSONRPCErrorCode.TASK_NOT_FOUND, f"unknown task {task_id}")
        task.status = TaskStatus(state=TaskState.CANCELED)
        await self._bus.close(task_id)
        return task

    async def get_task(self, task_id: TaskID) -> Task | None:
        return self._tasks.get(task_id)

    async def stream_events(self, task_id: TaskID) -> AsyncIterator:
        async for ev in self._bus.subscribe(task_id):
            yield ev

    async def _echo_workflow(self, task_id: TaskID, message: Message) -> None:
        """Async: working → artifact → completed. Publishes SSE events."""
        await asyncio.sleep(0)  # yield
        await self._bus.publish(task_id, TaskStatusUpdateEvent(
            task_id=task_id, context_id=self._tasks[task_id].context_id,
            status=TaskStatus(state=TaskState.WORKING),
        ))
        await asyncio.sleep(0)
        artifact = Artifact(
            name="echo",
            description="The message you sent.",
            parts=[TextPart(text=message.text() or "")],
        )
        self._tasks[task_id].artifacts.append(artifact)
        await self._bus.publish(task_id, TaskArtifactUpdateEvent(
            task_id=task_id, context_id=self._tasks[task_id].context_id,
            artifact=artifact,
        ))
        self._tasks[task_id].status = TaskStatus(state=TaskState.COMPLETED)
        await self._bus.publish(task_id, TaskStatusUpdateEvent(
            task_id=task_id, context_id=self._tasks[task_id].context_id,
            status=TaskStatus(state=TaskState.COMPLETED),
            final=True,
        ))
        await self._bus.close(task_id)
