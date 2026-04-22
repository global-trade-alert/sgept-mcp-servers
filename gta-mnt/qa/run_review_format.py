"""Gold-standard regression harness for gta-mnt review-formatting output.

Runs the markdown formatters against checked-in fixtures and diffs the output
against `qa/standards/*.md`. Exits non-zero on any drift so it can gate CI if
wired up later.

First-run workflow
------------------
1. Add a fixture JSON under `qa/fixtures/`.
2. Wire it into `CASES` below.
3. Run with `--write-standards` once to seed `qa/standards/<case>.md`.
4. Commit the standard. Subsequent runs compare against it and fail on drift.

Intentionally no dependency on the DB or network. All inputs come from JSON
fixtures so this suite stays safe to run in any environment.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Callable

from gta_mnt.formatters import (
    format_step1_queue,
    format_issue_comment,
)


QA_DIR = Path(__file__).parent
FIXTURES = QA_DIR / "fixtures"
STANDARDS = QA_DIR / "standards"


def _format_step1_queue(data: dict) -> str:
    return format_step1_queue(data)


def _format_issue_comment(data: dict) -> str:
    return format_issue_comment(**data)


# (case_name, fixture_filename, formatter_fn)
CASES: list[tuple[str, str, Callable[[dict], str]]] = [
    ("step1_queue_small", "step1_queue_small.json", _format_step1_queue),
    ("step1_queue_empty", "step1_queue_empty.json", _format_step1_queue),
    ("issue_comment", "issue_comment.json", _format_issue_comment),
]


def run(write_standards: bool) -> int:
    failures: list[str] = []

    for case, fixture, fn in CASES:
        with (FIXTURES / fixture).open() as f:
            data = json.load(f)
        actual = fn(data)

        standard_path = STANDARDS / f"{case}.md"

        if write_standards or not standard_path.exists():
            standard_path.write_text(actual, encoding="utf-8")
            print(f"[seeded] {case}")
            continue

        expected = standard_path.read_text(encoding="utf-8")
        if actual == expected:
            print(f"[pass]   {case}")
        else:
            failures.append(case)
            diff = difflib.unified_diff(
                expected.splitlines(keepends=True),
                actual.splitlines(keepends=True),
                fromfile=f"standards/{case}.md",
                tofile=f"<live output: {case}>",
            )
            print(f"[fail]   {case}")
            sys.stdout.writelines(diff)

    if failures:
        print(f"\n{len(failures)} regression(s): {', '.join(failures)}")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument(
        "--write-standards",
        action="store_true",
        help="Overwrite qa/standards/*.md with current formatter output. Use on first run or after an intentional format change.",
    )
    args = ap.parse_args()
    return run(write_standards=args.write_standards)


if __name__ == "__main__":
    sys.exit(main())
