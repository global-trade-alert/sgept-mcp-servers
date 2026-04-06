"""Tests for METIS workflow enforcement state and hook script."""

import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from metis_mcp.audit import AuditLog
from metis_mcp.engine import WorkflowEngine

WORKFLOWS_DIR = Path(__file__).parent / "workflows"
HOOK_SCRIPT = (
    Path(__file__).parent.parent.parent.parent.parent.parent
    / "claude-setup"
    / "cc-os"
    / "scripts"
    / "gate-metis-workflow.sh"
)


@pytest.fixture
def audit_log(tmp_path):
    return AuditLog(audit_dir=tmp_path / "audit")


@pytest.fixture
def enforcement_dir(tmp_path):
    d = tmp_path / "enforcement"
    d.mkdir()
    return d


@pytest.fixture
def engine_with_enforcement(audit_log, enforcement_dir):
    """Create engine with METIS_ENFORCEMENT_DIR set."""
    old_val = os.environ.get("METIS_ENFORCEMENT_DIR")
    os.environ["METIS_ENFORCEMENT_DIR"] = str(enforcement_dir)
    eng = WorkflowEngine(audit_log=audit_log)
    eng.load_workflows(WORKFLOWS_DIR)
    yield eng
    if old_val is None:
        os.environ.pop("METIS_ENFORCEMENT_DIR", None)
    else:
        os.environ["METIS_ENFORCEMENT_DIR"] = old_val


@pytest.fixture
def engine_no_enforcement(audit_log):
    """Create engine without METIS_ENFORCEMENT_DIR set."""
    old_val = os.environ.pop("METIS_ENFORCEMENT_DIR", None)
    eng = WorkflowEngine(audit_log=audit_log)
    eng.load_workflows(WORKFLOWS_DIR)
    yield eng
    if old_val is not None:
        os.environ["METIS_ENFORCEMENT_DIR"] = old_val


def _state_file(enforcement_dir, instance_id):
    """Helper to get the namespaced enforcement state file path."""
    return enforcement_dir / f".metis-workflow-state-{instance_id}.json"


