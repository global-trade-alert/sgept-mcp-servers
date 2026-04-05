"""Tests for the METIS workflow engine."""

import tempfile
from pathlib import Path

import pytest

from metis_mcp.audit import AuditLog
from metis_mcp.engine import (
    EngineError,
    InstanceNotFoundError,
    InvalidAdvanceError,
    WorkflowEngine,
    WorkflowNotFoundError,
)

WORKFLOWS_DIR = Path(__file__).parent / "workflows"


@pytest.fixture
def audit_log(tmp_path):
    """Create a temporary audit log."""
    return AuditLog(audit_dir=tmp_path / "audit")


@pytest.fixture
def engine(audit_log):
    """Create engine with test workflows loaded."""
    eng = WorkflowEngine(audit_log=audit_log)
    count = eng.load_workflows(WORKFLOWS_DIR)
    assert count >= 1, "Expected at least 1 workflow to load"
    return eng


class TestWorkflowLoading:
    """Test workflow definition loading."""

    def test_load_workflows_from_directory(self, engine):
        workflows = engine.list_workflows()
        assert len(workflows) >= 1
        ids = [w["id"] for w in workflows]
        assert "test-two-step" in ids

    def test_workflow_has_correct_structure(self, engine):
        workflows = engine.list_workflows()
        two_step = next(w for w in workflows if w["id"] == "test-two-step")
        assert two_step["name"] == "Test Two-Step Workflow"
        assert two_step["version"] == 1
        assert two_step["step_count"] == 2
        assert two_step["steps"][0]["id"] == "step_one"
        assert two_step["steps"][1]["id"] == "step_two"

    def test_load_nonexistent_directory(self, audit_log):
        eng = WorkflowEngine(audit_log=audit_log)
        with pytest.raises(EngineError, match="does not exist"):
            eng.load_workflows("/nonexistent/path")


class TestWorkflowStart:
    """Test starting workflow instances."""

    def test_start_workflow_creates_instance(self, engine):
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        assert instance.instance_id is not None
        assert instance.workflow_id == "test-two-step"
        assert instance.status.value == "running"
        assert instance.current_step_id == "step_one"

    def test_start_workflow_sets_step_states(self, engine):
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        assert instance.step_states["step_one"].status.value == "in_progress"
        assert instance.step_states["step_two"].status.value == "pending"

    def test_start_workflow_validates_inputs(self, engine):
        with pytest.raises(InvalidAdvanceError, match="Missing required inputs"):
            engine.start_workflow("test-two-step", {})

    def test_start_nonexistent_workflow(self, engine):
        with pytest.raises(WorkflowNotFoundError, match="not found"):
            engine.start_workflow("nonexistent", {"brief": "test"})


class TestWorkflowAdvance:
    """Test advancing through workflow steps."""

    def test_advance_step_one_with_valid_output(self, engine):
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        result = engine.advance(instance.instance_id, {"result": "step one done"})

        assert result["status"] == "advanced"
        assert result["completed_step"] == "step_one"
        assert result["current_step"]["id"] == "step_two"
        assert result["current_step"]["actor"] == "agent:general"

    def test_advance_step_two_completes_workflow(self, engine):
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        engine.advance(instance.instance_id, {"result": "step one done"})
        result = engine.advance(
            instance.instance_id, {"final_output": "all done"}
        )

        assert result["status"] == "completed"
        assert result["workflow_id"] == "test-two-step"

    def test_full_workflow_completion(self, engine):
        """End-to-end: start, advance through both steps, verify completion."""
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        iid = instance.instance_id

        # Verify initial state
        state = engine.get_state(iid)
        assert state["status"] == "running"
        assert state["current_step_id"] == "step_one"

        # Advance step 1
        result1 = engine.advance(iid, {"result": "step one done"})
        assert result1["status"] == "advanced"

        state = engine.get_state(iid)
        assert state["current_step_id"] == "step_two"
        assert state["step_states"]["step_one"]["status"] == "completed"
        assert state["step_states"]["step_two"]["status"] == "in_progress"

        # Advance step 2
        result2 = engine.advance(iid, {"final_output": "all done"})
        assert result2["status"] == "completed"

        state = engine.get_state(iid)
        assert state["status"] == "completed"
        assert state["step_states"]["step_two"]["status"] == "completed"


