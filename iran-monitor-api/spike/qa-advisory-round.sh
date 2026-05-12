#!/usr/bin/env bash
# Multi-model QA on a spike-results.md file.
# Mirrors what /advisory-round does: codex (gpt-5.5/high) + gemini (3.1-pro)
# in parallel, then a synthesis step.
#
# Usage:
#   ./spike/qa-advisory-round.sh <RUN_TS>
#
# Outputs land in spike/runs/$RUN_TS/advisory/.

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <RUN_TS>" >&2
  exit 1
fi

RUN_TS="$1"
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$PROJ/spike/runs/$RUN_TS"
RESULTS="$RUN_DIR/spike-results.md"
ADV_DIR="$RUN_DIR/advisory"
HELPERS="$HOME/Documents/GitHub/jf-private/.claude/shared-scripts"

if [[ ! -f "$RESULTS" ]]; then
  echo "ERROR: spike-results.md not found at $RESULTS" >&2
  exit 2
fi
mkdir -p "$ADV_DIR"

POSITION="$ADV_DIR/position.md"
CODEX_OUT="$ADV_DIR/codex-review.md"
GEMINI_OUT="$ADV_DIR/gemini-review.md"

# Build position file = QA prompt + the artifact under review
cat > "$POSITION" <<EOF
# Iran Monitor API — Spike QA Position Brief

## Artifact under review

A subagent-invocation spike for the Iran Monitor Inference API. The spike
exercises a Python-worker → \`claude -p\` headless subprocess pattern that
invokes perspective agents (tetlock-forecaster, schelling-bargaining,
wack-strategic) against three novel scenarios outside the canonical 8.

## Objective

Reviewer must reply with PASS in a Summary section iff ALL of the following hold;
else FAIL with reasoning. Cite specific lines/sections from the artifact for each
finding.

1. **Framework integrity.** Each perspective's captured \`key_reasoning\` reads
   like the framework named (Tetlock uses base rates + Fermi decomposition;
   Schelling reasons about coercion, credibility, focal points; Wack names
   predetermined elements + signposts). No perspective's reasoning could be
   swapped for another's without a domain expert noticing.
2. **Grounding.** Each perspective references at least 2 specific intelligence
   items (named operations, dates, actors, evidence) — i.e. the agent actually
   consulted the iran-monitor intelligence base rather than producing
   model-trained-data filler.
3. **Independence.** Three perspectives on the same scenario disagree about
   the right things (probability decomposition, weighting of evidence) but
   share a thematic spine derived from the intelligence base. They do NOT
   show copy-paste-feel between agents (verbatim phrases, identical
   sub-claims).
4. **Isolation.** The isolation probe (Schelling-bargaining run with vs.
   without a distinctive "ISOLATION PROBE" marker prior) shows: the no-prior
   run does NOT echo the marker text. If marker leakage occurred, this is a
   critical failure regardless of other dimensions.
5. **Probabilities sane.** Each \`p_point\` is in [0, 1]; \`p_interval\` brackets
   the point; aggregate divergence flag matches whether max-min > 15pp.

Also score on these dimensions (1-5 scale, 5 = strongest):

- **Framework integrity score** (per perspective; report mean across all 9)
- **Grounding score** (per perspective)
- **Disagreement quality** (how productive is the disagreement across perspectives?)
- **Production-readiness** (would these outputs be usable in a paid pilot today, with the known evidence_urls caveat?)

## Out of scope

- Whether the underlying perspective frameworks are well-chosen (assume they are).
- Whether the scenarios are well-formed (they're fixed for this run).
- HTTP API correctness, signing-key handling, rate limits (separate test surface).

---

## Spike results (the artifact)

\`\`\`markdown
$(cat "$RESULTS")
\`\`\`
EOF

echo "Position brief written: $POSITION"

# Run codex + gemini in parallel
echo "Dispatching codex (gpt-5.5 / high) + gemini (3.1-pro) reviewers in parallel..."

bash "$HELPERS/advisory-round-invoke-codex.sh" "$POSITION" "$CODEX_OUT" gpt-5.5 high &
CODEX_PID=$!
bash "$HELPERS/advisory-round-invoke-gemini.sh" "$POSITION" "$GEMINI_OUT" "" &
GEMINI_PID=$!

wait "$CODEX_PID"; CODEX_EXIT=$?
wait "$GEMINI_PID"; GEMINI_EXIT=$?

echo "Codex exit: $CODEX_EXIT"
echo "Gemini exit: $GEMINI_EXIT"
echo "Codex review:  $CODEX_OUT"
echo "Gemini review: $GEMINI_OUT"

# Quick verdict extraction
echo
echo "=== CODEX VERDICT ==="
grep -i -E "^(PASS|FAIL|verdict|summary)" "$CODEX_OUT" 2>/dev/null | head -5 || echo "(no clear verdict line)"
echo
echo "=== GEMINI VERDICT ==="
grep -i -E "^(PASS|FAIL|verdict|summary)" "$GEMINI_OUT" 2>/dev/null | head -5 || echo "(no clear verdict line)"
echo
echo "=== DONE ==="
echo "Run the synthesis step manually (or via /advisory-round) to integrate both reviews."