class TestEnforcementStateWrite:
    """Test write_enforcement_state produces correct JSON."""

    def test_start_workflow_writes_state_file(self, engine_with_enforcement, enforcement_dir):
        instance = engine_with_enforcement.start_workflow(
            "test-enforced", {"topic": "trade policy"}
        )
        state_file = _state_file(enforcement_dir, instance.instance_id)
        assert state_file.exists()

        state = json.loads(state_file.read_text())
        assert state["instance_id"] == instance.instance_id
        assert state["workflow_id"] == "test-enforced"
        assert state["current_step_id"] == "research"
        assert state["current_step_actor"] == "agent:researcher"
        assert state["permitted_tools"] == ["Read", "Grep", "Glob", "WebSearch"]
        assert state["blocked_tools"] == []
        assert state["enforce"] is True

    def test_advance_updates_state_file(self, engine_with_enforcement, enforcement_dir):
        instance = engine_with_enforcement.start_workflow(
            "test-enforced", {"topic": "trade policy"}
        )
        engine_with_enforcement.advance(
            instance.instance_id, {"findings": "important findings"}
        )

        state_file = _state_file(enforcement_dir, instance.instance_id)
        state = json.loads(state_file.read_text())
        assert state["current_step_id"] == "draft"
        assert state["current_step_actor"] == "agent:drafter"
        assert state["permitted_tools"] == ["Read", "Grep", "Glob", "Write", "Edit"]
        assert state["enforce"] is True

    def test_completion_clears_state_file(self, engine_with_enforcement, enforcement_dir):
        instance = engine_with_enforcement.start_workflow(
            "test-enforced", {"topic": "trade policy"}
        )
        engine_with_enforcement.advance(
            instance.instance_id, {"findings": "findings"}
        )
        engine_with_enforcement.advance(
            instance.instance_id, {"document": "draft doc"}
        )
        engine_with_enforcement.advance(
            instance.instance_id, {"approval": "approved"}
        )

        state_file = _state_file(enforcement_dir, instance.instance_id)
        assert not state_file.exists()

    def test_no_enforcement_dir_writes_nothing(self, engine_no_enforcement):
        instance = engine_no_enforcement.start_workflow(
            "test-enforced", {"topic": "trade policy"}
        )
        result = engine_no_enforcement.write_enforcement_state(instance.instance_id)
        assert result is None

    def test_step_without_permitted_tools_sets_enforce_false(
        self, engine_with_enforcement, enforcement_dir
    ):
        """The review step has no permitted_tools -> enforce=false."""
        instance = engine_with_enforcement.start_workflow(
            "test-enforced", {"topic": "trade policy"}
        )
        engine_with_enforcement.advance(
            instance.instance_id, {"findings": "findings"}
        )
        engine_with_enforcement.advance(
            instance.instance_id, {"document": "draft doc"}
        )

        state_file = _state_file(enforcement_dir, instance.instance_id)
        state = json.loads(state_file.read_text())
        assert state["current_step_id"] == "review"
        assert state["permitted_tools"] == []
        assert state["enforce"] is False

    def test_explicit_enforcement_dir_overrides_env(self, engine_with_enforcement, tmp_path):
        """Passing enforcement_dir explicitly overrides the env var."""
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()

        instance = engine_with_enforcement.start_workflow(
            "test-enforced", {"topic": "trade policy"}
        )
        result = engine_with_enforcement.write_enforcement_state(
            instance.instance_id, enforcement_dir=custom_dir
        )
        assert result == custom_dir / f".metis-workflow-state-{instance.instance_id}.json"
        assert result.exists()

    def test_workflow_without_permitted_tools_not_enforced(
        self, engine_with_enforcement, enforcement_dir
    ):
        """test-two-step has no permitted_tools on any step -> enforce=false."""
        instance = engine_with_enforcement.start_workflow(
            "test-two-step", {"brief": "test brief"}
        )
        state_file = _state_file(enforcement_dir, instance.instance_id)
        state = json.loads(state_file.read_text())
        assert state["enforce"] is False


class TestPermittedToolsParsing:
    """Test that permitted_tools are correctly parsed from YAML."""

    def test_enforced_workflow_has_permitted_tools(self, engine_with_enforcement):
        workflows = engine_with_enforcement.list_workflows()
        enforced = next(w for w in workflows if w["id"] == "test-enforced")
        assert enforced["step_count"] == 3

    def test_step_def_has_permitted_tools(self, engine_with_enforcement):
        wf = engine_with_enforcement._workflows["test-enforced"]
        research = wf.get_step("research")
        assert research.permitted_tools == ["Read", "Grep", "Glob", "WebSearch"]

        draft = wf.get_step("draft")
        assert draft.permitted_tools == ["Read", "Grep", "Glob", "Write", "Edit"]

        review = wf.get_step("review")
        assert review.permitted_tools == []

    def test_legacy_workflow_has_empty_permitted_tools(self, engine_with_enforcement):
        wf = engine_with_enforcement._workflows["test-two-step"]
        for step in wf.steps:
            assert step.permitted_tools == []


