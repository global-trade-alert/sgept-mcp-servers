"""Intelligence-base hash sealing.

Hash is SHA-256 over a sorted manifest of (relative_path, content_sha256) pairs.
Sealed at the end of the cron's Phase 6 (COMMIT) — after git push, the cron writes
`data/.intel-base-hash` atomically. Workers read this file at query start.

If the cron is mid-cycle, the file still points to the last fully-committed cycle.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

from .config import get_settings

# Relative paths under iran_monitor_repo that constitute the intelligence base.
# Globs against the repo root; the latest cycle's raw-intelligence.md is captured
# via the perspective-assessments tree (one subdir per cycle) — we hash all of it.
INTEL_BASE_GLOBS = [
    "data/probabilities.csv",
    "data/probabilities_v.csv",
    "data/tracking/peripheral-watch-list.jsonl",
    "data/tracking/aggregation-state.json",
    "data/tracking/war-chronicle.md",
    "data/briefings/**/*.md",
    "data/perspective-assessments/**/*.json",
    "data/perspective-assessments/**/raw-intelligence.md",
    "data/perspective-assessments/**/briefing-*.md",
]


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(repo_root: Path) -> list[tuple[str, str]]:
    """Sorted list of (relative_path, content_sha256). Missing files skipped."""
    seen: set[Path] = set()
    for glob in INTEL_BASE_GLOBS:
        for f in repo_root.glob(glob):
            if f.is_file():
                seen.add(f)
    items = []
    for f in sorted(seen):
        rel = f.relative_to(repo_root).as_posix()
        items.append((rel, _sha256_file(f)))
    return items


def compute_intel_base_hash(repo_root: Path) -> str:
    manifest = build_manifest(repo_root)
    h = hashlib.sha256()
    for rel, content_hash in manifest:
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(content_hash.encode("ascii"))
        h.update(b"\n")
    return "sha256:" + h.hexdigest()


def seal(repo_root: Path | None = None) -> str:
    """Atomic write to data/.intel-base-hash. Returns the new hash."""
    settings = get_settings()
    root = repo_root or settings.iran_monitor_repo
    digest = compute_intel_base_hash(root)
    target = root / "data" / ".intel-base-hash"
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(digest + "\n")
    os.replace(tmp, target)
    return digest


def read_sealed_hash(repo_root: Path | None = None) -> str | None:
    settings = get_settings()
    root = repo_root or settings.iran_monitor_repo
    target = root / "data" / ".intel-base-hash"
    if not target.exists():
        return None
    return target.read_text().strip()


# ── CLI ───────────────────────────────────────────────────────────────────────


def seal_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Compute and seal intelligence-base hash. Call from cron Phase 6."
    )
    parser.add_argument("--repo", type=Path, default=None, help="iran-monitor repo root")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print hash without writing the seal"
    )
    args = parser.parse_args()
    settings = get_settings()
    root = args.repo or settings.iran_monitor_repo
    if not root.exists():
        print(f"ERROR: repo root not found: {root}", file=sys.stderr)
        sys.exit(2)
    if args.dry_run:
        print(compute_intel_base_hash(root))
        return
    digest = seal(root)
    print(f"Sealed {root}/data/.intel-base-hash = {digest}")
