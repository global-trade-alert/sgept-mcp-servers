"""IranMonitorBackend — A2A protocol translation layer."""

from __future__ import annotations

import json
import pytest

from a2a_protocol import (
    AgentBackend,
    AgentCard,
    AuthContext,
    DataPart,
    Message,
    MessageRole,
    TaskContext,
    TaskState,
    TextPart,
)

from iran_monitor_api import db
from iran_monitor_api.backend import IranMonitorBackend


@pytest.fixture
def backend(isolated_env):
    return IranMonitorBackend()


def test_implements_protocol(backend):
    assert isinstance(backend, AgentBackend)


def test_agent_card_advertises_skills(backend):
    card = backend.agent_card
    assert isinstance(card, AgentCard)
    assert card.name == "iran-monitor"
    assert len(card.skills) == 1
    assert card.skills[0].id == "assess_scenario"
    assert card.capabilities.streaming is True
    assert card.capabilities.push_notifications is False
    assert card.capabilities.streaming_granularity == "event"
    assert card.authentication.schemes == ["bearer"]


def test_authenticate_accepts_valid_key(backend):
    ctx = backend.authenticate("test-key-A")
    assert ctx is not None
    assert ctx.principal == "test-org-A"
    assert "assess_scenario" in ctx.scopes


def test_authenticate_rejects_invalid_key(backend):
    assert backend.authenticate("wrong-key") is None


@pytest.mark.asyncio
async def test_submit_task_with_data_part(backend):
    msg = Message(
        role=MessageRole.USER,
        parts=[DataPart(data={
            "scenario": "Iran launches cyber attack on German infrastructure within 30 days",
            "horizon": "30d",
            "tier": "premium",
        })],
    )
    auth = backend.authenticate("test-key-A")
    from uuid import uuid4
    task_id = str(uuid4())
    ctx = TaskContext(auth=auth, context_id="ctx-1")
    handle = await backend.submit_task(msg, task_id, ctx)
    assert handle.task.id == task_id
    assert handle.task.status.state == TaskState.SUBMITTED

    # DB row exists
    from uuid import UUID
    row = db.get_query(UUID(task_id))
    assert row is not None
    assert row["org_id"] == "test-org-A"
    assert row["tier"] == "premium"


@pytest.mark.asyncio
async def test_submit_task_with_text_part_defaults(backend):
    msg = Message(
        role=MessageRole.USER,
        parts=[TextPart(text="Iran launches cyber attack on German infrastructure within 30 days")],
    )
    auth = backend.authenticate("test-key-A")
    from uuid import uuid4
    task_id = str(uuid4())
    ctx = TaskContext(auth=auth, context_id="ctx-2")
    handle = await backend.submit_task(msg, task_id, ctx)
    from uuid import UUID
    row = db.get_query(UUID(task_id))
    assert row["tier"] == "standard"      # default
    assert row["horizon"] == "30d"        # default


@pytest.mark.asyncio
async def test_get_task_returns_none_for_unknown(backend):
    from uuid import uuid4
    assert (await backend.get_task(str(uuid4()))) is None


@pytest.mark.asyncio
async def test_get_task_builds_a2a_task_from_db_row(backend):
    msg = Message(
        role=MessageRole.USER,
        parts=[DataPart(data={
            "scenario": "Iran launches cyber attack on German infrastructure within 30 days",
            "horizon": "30d",
            "tier": "standard",
        })],
    )
    auth = backend.authenticate("test-key-A")
    from uuid import uuid4
    task_id = str(uuid4())
    ctx = TaskContext(auth=auth, context_id="ctx-3")
    await backend.submit_task(msg, task_id, ctx)

    fetched = await backend.get_task(task_id)
    assert fetched is not None
    assert fetched.id == task_id
    assert fetched.status.state == TaskState.SUBMITTED
    assert fetched.metadata["tier"] == "standard"


@pytest.mark.asyncio
async def test_cancel_task_transitions_to_canceled(backend):
    msg = Message(
        role=MessageRole.USER,
        parts=[DataPart(data={
            "scenario": "Iran launches cyber attack on German infrastructure within 30 days",
            "horizon": "30d",
            "tier": "standard",
        })],
    )
    auth = backend.authenticate("test-key-A")
    from uuid import uuid4
    task_id = str(uuid4())
    ctx = TaskContext(auth=auth, context_id="ctx-4")
    await backend.submit_task(msg, task_id, ctx)

    final = await backend.cancel_task(task_id)
    # After cancel, DB row status is "canceled"; backend translation may map to FAILED
    # since canceled isn't in the Status enum yet — verify the DB.
    from uuid import UUID
    row = db.get_query(UUID(task_id))
    assert row["status"] == "canceled"


@pytest.mark.asyncio
async def test_submit_rejects_unknown_tier(backend):
    msg = Message(
        role=MessageRole.USER,
        parts=[DataPart(data={
            "scenario": "x" * 80,
            "horizon": "30d",
            "tier": "ultra",
        })],
    )
    auth = backend.authenticate("test-key-A")
    from uuid import uuid4
    ctx = TaskContext(auth=auth, context_id="ctx-5")
    from a2a_protocol import A2AError
    with pytest.raises(A2AError):
        await backend.submit_task(msg, str(uuid4()), ctx)


@pytest.mark.asyncio
async def test_submit_rejects_unknown_horizon(backend):
    msg = Message(
        role=MessageRole.USER,
        parts=[DataPart(data={
            "scenario": "x" * 80,
            "horizon": "120d",
            "tier": "standard",
        })],
    )
    auth = backend.authenticate("test-key-A")
    from uuid import uuid4
    ctx = TaskContext(auth=auth, context_id="ctx-6")
    from a2a_protocol import A2AError
    with pytest.raises(A2AError):
        await backend.submit_task(msg, str(uuid4()), ctx)


@pytest.mark.asyncio
async def test_submit_rejects_empty_message(backend):
    msg = Message(role=MessageRole.USER, parts=[TextPart(text="")])
    auth = backend.authenticate("test-key-A")
    from uuid import uuid4
    ctx = TaskContext(auth=auth, context_id="ctx-7")
    from a2a_protocol import A2AError
    with pytest.raises(A2AError):
        await backend.submit_task(msg, str(uuid4()), ctx)
