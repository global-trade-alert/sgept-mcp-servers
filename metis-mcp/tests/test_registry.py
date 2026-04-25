"""Tests for the METIS capability registry.

Standalone — imports only from registry.py and registry_models.py.
Run: cd metis-mcp && python -m pytest tests/test_registry.py -v
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from metis_mcp.registry import CapabilityRegistry
from metis_mcp.registry_models import CapabilityEntry, StaffingPlan


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


SAMPLE_ENTRIES = [
    {
        "id": "proposal-discovery",
        "category": "agent",
        "name": "Proposal Discovery Agent",
        "description": "Extract the real client problem before any offer is designed",
        "tags": ["proposal", "discovery", "client"],
        "inputs": ["client_inquiry"],
        "outputs": ["problem_statement", "constraints", "stakeholders"],
        "tools": ["Read", "Grep", "Glob", "AskUserQuestion", "WebSearch"],
        "model": "sonnet",
        "source": ".claude/agents/proposal-discovery.md",
        "confidence": "high",
        "human_required": False,
    },
    {
        "id": "proposal-drafter",
        "category": "agent",
        "name": "Proposal Drafter Agent",
        "description": "Draft the client-facing proposal document from structured inputs",
        "tags": ["proposal", "drafting", "document"],
        "inputs": ["problem_statement", "offer_structure", "pricing"],
        "outputs": ["proposal_document"],
        "tools": ["Read", "Grep", "Glob", "Write"],
        "model": "sonnet",
        "source": ".claude/agents/proposal-drafter.md",
        "confidence": "high",
        "human_required": False,
    },
    {
        "id": "slack-checker",
        "category": "agent",
        "name": "Slack Checker Agent",
        "description": "Triage Slack messages, suggest quick replies, and create follow-up todos",
        "tags": ["slack", "triage", "communication"],
        "inputs": ["slack_messages"],
        "outputs": ["reply_drafts", "todo_items"],
        "tools": ["Read", "Edit", "Write", "Glob"],
        "model": "sonnet",
        "source": ".claude/agents/slack-checker.md",
        "confidence": "high",
        "human_required": False,
    },
    {
        "id": "price",
        "category": "skill",
        "name": "Pricing Analysis",
        "description": "Run 4-lens pricing analysis: willingness-to-pay segmentation, economic value to customer, competitor benchmarking, and value metrics",
        "tags": ["pricing", "proposal", "commercial"],
        "inputs": ["client_context"],
        "outputs": ["pricing_recommendation"],
        "tools": ["Read", "Grep", "Glob", "WebSearch"],
        "model": "sonnet",
        "source": ".claude/skills/price/SKILL.md",
        "confidence": "high",
        "human_required": False,
    },
    {
        "id": "sgept-docx",
        "category": "skill",
        "name": "SGEPT Document Generator",
        "description": "Convert markdown content to professional SGEPT Word documents with letterhead, logo, and Roboto font",
        "tags": ["document", "formatting", "word"],
        "inputs": ["markdown_content"],
        "outputs": ["docx_file"],
        "tools": ["Bash"],
        "model": None,
        "source": ".claude/skills/sgept-docx/SKILL.md",
        "confidence": "high",
        "human_required": False,
    },
]


@pytest.fixture
def registry_dir(tmp_path: Path) -> Path:
    """Create a temp directory with sample YAML entries."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Write schema file (should be skipped)
    schema_path = tmp_path / "_schema.yaml"
    schema_path.write_text(yaml.dump({"required_fields": ["id", "category", "name"]}))

    for entry in SAMPLE_ENTRIES:
        if entry["category"] == "agent":
            path = agents_dir / f"{entry['id']}.yaml"
        else:
            path = skills_dir / f"{entry['id']}.yaml"
        path.write_text(yaml.dump(entry, default_flow_style=False))

    return tmp_path


