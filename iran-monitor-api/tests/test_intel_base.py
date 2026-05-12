"""Intelligence-base hash determinism + atomic seal."""

from __future__ import annotations

from pathlib import Path

from iran_monitor_api.intel_base import (
    build_manifest,
    compute_intel_base_hash,
    read_sealed_hash,
    seal,
)


def test_manifest_is_sorted_deterministically(isolated_env):
    repo = isolated_env / "iran-monitor-fake"
    m1 = build_manifest(repo)
    m2 = build_manifest(repo)
    assert m1 == m2
    paths = [p for p, _ in m1]
    assert paths == sorted(paths)


def test_hash_changes_when_content_changes(isolated_env):
    repo = isolated_env / "iran-monitor-fake"
    h1 = compute_intel_base_hash(repo)
    (repo / "data" / "probabilities.csv").write_text(
        "timestamp,A,B1\n2026-05-12T12:00:00Z,0.2,0.3\n"
    )
    h2 = compute_intel_base_hash(repo)
    assert h1 != h2


def test_hash_stable_when_content_unchanged(isolated_env):
    repo = isolated_env / "iran-monitor-fake"
    h1 = compute_intel_base_hash(repo)
    h2 = compute_intel_base_hash(repo)
    assert h1 == h2


def test_seal_writes_atomically(isolated_env):
    repo = isolated_env / "iran-monitor-fake"
    digest = seal(repo)
    sealed_file = repo / "data" / ".intel-base-hash"
    assert sealed_file.exists()
    assert sealed_file.read_text().strip() == digest
    assert digest == read_sealed_hash(repo)


def test_read_returns_none_when_unsealed(isolated_env):
    repo = isolated_env / "iran-monitor-fake"
    assert read_sealed_hash(repo) is None


def test_hash_changes_when_files_added(isolated_env):
    repo = isolated_env / "iran-monitor-fake"
    h1 = compute_intel_base_hash(repo)
    cycle = repo / "data" / "perspective-assessments" / "260512-1800"
    cycle.mkdir(parents=True)
    (cycle / "raw-intelligence.md").write_text("## New developments\n")
    h2 = compute_intel_base_hash(repo)
    assert h1 != h2
