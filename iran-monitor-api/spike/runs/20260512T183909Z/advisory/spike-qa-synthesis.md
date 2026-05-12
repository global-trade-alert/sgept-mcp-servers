# Spike QA Synthesis — Run 20260512T183909Z

**Overall verdict:** **FAIL**

- Codex (gpt-5.5/high): **FAIL**
- Gemini (3.1-pro):     **PASS**

## Where reviewers AGREED

- ****S3 schelling:** “A Houthi-US commercial shipping ceasefire… representing a tacit Schelling bargain…” and “Breaking this focal point…”**
  - _gemini parallel:_ *S3 Wack* cites the "Houthi-US commercial shipping ceasefire... since 6 May 2026" and "Saudi Arabia's refusal of base access (Day 69)".

## Codex-only findings

- **Wack framework integrity is incomplete:** the Wack outputs consistently use “predetermined elements,” but they do **not name or present signposts**, despite the criterion requiring Wack to include “predetermined elements + signposts.”
- **Grounding fails for at least one perspective:** **S2-oil-yuan / wack-strategic** does not clearly reference at least two specific intelligence items; it relies mostly on generic structural claims.
- **S1 tetlock:** “The historical base rate…” and “Fermi decomposition: P(Iran decides…)…”
- **S2 tetlock:** “Outside view: formal public bilateral oil-for-yuan agreements…” and “Fermi decomposition: P(China willing…)…”
- **S3 tetlock:** “The scenario requires two conjunctive conditions…” with explicit conditional estimates: “0.38 × 0.18 × 0.04…”
- **S1 schelling:** “Iran's current coercive game is targeted at the US, Gulf shipping states, and Israel…” and “the Trump-Xi summit… is the dominant focal point…”
- **S2 schelling:** “China's strategic leverage… derives entirely from maintaining ambiguity,” “commitment device,” “focal point violation,” and “commitment problem is inverted…”
- **S1 wack:** “Wack's predetermined-vs-uncertain taxonomy identifies two structural constraints…” but no signposts are named.
- **S2 wack:** “Predetermined elements cut sharply against this scenario…” but again no signposts.

## Gemini-only findings

- *Tetlock*: Uses base rates and explicit probability breakdown (e.g., S1: *"Fermi decomposition: P(Iran decides...) ≈ 3-4%"*, S2: *"Bayesian update ... Fermi decomposition"*).
- *Schelling*: Focuses strictly on game theory, leverage, and negotiation dynamics (e.g., S1: *"coercive game ... coercive benefit"*, S2: *"focal point violation"*, *"Schelling commitment problem"*).
- *Wack*: Explicitly filters through structural forces and predetermined taxonomy (e.g., S1: *"Wack's predetermined-vs-uncertain taxonomy"*, S3: *"near-predetermined institutional impossibility"*).
- *S1 Tetlock* cites "PWL-026", "MuddyWater's new Dindoor backdoor", and the "Trump-Xi summit on 14–15 May".
- *S2 Schelling* cites the "May 3 formal order for firms to ignore US Iran sanctions" and "US Treasury sanctions of Chinese satellite firms on 10 May".
- *Example (S2):* Tetlock treats the May 14-15 summit as a *"possible catalyst for a provocative Chinese signal"* (pushing probability up), whereas Schelling sees it as a *"focal point violation"* that would invite US escalation (suppressing probability), and Wack points to structural bandwidth constraints. They disagree productively based on their frameworks.
- All `p_point` values fall strictly within `[0, 1]`.
- Every `p_interval` correctly brackets its respective `p_point` (e.g., S3 Schelling p=0.020 is within [0.01, 0.04]).
- Aggregation math and divergence flags are correct. Divergence is calculated properly (e.g., in S3, max 0.03 - min 0.016 = 0.014 = 1.4pp), and `divergence_flag` correctly evaluates to `false` in all cases since none exceed the 15pp threshold.

## Go/no-go

At least one reviewer flagged a critical failure. Do NOT proceed to
Phase 1 production deploy until the named failure mode is resolved.
Re-run the spike after fixes.

## Raw reviewer outputs

- `codex-review.md`
- `gemini-review.md`
