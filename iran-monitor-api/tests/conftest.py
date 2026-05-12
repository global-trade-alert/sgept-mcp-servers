"""Pytest fixtures: a tmp-dir-scoped settings + DB for hermetic tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from iran_monitor_api import config, db


@pytest.fixture(autouse=True)
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Each test gets its own data dir, DB, keys dir, and settings."""
    monkeypatch.setenv("IRAN_API_BASE_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("IRAN_API_SIGNING_KEY_PATH", str(tmp_path / "keys" / "signing-key.bin"))
    monkeypatch.setenv("IRAN_API_SIGNING_PUB_KEY_PATH", str(tmp_path / "keys" / "signing-key.pub"))
    monkeypatch.setenv("IRAN_API_IRAN_MONITOR_REPO", str(tmp_path / "iran-monitor-fake"))
    monkeypatch.setenv(
        "IRAN_API_API_KEYS_JSON",
        json.dumps({"test-key-A": "test-org-A", "test-key-B": "test-org-B"}),
    )

    # Reset singletons so settings reload from env
    config.reset_settings_for_tests()
    from iran_monitor_api.api import auth as auth_mod
    auth_mod.reset_api_keys_cache()

    # Build a minimal fake iran-monitor repo
    fake = tmp_path / "iran-monitor-fake"
    (fake / "data" / "perspective-assessments" / "260512-1200").mkdir(parents=True)
    (fake / "data" / "probabilities.csv").write_text("timestamp,A,B1\n2026-05-12T12:00:00Z,0.1,0.2\n")
    (fake / "data" / "probabilities_v.csv").write_text("timestamp,A,V,B1\n2026-05-12T12:00:00Z,0.1,0.05,0.2\n")
    (fake / "data" / "tracking").mkdir(parents=True, exist_ok=True)
    (fake / "data" / "tracking" / "peripheral-watch-list.jsonl").write_text(
        '{"signal":"cyber","date":"2026-05-01"}\n'
    )
    (fake / "data" / "tracking" / "aggregation-state.json").write_text('{"method":"v1"}')
    (fake / "data" / "tracking" / "war-chronicle.md").write_text("# War chronicle\n")

    # Minimal .claude/agents/ for subagent tests
    agents_dir = fake / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    for name in [
        "tetlock-forecaster",
        "schelling-bargaining",
        "wack-strategic",
        "red-team-adversarial",
    ]:
        (agents_dir / f"{name}.md").write_text(
            f"---\nname: {name}\nmodel: sonnet\n---\n# Test agent {name}\n"
        )

    # Initialize DB fresh
    db.init_db()

    yield tmp_path

    config.reset_settings_for_tests()
