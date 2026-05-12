"""Synthesize codex + gemini reviews into a final spike QA verdict.

Replicates the synthesis step from /advisory-round in a compact form:
- Reads codex-review.md + gemini-review.md
- Extracts each reviewer's verdict (PASS/FAIL) and key findings
- Cross-references findings: where both reviewers agree (ACCEPT), where
  one flags and the other doesn't (DEFER + investigation note), where
  both reject the artifact (REJECT)
- Outputs spike-qa-synthesis.md with an explicit go/no-go for Phase 1
  production deploy

Usage:
    uv run python spike/synthesize-qa.py <RUN_TS>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def extract_verdict(text: str) -> str:
    """Best-effort PASS/FAIL extraction. Returns 'PASS', 'FAIL', or 'UNCLEAR'."""
    # Look for explicit verdict lines
    for line in text.splitlines():
        s = line.strip()
        if re.match(r"^(verdict|summary)\s*[:\-]", s, re.IGNORECASE):
            if "PASS" in s.upper():
                return "PASS"
            if "FAIL" in s.upper():
                return "FAIL"
        # Or a line that starts with PASS/FAIL
        m = re.match(r"^\**\s*(PASS|FAIL)\b", s)
        if m:
            return m.group(1).upper()
    # Heuristic: count PASS vs FAIL mentions
    upper = text.upper()
    p = upper.count("PASS")
    f = upper.count("FAIL")
    if p > f * 2:
        return "PASS"
    if f > p * 2:
        return "FAIL"
    return "UNCLEAR"


def extract_findings(text: str, max_n: int = 10) -> list[str]:
    """Pull bullet-style findings or numbered points. Returns up to max_n."""
    findings = []
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^[-*•]\s+(.{30,})", s)
        if m:
            findings.append(m.group(1).strip())
        m = re.match(r"^\d+\.\s+(.{30,})", s)
        if m:
            findings.append(m.group(1).strip())
    return findings[:max_n]


def render(run_ts: str, codex_text: str, gemini_text: str) -> str:
    codex_verdict = extract_verdict(codex_text)
    gemini_verdict = extract_verdict(gemini_text)
    codex_findings = extract_findings(codex_text)
    gemini_findings = extract_findings(gemini_text)

    # Cross-reference: rough text similarity (sub-phrase containment, case-insens.)
    def overlaps(a: str, b: str) -> bool:
        a_l = a.lower()
        b_l = b.lower()
        # Strip leading bold/emphasis chars
        a_l = re.sub(r"^\**", "", a_l).strip()
        b_l = re.sub(r"^\**", "", b_l).strip()
        # Tokenize ~ first 5 substantive words
        a_tokens = [w for w in re.findall(r"\w{4,}", a_l)][:5]
        b_tokens = [w for w in re.findall(r"\w{4,}", b_l)][:5]
        if not a_tokens or not b_tokens:
            return False
        common = set(a_tokens) & set(b_tokens)
        return len(common) >= 3

    shared = []
    codex_only = []
    gemini_only = list(gemini_findings)
    for cf in codex_findings:
        match = next((gf for gf in gemini_only if overlaps(cf, gf)), None)
        if match:
            shared.append((cf, match))
            gemini_only.remove(match)
        else:
            codex_only.append(cf)

    # Build overall verdict
    if codex_verdict == "PASS" and gemini_verdict == "PASS":
        overall = "PASS"
    elif codex_verdict == "FAIL" or gemini_verdict == "FAIL":
        overall = "FAIL"
    else:
        overall = "MIXED — needs human review"

    parts = [
        f"# Spike QA Synthesis — Run {run_ts}",
        "",
        f"**Overall verdict:** **{overall}**",
        "",
        f"- Codex (gpt-5.5/high): **{codex_verdict}**",
        f"- Gemini (3.1-pro):     **{gemini_verdict}**",
        "",
        "## Where reviewers AGREED",
        "",
    ]
    if shared:
        for cf, gf in shared:
            parts.append(f"- **{cf}**")
            parts.append(f"  - _gemini parallel:_ {gf}")
    else:
        parts.append("_(no overlapping findings detected; review the two files independently)_")
    parts += ["", "## Codex-only findings", ""]
    if codex_only:
        for cf in codex_only:
            parts.append(f"- {cf}")
    else:
        parts.append("_(none)_")
    parts += ["", "## Gemini-only findings", ""]
    if gemini_only:
        for gf in gemini_only:
            parts.append(f"- {gf}")
    else:
        parts.append("_(none)_")
    parts += [
        "",
        "## Go/no-go",
        "",
    ]
    if overall == "PASS":
        parts += [
            "Both independent reviewers signed off on framework integrity, grounding,",
            "independence, isolation, and probability sanity. The spike clears the",
            "design-doc gate; Phase 1 production deploy is unblocked from the",
            "subagent-invocation perspective. Other gates (JCC-956 buyer call, full",
            "12-perspective load test) still apply.",
        ]
    elif overall == "FAIL":
        parts += [
            "At least one reviewer flagged a critical failure. Do NOT proceed to",
            "Phase 1 production deploy until the named failure mode is resolved.",
            "Re-run the spike after fixes.",
        ]
    else:
        parts += [
            "Reviewers split or returned unclear verdicts. Read both review files",
            "in full and apply human judgment before proceeding.",
        ]
    parts += [
        "",
        "## Raw reviewer outputs",
        "",
        "- `codex-review.md`",
        "- `gemini-review.md`",
    ]
    return "\n".join(parts) + "\n"


def main():
    if len(sys.argv) != 2:
        print("usage: synthesize-qa.py <RUN_TS>", file=sys.stderr)
        sys.exit(1)
    run_ts = sys.argv[1]
    proj = Path(__file__).resolve().parent.parent
    adv = proj / "spike" / "runs" / run_ts / "advisory"
    codex = adv / "codex-review.md"
    gemini = adv / "gemini-review.md"
    if not codex.exists() or not gemini.exists():
        print(f"ERROR: missing reviewer outputs in {adv}", file=sys.stderr)
        sys.exit(2)
    synthesis = render(run_ts, codex.read_text(), gemini.read_text())
    out = adv / "spike-qa-synthesis.md"
    out.write_text(synthesis)
    print(f"Synthesis written: {out}")
    print()
    print(synthesis)


if __name__ == "__main__":
    main()