class TestGateFailure:
    """Test quality gate rejection."""

    def test_gate_rejects_empty_output(self, engine):
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        result = engine.advance(instance.instance_id, {})

        assert result["status"] == "gate_failed"
        assert result["step_id"] == "step_one"
        assert len(result["errors"]) > 0
        assert "Missing required" in result["errors"][0]

    def test_gate_rejects_empty_string(self, engine):
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        result = engine.advance(instance.instance_id, {"result": ""})

        assert result["status"] == "gate_failed"
        assert "Empty required" in result["errors"][0]

    def test_gate_rejects_none_value(self, engine):
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        result = engine.advance(instance.instance_id, {"result": None})

        assert result["status"] == "gate_failed"
        assert "Missing required" in result["errors"][0]

    def test_gate_failure_does_not_advance(self, engine):
        """After gate failure, instance stays on the same step."""
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        engine.advance(instance.instance_id, {})  # fails gate

        state = engine.get_state(instance.instance_id)
        assert state["status"] == "running"
        assert state["current_step_id"] == "step_one"
        assert state["step_states"]["step_one"]["status"] == "in_progress"

    def test_can_retry_after_gate_failure(self, engine):
        """After gate failure, can retry with valid output."""
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        engine.advance(instance.instance_id, {})  # fails gate
        result = engine.advance(
            instance.instance_id, {"result": "valid output"}
        )

        assert result["status"] == "advanced"


class TestInstanceManagement:
    """Test instance listing and state retrieval."""

    def test_get_state_returns_full_state(self, engine):
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        state = engine.get_state(instance.instance_id)

        assert state["instance_id"] == instance.instance_id
        assert state["workflow_id"] == "test-two-step"
        assert state["workflow_name"] == "Test Two-Step Workflow"
        assert state["status"] == "running"
        assert "step_one" in state["step_states"]
        assert "step_two" in state["step_states"]
        assert state["inputs"] == {"brief": "test brief"}
        assert "correlation_id" in state

    def test_get_state_nonexistent_instance(self, engine):
        with pytest.raises(InstanceNotFoundError):
            engine.get_state("nonexistent-id")

    def test_list_instances_all(self, engine):
        engine.start_workflow("test-two-step", {"brief": "one"})
        engine.start_workflow("test-two-step", {"brief": "two"})

        instances = engine.list_instances()
        assert len(instances) == 2

    def test_list_instances_filter_by_status(self, engine):
        i1 = engine.start_workflow("test-two-step", {"brief": "one"})
        i2 = engine.start_workflow("test-two-step", {"brief": "two"})

        # Complete i1
        engine.advance(i1.instance_id, {"result": "done"})
        engine.advance(i1.instance_id, {"final_output": "done"})

        running = engine.list_instances(status="running")
        completed = engine.list_instances(status="completed")

        assert len(running) == 1
        assert running[0]["instance_id"] == i2.instance_id
        assert len(completed) == 1
        assert completed[0]["instance_id"] == i1.instance_id

    def test_list_instances_filter_by_workflow(self, engine):
        engine.start_workflow("test-two-step", {"brief": "one"})

        matches = engine.list_instances(workflow_id="test-two-step")
        no_matches = engine.list_instances(workflow_id="nonexistent")

        assert len(matches) == 1
        assert len(no_matches) == 0

    def test_advance_nonexistent_instance(self, engine):
        with pytest.raises(InstanceNotFoundError):
            engine.advance("nonexistent-id", {"result": "test"})

    def test_advance_completed_workflow(self, engine):
        instance = engine.start_workflow("test-two-step", {"brief": "test"})
        engine.advance(instance.instance_id, {"result": "done"})
        engine.advance(instance.instance_id, {"final_output": "done"})

        with pytest.raises(InvalidAdvanceError, match="Cannot advance"):
            engine.advance(instance.instance_id, {"extra": "output"})


class TestAuditLog:
    """Test audit trail generation."""

    def test_audit_log_captures_all_events(self, engine, audit_log):
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        engine.advance(instance.instance_id, {"result": "step one done"})
        engine.advance(instance.instance_id, {"final_output": "all done"})

        entries = audit_log.read_all()
        events = [e["event"] for e in entries]

        assert "workflow_started" in events
        assert "gate_passed" in events
        assert "step_advanced" in events
        assert "workflow_completed" in events

    def test_audit_log_captures_gate_failure(self, engine, audit_log):
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        engine.advance(instance.instance_id, {})  # gate fails

        entries = audit_log.read_all()
        events = [e["event"] for e in entries]

        assert "gate_failed" in events

    def test_audit_entries_have_correlation_id(self, engine, audit_log):
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        entries = audit_log.read_all()

        correlation_ids = set(e["correlation_id"] for e in entries)
        assert len(correlation_ids) == 1  # all same correlation ID
        assert "" not in correlation_ids  # not empty

    def test_audit_entries_have_timestamps(self, engine, audit_log):
        engine.start_workflow("test-two-step", {"brief": "test brief"})
        entries = audit_log.read_all()

        for entry in entries:
            assert "timestamp" in entry
            assert "T" in entry["timestamp"]  # ISO format

    def test_audit_entries_have_instance_id(self, engine, audit_log):
        instance = engine.start_workflow("test-two-step", {"brief": "test brief"})
        entries = audit_log.read_all()

        for entry in entries:
            assert entry["instance_id"] == instance.instance_id