@pytest.mark.skipif(
    not HOOK_SCRIPT.exists(),
    reason=f"Hook script not found at {HOOK_SCRIPT}",
)
class TestHookScript:
    """Test the gate-metis-workflow.sh hook script."""

    def _run_hook(self, tool_name: str, state_file_content: dict | None, project_dir: str) -> subprocess.CompletedProcess:
        """Run the hook script with given tool input and state."""
        hook_input = json.dumps({"tool_name": tool_name, "tool_input": {}})

        if state_file_content is not None:
            claude_dir = Path(project_dir) / ".claude"
            claude_dir.mkdir(parents=True, exist_ok=True)
            # Use fresh timestamp so staleness check doesn't filter it out
            state_file_content = dict(state_file_content)
            state_file_content["step_started_at"] = datetime.now(timezone.utc).isoformat()
            instance_id = state_file_content.get("instance_id", "test-123")
            state_path = claude_dir / f".metis-workflow-state-{instance_id}.json"
            state_path.write_text(json.dumps(state_file_content))

        env = os.environ.copy()
        env["CLAUDE_PROJECT_DIR"] = project_dir

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            input=hook_input,
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        return result

    def test_no_state_file_allows_all(self, tmp_path):
        result = self._run_hook("Write", None, str(tmp_path))
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_enforce_false_allows_all(self, tmp_path):
        state = {
            "instance_id": "test-123",
            "workflow_id": "test",
            "current_step_id": "step1",
            "current_step_actor": "agent:test",
            "permitted_tools": ["Read"],
            "blocked_tools": [],
            "step_started_at": "2026-04-06T00:00:00Z",
            "enforce": False,
        }
        result = self._run_hook("Write", state, str(tmp_path))
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_universal_tools_always_allowed(self, tmp_path):
        state = {
            "instance_id": "test-123",
            "workflow_id": "test",
            "current_step_id": "step1",
            "current_step_actor": "agent:test",
            "permitted_tools": [],
            "blocked_tools": ["Read"],
            "step_started_at": "2026-04-06T00:00:00Z",
            "enforce": True,
        }
        # Universal tools bypass everything
        for tool in ["Read", "Grep", "Glob", "Bash", "Agent"]:
            result = self._run_hook(tool, state, str(tmp_path))
            assert result.returncode == 0
            assert "deny" not in result.stdout, f"{tool} should be universal-allowed"

    def test_metis_tools_always_allowed(self, tmp_path):
        state = {
            "instance_id": "test-123",
            "workflow_id": "test",
            "current_step_id": "step1",
            "current_step_actor": "agent:test",
            "permitted_tools": ["Write"],
            "blocked_tools": [],
            "step_started_at": "2026-04-06T00:00:00Z",
            "enforce": True,
        }
        result = self._run_hook("mcp__metis__advance", state, str(tmp_path))
        assert result.returncode == 0
        assert "deny" not in result.stdout

    def test_permitted_tool_allowed(self, tmp_path):
        state = {
            "instance_id": "test-123",
            "workflow_id": "test",
            "current_step_id": "research",
            "current_step_actor": "agent:test",
            "permitted_tools": ["Write", "Edit", "WebSearch"],
            "blocked_tools": [],
            "step_started_at": "2026-04-06T00:00:00Z",
            "enforce": True,
        }
        result = self._run_hook("Write", state, str(tmp_path))
        assert result.returncode == 0
        assert "deny" not in result.stdout

    def test_blocked_tool_denied(self, tmp_path):
        state = {
            "instance_id": "test-123",
            "workflow_id": "test",
            "current_step_id": "research",
            "current_step_actor": "agent:test",
            "permitted_tools": ["Write"],
            "blocked_tools": ["mcp__google-ceo__gmail_send"],
            "step_started_at": "2026-04-06T00:00:00Z",
            "enforce": True,
        }
        result = self._run_hook("mcp__google-ceo__gmail_send", state, str(tmp_path))
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "METIS WORKFLOW ENFORCEMENT" in output["hookSpecificOutput"]["permissionDecisionReason"]

    def test_unlisted_tool_soft_allowed_with_warning(self, tmp_path):
        state = {
            "instance_id": "test-123",
            "workflow_id": "test",
            "current_step_id": "research",
            "current_step_actor": "agent:test",
            "permitted_tools": ["Write", "Edit"],
            "blocked_tools": [],
            "step_started_at": "2026-04-06T00:00:00Z",
            "enforce": True,
        }
        result = self._run_hook("WebFetch", state, str(tmp_path))
        assert result.returncode == 0
        # Should NOT block (soft enforcement)
        assert "deny" not in result.stdout
        # Should warn on stderr
        assert "METIS WORKFLOW WARNING" in result.stderr

    def test_empty_tool_name_passes_through(self, tmp_path):
        hook_input = json.dumps({"tool_name": "", "tool_input": {}})
        env = os.environ.copy()
        env["CLAUDE_PROJECT_DIR"] = str(tmp_path)
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            input=hook_input,
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""