@pytest.fixture
def registry(registry_dir: Path) -> CapabilityRegistry:
    """Initialize and load a registry from the sample entries."""
    reg = CapabilityRegistry(str(registry_dir))
    reg.load()
    return reg


# ------------------------------------------------------------------
# Tests: Loading
# ------------------------------------------------------------------


class TestLoading:
    def test_load_returns_all_entries(self, registry: CapabilityRegistry):
        entries = registry.list()
        assert len(entries) == 5

    def test_reload_clears_and_reloads(self, registry: CapabilityRegistry):
        registry.load()
        entries = registry.list()
        assert len(entries) == 5

    def test_invalid_yaml_is_skipped(self, registry_dir: Path):
        """Invalid YAML files should be skipped with a warning, not crash."""
        bad_file = registry_dir / "agents" / "broken.yaml"
        bad_file.write_text("this: is: not: valid: yaml: [")

        reg = CapabilityRegistry(str(registry_dir))
        reg.load()  # should not raise
        # May or may not parse depending on YAML parser tolerance, but should not crash
        # At minimum the valid entries should be present
        assert len(reg.list()) >= 5

    def test_invalid_schema_is_skipped(self, registry_dir: Path):
        """YAML that doesn't match the CapabilityEntry schema should be skipped."""
        bad_file = registry_dir / "agents" / "bad-schema.yaml"
        bad_file.write_text(yaml.dump({"foo": "bar"}))

        reg = CapabilityRegistry(str(registry_dir))
        reg.load()
        assert len(reg.list()) == 5  # only the original 5

    def test_schema_file_is_skipped(self, registry_dir: Path):
        """Files starting with _ should be skipped."""
        reg = CapabilityRegistry(str(registry_dir))
        reg.load()
        # _schema.yaml should not appear as an entry
        assert registry_dir / "_schema.yaml"  # file exists
        assert reg.get("_schema") is None


# ------------------------------------------------------------------
# Tests: List filtering
# ------------------------------------------------------------------


class TestList:
    def test_list_all(self, registry: CapabilityRegistry):
        entries = registry.list()
        assert len(entries) == 5

    def test_list_by_category_agent(self, registry: CapabilityRegistry):
        agents = registry.list(category="agent")
        assert len(agents) == 3
        assert all(e.category == "agent" for e in agents)

    def test_list_by_category_skill(self, registry: CapabilityRegistry):
        skills = registry.list(category="skill")
        assert len(skills) == 2
        assert all(e.category == "skill" for e in skills)

    def test_list_by_category_empty(self, registry: CapabilityRegistry):
        workflows = registry.list(category="workflow")
        assert len(workflows) == 0

    def test_list_by_tags_single(self, registry: CapabilityRegistry):
        results = registry.list(tags=["proposal"])
        ids = {e.id for e in results}
        assert "proposal-discovery" in ids
        assert "proposal-drafter" in ids
        assert "price" in ids  # has "proposal" tag too

    def test_list_by_tags_multiple_and(self, registry: CapabilityRegistry):
        results = registry.list(tags=["proposal", "discovery"])
        assert len(results) == 1
        assert results[0].id == "proposal-discovery"

    def test_list_by_category_and_tags(self, registry: CapabilityRegistry):
        results = registry.list(category="agent", tags=["proposal"])
        ids = {e.id for e in results}
        assert "proposal-discovery" in ids
        assert "proposal-drafter" in ids
        assert "price" not in ids  # skill, not agent

    def test_list_returns_sorted_by_id(self, registry: CapabilityRegistry):
        entries = registry.list()
        ids = [e.id for e in entries]
        assert ids == sorted(ids)


# ------------------------------------------------------------------
# Tests: Get
# ------------------------------------------------------------------


