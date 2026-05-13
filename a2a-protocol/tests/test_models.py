"""A2A wire models."""

from __future__ import annotations

import json

from a2a_protocol import (
    Artifact,
    DataPart,
    FilePart,
    Message,
    MessageRole,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)
from a2a_protocol.models import (
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    data_message,
    new_context_id,
    new_task_id,
    text_message,
)


def test_text_message_roundtrip():
    m = text_message(MessageRole.USER, "hello")
    d = m.model_dump(mode="json", by_alias=True)
    assert d["role"] == "user"
    assert d["parts"][0]["kind"] == "text"
    assert d["parts"][0]["text"] == "hello"
    m2 = Message.model_validate(d)
    assert m2.text() == "hello"


def test_data_message_roundtrip():
    m = data_message(MessageRole.USER, {"scenario": "x", "horizon": "30d"})
    d = m.model_dump(mode="json", by_alias=True)
    assert d["parts"][0]["kind"] == "data"
    m2 = Message.model_validate(d)
    assert m2.data() == {"scenario": "x", "horizon": "30d"}


def test_message_part_discriminator():
    msg = Message(
        role=MessageRole.AGENT,
        parts=[
            TextPart(text="here is the result"),
            DataPart(data={"p": 0.18}),
        ],
    )
    serialized = msg.model_dump(mode="json", by_alias=True)
    kinds = [p["kind"] for p in serialized["parts"]]
    assert kinds == ["text", "data"]


def test_task_serialization_uses_camelcase():
    task_id = new_task_id()
    ctx_id = new_context_id()
    t = Task(
        id=task_id,
        context_id=ctx_id,
        status=TaskStatus(state=TaskState.WORKING),
    )
    d = t.model_dump(mode="json", by_alias=True)
    assert d["contextId"] == ctx_id
    assert d["status"]["state"] == "working"
    assert d["kind"] == "task"


def test_status_update_event_camelcase():
    ev = TaskStatusUpdateEvent(
        task_id="t1", context_id="c1",
        status=TaskStatus(state=TaskState.INPUT_REQUIRED),
        final=False,
    )
    d = ev.model_dump(mode="json", by_alias=True)
    assert d["taskId"] == "t1"
    assert d["contextId"] == "c1"
    assert d["kind"] == "status-update"
    assert d["status"]["state"] == "input-required"


def test_artifact_with_multiple_parts():
    a = Artifact(
        name="result",
        parts=[
            TextPart(text="briefing"),
            DataPart(data={"p_point": 0.18}),
        ],
    )
    d = a.model_dump(mode="json", by_alias=True)
    assert d["name"] == "result"
    assert len(d["parts"]) == 2
    assert d["parts"][0]["kind"] == "text"
    assert d["parts"][1]["kind"] == "data"
