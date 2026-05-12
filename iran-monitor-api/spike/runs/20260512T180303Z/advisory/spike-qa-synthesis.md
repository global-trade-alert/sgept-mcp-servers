# Spike QA Synthesis — Run 20260512T180303Z

**Overall verdict:** **FAIL**

- Codex (gpt-5.5/high): **FAIL**
- Gemini (3.1-pro):     **FAIL**

## Where reviewers AGREED

- **S1 schelling: “**coercive-logic analysis**,” “**BATNA**,” “**commitment problem**”**
  - _gemini parallel:_ **Schelling-bargaining** relies on "coercive-logic analysis," "BATNA," "focal point," and "commitment problem" (e.g., S2: "This is the textbook Schelling tacit bargain").

## Codex-only findings

- **Grounding fails** for at least one perspective output: **S1 schelling-bargaining** cites only one concrete intelligence item.
- **Independence fails**: several non-Tetlock outputs explicitly anchor on or “revise” the Tetlock prior, indicating cross-perspective dependence.
- **Framework integrity is mostly strong but not perfect**: Wack outputs identify predetermined elements, but do not explicitly provide signposts, which the rubric requires.
- **Tetlock** uses base rates/Fermi/Bayesian decomposition:
- S1 tetlock: “**Fermi decomposition yields** …”
- S2 tetlock: “**Base rate is effectively zero** …” and “**Fermi decomposition** …”
- S3 tetlock: “**Fermi decomposition yields two components** …” and “**Bayesian chain** …”
- **Schelling** uses bargaining/coercion/credibility/BATNA:
- S2 schelling: “**BATNAs**,” “**tacit bargain**,” “**audience costs**,” “**focal point**”

## Gemini-only findings

- **Tetlock-forecaster** consistently utilizes "Fermi decomposition," "base rate," and "Bayesian chain" (e.g., S1: "Fermi decomposition yields an extremely low base rate").
- **Wack-strategic** correctly structures reasoning around "predetermined elements" and "structural constraints" (e.g., S3: "Wack's predetermined-element taxonomy identifies the Article 5-equivalent trigger as structurally predetermined").
- **S1:** Cites "PWL-026" (MuddyWater 'Dindoor' backdoor) and the "Day 72 war chronicle" (Iran-US MoU negotiations).
- **S2:** Cites the "Trump-Xi summit in Beijing on May 14-15," "US Treasury sanctioned Chang Guang Satellite Technology... on May 8-10," and the "Day 65 directive."
- **S3:** Cites "B4 at 35%," the "Hezbollah 105-wave record," and a "vessel strike 23nm from Doha."
- *Verbatim text copying:* In S1, Tetlock writes `(MuddyWater 'Dindoor' backdoor, elevated wiper-attack risk)` and Schelling reuses this exact string. In S3, Tetlock writes `France, UK refusing full Iran war participation, Saudi Arabia blocking Prince Sultan access` which Schelling copies verbatim, and Wack copies near-verbatim (`France and UK refusing full Iran war participation, Saudi Arabia denying Prince Sultan access`).
- *Explicit output referencing:* Schelling and Wack explicitly anchor to Tetlock's numerical prior, violating independent probability decomposition. S1 Schelling writes, "The Tetlock prior of 2% is modestly reduced to 1.5%". S2 Wack writes, "The Tetlock cold-start prior (3%) is well-reasoned". S3 Wack writes, "Revising Tetlock's prior modestly downward from 3% to 2.5%".
- Every `p_point` is in `[0, 1]` (e.g., S1 outputs are 0.020, 0.015, 0.015).
- Every `interval` successfully brackets its respective `p_point` (e.g., S2 Tetlock point `0.030` is bracketed by `[0.01, 0.06]`).

## Go/no-go

At least one reviewer flagged a critical failure. Do NOT proceed to
Phase 1 production deploy until the named failure mode is resolved.
Re-run the spike after fixes.

## Raw reviewer outputs

- `codex-review.md`
- `gemini-review.md`