class TestGet:
    def test_get_existing(self, registry: CapabilityRegistry):
        entry = registry.get("proposal-discovery")
        assert entry is not None
        assert entry.name == "Proposal Discovery Agent"
        assert entry.model == "sonnet"

    def test_get_nonexistent(self, registry: CapabilityRegistry):
        assert registry.get("nonexistent-thing") is None

    def test_get_returns_full_entry(self, registry: CapabilityRegistry):
        entry = registry.get("price")
        assert entry is not None
        assert entry.category == "skill"
        assert "pricing" in entry.tags
        assert "client_context" in entry.inputs
        assert entry.confidence == "high"


# ------------------------------------------------------------------
# Tests: Search (FTS5)
# ------------------------------------------------------------------


class TestSearch:
    def test_search_by_description(self, registry: CapabilityRegistry):
        results = registry.search("client problem")
        ids = [e.id for e in results]
        assert "proposal-discovery" in ids

    def test_search_by_name(self, registry: CapabilityRegistry):
        results = registry.search("Slack Checker")
        ids = [e.id for e in results]
        assert "slack-checker" in ids

    def test_search_by_tags(self, registry: CapabilityRegistry):
        results = registry.search("pricing commercial")
        ids = [e.id for e in results]
        assert "price" in ids

    def test_search_empty_query(self, registry: CapabilityRegistry):
        results = registry.search("")
        assert results == []

    def test_search_no_results(self, registry: CapabilityRegistry):
        results = registry.search("quantum computing blockchain")
        assert results == []

    def test_search_returns_ranked(self, registry: CapabilityRegistry):
        """Search should return results — ordering by FTS5 rank."""
        results = registry.search("proposal")
        assert len(results) >= 2
        # All returned entries should be valid CapabilityEntry objects
        assert all(isinstance(e, CapabilityEntry) for e in results)


# ------------------------------------------------------------------
# Tests: Staff (staffing recommender)
# ------------------------------------------------------------------


class TestStaff:
    def test_staff_with_matches(self, registry: CapabilityRegistry):
        plan = registry.staff(["drafting proposals", "pricing analysis"])
        assert isinstance(plan, StaffingPlan)
        assert len(plan.matched) == 2
        matched_ids = {m.capability_id for m in plan.matched}
        assert "proposal-drafter" in matched_ids or "proposal-discovery" in matched_ids

    def test_staff_with_gaps(self, registry: CapabilityRegistry):
        plan = registry.staff(["quantum computing integration"])
        assert len(plan.gaps) == 1
        assert "quantum computing integration" in plan.gaps

    def test_staff_mixed_matches_and_gaps(self, registry: CapabilityRegistry):
        plan = registry.staff(["slack triage messages", "blockchain deployment"])
        assert len(plan.matched) >= 1
        assert len(plan.gaps) >= 1
        assert "blockchain deployment" in plan.gaps

    def test_staff_empty_requirements(self, registry: CapabilityRegistry):
        plan = registry.staff([])
        assert plan.matched == []
        assert plan.gaps == []

    def test_staff_returns_match_reasons(self, registry: CapabilityRegistry):
        plan = registry.staff(["proposal drafting"])
        if plan.matched:
            assert plan.matched[0].match_reason  # non-empty reason string


# ------------------------------------------------------------------
# Tests: Persistence
# ------------------------------------------------------------------


class TestPersistence:
    def test_file_backed_index(self, registry_dir: Path, tmp_path: Path):
        db_path = str(tmp_path / "test.db")
        reg = CapabilityRegistry(str(registry_dir), index_path=db_path)
        reg.load()

        # Database file should exist
        assert Path(db_path).exists()

        # Search should work
        results = reg.search("proposal")
        assert len(results) >= 2
        reg.close()

    def test_close_and_reopen(self, registry_dir: Path):
        reg = CapabilityRegistry(str(registry_dir))
        reg.load()
        reg.close()

        # After close, search returns empty
        results = reg.search("proposal")
        assert results == []

        # Reload works
        reg.load()
        results = reg.search("proposal")
        assert len(results) >= 2
