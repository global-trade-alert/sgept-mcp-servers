# Iran Monitor API — Spike QA Position Brief

## Artifact under review

A subagent-invocation spike for the Iran Monitor Inference API. The spike
exercises a Python-worker → `claude -p` headless subprocess pattern that
invokes perspective agents (tetlock-forecaster, schelling-bargaining,
wack-strategic) against three novel scenarios outside the canonical 8.

## Objective

Reviewer must reply with PASS in a Summary section iff ALL of the following hold;
else FAIL with reasoning. Cite specific lines/sections from the artifact for each
finding.

1. **Framework integrity.** Each perspective's captured `key_reasoning` reads
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
5. **Probabilities sane.** Each `p_point` is in [0, 1]; `p_interval` brackets
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

```markdown
# Iran Monitor API — Subagent Invocation Spike Results

**Generated:** 20260512T180303Z
**Perspectives:** tetlock-forecaster, schelling-bargaining, wack-strategic
**Scenarios:** 3

## Spike objective

Validate that `claude -p` headless invocation from a Python worker delivers:

1. Per-perspective parseable JSON output for a novel (non-canonical-8) scenario.
2. Isolation: agent N's reasoning is structurally independent of agent N-1's output text.
3. End-to-end pipeline: intel-base seal → perspective subprocess → aggregation → Ed25519-signed audit record, all on real (not mocked) data.

## Scenarios used

- **S1-cyber-germany** (cyber, medium): Iran (IRGC or proxy) launches a meaningfully disruptive cyber attack on German critical infrastructure (energy grid, water utilities, or rail) attributable to Iran within the next 30 days, with German government public attribution.
- **S2-oil-yuan** (economic, medium): Iran and China sign a formal bilateral agreement enabling oil-for-yuan settlement (not crude swap, not informal credit) with at least one explicit volume commitment, within the next 30 days, publicly announced by both parties.
- **S3-houthi-redsea** (regional, high): Houthi forces conduct a multi-vessel attack on commercial shipping in the Red Sea within the next 30 days that causes ≥3 vessel casualties (sunk, severely damaged, or crew casualties), prompting at least one Western navy to declare an Article 5-equivalent response posture.

## S1-cyber-germany

**Scenario:** Iran (IRGC or proxy) launches a meaningfully disruptive cyber attack on German critical infrastructure (energy grid, water utilities, or rail) attributable to Iran within the next 30 days, with German government public attribution.

**Intel-base hash:** `sha256:688028d990580189611326674316b847aa5a7a4953add4395a53b38d8c5263fc`

### Per-perspective outputs

| Perspective | p_point | interval | runtime (s) | evidence URLs |
|---|---|---|---|---|
| tetlock-forecaster | 0.020 | [0.01, 0.04] | 119.6 |  |
| schelling-bargaining | 0.015 | [0.01, 0.03] | 98.5 |  |
| wack-strategic | 0.015 | [0.01, 0.03] | 168.9 |  |

### Reasoning (full text)

#### tetlock-forecaster (p=0.020)

> Fermi decomposition yields an extremely low base rate: P(Iran deliberately targets German CI) × P(meaningful disruption achieved) × P(German public attribution within 30 days) ≈ 0.03 × 0.25 × 0.30 ≈ 0.22%. The peripheral watch list (PWL-026, cycle 260327-1115) confirms IRGC cyber command is actively developing new destructive tools (MuddyWater 'Dindoor' backdoor, elevated wiper-attack risk), which pushes the estimate modestly above base rate. However, three hard constraints suppress the probability toward the low end: (1) zero historical precedent for a meaningfully disruptive Iranian cyberattack on German critical infrastructure in the public record — Iran's disruptive cyber operations have targeted Saudi Arabia, Israel, and US entities, not EU NATO members; (2) Germany is not a belligerent in the active conflict and attacking German energy/water/rail would open a new European front at the worst possible strategic moment, alienating a neutral that has not been particularly hostile to Iran's position; (3) the compound requirement — attempt, meaningful disruption of hardened BSI-protected systems, and German government public attribution all within a single 30-day window — is extremely demanding; German attribution alone typically takes weeks to months even after a confirmed incident. The ongoing Iran-US MoU negotiations (Day 72 war chronicle) further reduce Iran's incentive to provoke European reaction. The 2% central estimate reflects the elevated threat environment from active conflict, the PWL-026 cyber escalation signal, and a small non-zero tail for opportunistic or proxy-attributed incidents, offset sharply against the near-zero base rate for this specific target-geography-attribution compound event.

#### schelling-bargaining (p=0.015)

> The Schelling framework's primary contribution here is coercive-logic analysis: for an attack to serve bargaining purposes, the target must control something Iran wants, and compliance must become more attractive than defiance after the attack. Germany controls none of the variables Iran is trying to move — US military posture, Hormuz transit rights, sanctions architecture — so the attack produces no coercive pathway to any of Iran's stated objectives. If anything it worsens Iran's BATNA by converting a sympathetic neutral (European states have pushed back on US war posture) into an adversary, and the bilateral commitment problem prevents any resulting German concessions from being credible anyway. PWL-026 (MuddyWater 'Dindoor' backdoor, elevated wiper-attack risk) establishes that IRGC cyber command is developing new destructive tools, but tool development does not constitute coercive purpose. The Tetlock prior of 2% is modestly reduced to 1.5% on the grounds that the bargaining structure actively disincentivises deliberate Germany-targeting, while preserving non-zero probability for rogue/unauthorised IRGC cyber actions, broad Western-targeting campaigns that incidentally reach German infrastructure, and the compound-attribution tail that Tetlock already discounted.

#### wack-strategic (p=0.015)

> The Wack framework identifies three predetermined elements that jointly suppress this scenario toward its floor. First, Iran's cyber operational pattern is geographically predetermined: MuddyWater/IRGC cyber command has targeted Saudi, Israeli, and US networks — not EU/NATO member state critical infrastructure — across its documented operational history; PWL-026 confirms the 'Dindoor' deployment targets US networks specifically. Second, Germany's non-belligerent status is a structural constraint that would be violated by this scenario: Iran needs European diplomatic neutrality to preserve off-ramps, and the Day-72 war chronicle confirms the MoU negotiation channel is active (Iran transmitted its formal response via Pakistan on Day 72), making European provocation strategically irrational at this precise moment. Third, German public attribution within 30 days is structurally near-impossible: BSI attribution processes take months even after a confirmed incident; the compound requirement — meaningful disruption of BSI-hardened systems, attribution investigation, and government public attribution — in a single 30-day window is not supported by any precedent. The sole genuine uncertainty is an unconstrained proxy actor, but IRGC proxy targeting decisions have shown no European orientation. I update modestly below the Tetlock cold-start prior (2.0% → 1.5%) because the Day-72 MoU diplomatic track has strengthened the 'preserve European neutrality' predetermined element since the prior was written, reducing the already-minimal residual probability further.

### Aggregation + signed audit

```json
{
  "p_point": 0.016666666666666666,
  "p_range": [
    0.015,
    0.02
  ],
  "divergence_pp": 0.5000000000000001,
  "divergence_flag": false
}
```

Signature (base64 Ed25519): `ncB+OtLhe4LqwD9Pt8jilbUtacjKm1k6jnUdYQmswhBR69ajNNMy+tsM7dmMU7uqhn+lRqtysR5Oq3Nlwyt2BQ==`

### Isolation probe — schelling-bargaining with/without distinctive prior

**Leak marker check:** no-leak (PASS)

Both runs are recorded under `isolation/` and `isolation-with-prior/`.

## S2-oil-yuan

**Scenario:** Iran and China sign a formal bilateral agreement enabling oil-for-yuan settlement (not crude swap, not informal credit) with at least one explicit volume commitment, within the next 30 days, publicly announced by both parties.

**Intel-base hash:** `sha256:688028d990580189611326674316b847aa5a7a4953add4395a53b38d8c5263fc`

### Per-perspective outputs

| Perspective | p_point | interval | runtime (s) | evidence URLs |
|---|---|---|---|---|
| tetlock-forecaster | 0.030 | [0.01, 0.06] | 187.2 | [1](https://www.state.gov/releases/office-of-the-spokesperson/2026/05/disrupting-irans-overseas-military-procurement-networks-2/) [2](https://www.chinatechnews.com/2026/05/10/121435-u-s-treasury-sanctions-chinese-tech-companies-over-alleged-support-for-iranian-missile-and-drone-programs) |
| schelling-bargaining | 0.020 | [0.01, 0.04] | 96.4 |  |
| wack-strategic | 0.018 | [0.00, 0.04] | 150.8 |  |

### Reasoning (full text)

#### tetlock-forecaster (p=0.030)

> Base rate is effectively zero — no such agreement (formal bilateral, oil-for-yuan with explicit volume commitment, publicly announced by both parties) has been signed in 20+ years of significant Iran-China oil trade; actual mechanisms are informal intermediaries and deliberate opacity. Current conditions push the estimate below even the prior: (1) US Treasury sanctioned Chang Guang Satellite Technology and associated entities on May 8-10 for enabling IRGC targeting, creating maximum political cost for Beijing to formalise Iran ties in the same window; (2) Trump-Xi summit in Beijing on May 14-15 — four days from now — means China will not issue a provocation that directly undercuts the summit's agenda of US pressure on Iran to reopen Hormuz; (3) the Araghchi-Wang Yi meeting on 6 May was diplomatic positioning, not economic deal-making, and China is explicitly calling for 'comprehensive ceasefire', a mediator posture incompatible with formal economic integration signalling. Fermi decomposition: P(China political will now) ~0.04 × P(Iran political will) ~0.35 × P(deal in 30 days) ~0.20 × P(public by both) ~0.25 = 0.0007. Bayesian chain from 2% prior, applying LR for fresh US sanctions (0.30), summit imminence (0.20), active Iran-US diplomacy via Pakistan (0.50) yields posterior ~0.06%. The 3% point estimate is a disciplined upward adjustment for Chinese decision-making uncertainty and the possibility of a confrontational summit outcome triggering countermoves.

#### schelling-bargaining (p=0.020)

> The Schelling-central insight is that both China and Iran currently have BATNAs that are strictly superior to a formal public deal. China's Day 65 directive ordering domestic firms to ignore US Iran sanctions achieves the economic substance of oil-for-yuan protection without the audience costs of formalization — this is the textbook Schelling tacit bargain, and it makes a public treaty unnecessary. The Trump-Xi summit on 14-15 May (2-3 days from now at cycle close) creates prohibitive audience costs for China: formalising Iran economic ties immediately before a summit where China is positioning as mediator would destroy its bargaining leverage across every agenda item. China's mediator posture — calling for ceasefire, hosting Wang Yi-Araghchi meeting — is structurally incompatible with being seen as Iran's declared economic patron. The informal arrangement is itself the Schelling focal point: both sides have converged on opacity precisely because it avoids the commitment problem (formal announcement invites US secondary sanctions escalation that both sides want to avoid). No external event within the 30-day window creates a focal point for formalisation; the only scenario that could (a catastrophic summit breakdown post-May 15) leaves fewer than 2 weeks for negotiation, drafting, and dual public announcement — an impossibly tight timeline for a formal bilateral agreement with volume commitments.

#### wack-strategic (p=0.018)

> Three predetermined elements, not three uncertainties, block this scenario. First, China's deniability doctrine is structural: the Day 65 (May 3) domestic order instructing Chinese firms to ignore US Iran sanctions already achieves Beijing's operational objective — protecting yuan-settled Iran trade — without the geopolitical cost of a public bilateral agreement. The domestic order is a functional substitute that *reduces* demand for formalisation, not a step toward it. Second, the Trump-Xi summit (May 14-15) imposes a hard constraint: China's declared posture is mediator demanding 'comprehensive ceasefire', and signing a formal oil-for-yuan pact in the same window would be an act of bad faith incompatible with that posture. Third, the May 8-10 US Treasury sanctions on Chinese satellite firms for enabling IRGC targeting demonstrate the US is actively escalating costs for Iran-adjacent Chinese actions — formalisation would invite sector-wide retaliation. The Tetlock cold-start prior (3%) is well-reasoned; I update modestly downward because the Day 65 domestic directive has already satisfied China's near-term operational demand for Iran energy settlement protection without triggering the sanctions exposure that public formalisation would create. The 4% upper bound captures the non-negligible tail probability of a confrontational summit outcome driving a deliberate Chinese countermeasure — but even then, a formal oil-for-yuan agreement is an implausibly high-profile instrument when grey-zone mechanisms are available.

### Aggregation + signed audit

```json
{
  "p_point": 0.02266666666666667,
  "p_range": [
    0.018,
    0.03
  ],
  "divergence_pp": 1.2,
  "divergence_flag": false
}
```

Signature (base64 Ed25519): `A11aiYcDe08AxEqrj6ct6Z7zhpjjPNofjt7u5wsPV5GsP0xqIo3iOVAxLM6gaskC5gfcN8G4H98P7+CMsqDLAg==`

## S3-houthi-redsea

**Scenario:** Houthi forces conduct a multi-vessel attack on commercial shipping in the Red Sea within the next 30 days that causes ≥3 vessel casualties (sunk, severely damaged, or crew casualties), prompting at least one Western navy to declare an Article 5-equivalent response posture.

**Intel-base hash:** `sha256:688028d990580189611326674316b847aa5a7a4953add4395a53b38d8c5263fc`

### Per-perspective outputs

| Perspective | p_point | interval | runtime (s) | evidence URLs |
|---|---|---|---|---|
| tetlock-forecaster | 0.030 | [0.01, 0.06] | 158.4 |  |
| schelling-bargaining | 0.020 | [0.01, 0.04] | 103.4 |  |
| wack-strategic | 0.025 | [0.01, 0.05] | 132.0 |  |

### Reasoning (full text)

#### tetlock-forecaster (p=0.030)

> Fermi decomposition yields two components: P(Houthi multi-vessel attack ≥3 vessel casualties, Red Sea, 30 days) ≈ 25%, and P(Article 5-equivalent Western naval response | that attack) ≈ 8-10%. The first component is driven upward by confirmed Houthi activation since Day 28, at least 4 vessels already struck in this conflict, and B4 at 35% reflecting active regional widening — Houthis are operational. The second component is the binding constraint. Base rate for Article 5-equivalent declarations in response to maritime proxy attacks is zero: the US conducted 18 months of Houthi counter-operations without invoking collective defense, and in the current 72-day conflict Western navies have absorbed escalating attacks (Hezbollah 105-wave record, vessel strike 23nm from Doha) without formal collective-defense declarations. Availability bias check: the dramatic attack numbers inflate Component 1 intuitions, but coordinated multi-vessel attacks causing ≥3 casualties in a single operation remain qualitatively rarer than individual vessel targeting. NATO cohesion signal (France, UK refusing full Iran war participation, Saudi Arabia blocking Prince Sultan access) strongly compresses Component 2. Bayesian chain: base rate ~2%, updated upward by B4 dominance and confirmed Houthi posture (LR ~1.5), updated downward by 70+ days of negative evidence on Article 5-equivalent declarations (LR ~0.8). Posterior: 2.4%, rounded to 3%.

#### schelling-bargaining (p=0.020)

> The scenario requires a conjunction: a qualitatively severe Houthi attack (≥3 vessel casualties) AND a formal collective-defence declaration by a Western navy. The Schelling framework compresses both components. Component 1 is plausible given B4 at 35% and confirmed Houthi operational tempo (4 vessels struck to date, record Hezbollah escalation co-occurring), but coordinated multi-vessel attacks reaching the ≥3 casualty threshold in a single engagement remain rarer than individual targeting. Component 2 is the binding constraint and the Schelling framework specifically argues for a very low conditional probability: the audience cost mechanism runs in reverse here — Western navies know that declaring Article 5-equivalent creates binding obligations they may be unable to honour (given fragmented allied cohesion: France, UK refusing full Iran war participation, Saudi Arabia blocking Prince Sultan access), so rational actors set the declaration threshold extremely high precisely because backing down from it would be catastrophic to credibility. This is Schelling's commitment device logic applied to abstention: by not declaring, Western navies preserve their BATNA (continued defensive operations without formal collective-defence obligations), which is superior to the commitment costs of declaration. Seventy-two days of absorbing attacks — including vessels sunk, a strike 23nm from Doha, and drone attacks on Gulf infrastructure — without any Article 5-equivalent declaration establishes a strong empirical baseline against Component 2. The allied fragmentation dynamics make collective coordination for such a declaration even harder than the base rate suggests.

#### wack-strategic (p=0.025)

> Wack's predetermined-element taxonomy identifies the Article 5-equivalent trigger as structurally predetermined NOT to occur: NATO doctrine covers attacks on member states, not proxy attacks on commercial shipping, and Western navies have absorbed 70+ days of escalating attacks (plus 18+ months pre-conflict) without invoking collective defence — this is negative evidence with a strong Bayesian weight. The Houthi attack component is genuinely uncertain (~15-20% at current operational tempo given confirmed B4-era activation), but the joint probability collapses because the response mechanism is near-structurally impossible under current alliance conditions. Two new predetermined elements further compress: (1) Western coalition fracture — France and UK refusing full Iran war participation, Saudi Arabia denying Prince Sultan access — moves the alliance posture away from collective-defence escalation; (2) GPS jamming attribution ambiguity (PWL-019, 1,100+ ships) creates conditions where even a severe incident risks initial ambiguity, delaying rather than triggering a formal collective-defence declaration. Revising Tetlock's prior modestly downward from 3% to 2.5%, with the binding constraint entirely in the response mechanism, not the attack probability.

### Aggregation + signed audit

```json
{
  "p_point": 0.024999999999999998,
  "p_range": [
    0.02,
    0.03
  ],
  "divergence_pp": 0.9999999999999999,
  "divergence_flag": false
}
```

Signature (base64 Ed25519): `EwxK8mvT1RqkP93ljOzJmcnBerAABAB11cqLzjBOUneuA6Zk/X92xP1GuXpd4KNnIeK1Kt62HbGB4tRXbA8ZCg==`

---
## Pass/fail criteria

- [ ] All 3 perspectives produced parseable JSON for each scenario (no `SubagentError`)
- [ ] `p_point ∈ [0, 1]` and `key_reasoning` non-empty for each
- [ ] Per-perspective runtime under 5 min (spike threshold; production target 25 min for 12 perspectives)
- [ ] Isolation: distinctive prior marker does NOT appear in the no-prior run's reasoning
- [ ] Audit record validates against the verification key
- [ ] Aggregation + divergence flag computed correctly

CEO reviews the captured reasoning narratives for substantive quality (framework applied, evidence cited).
`/advisory-round` provides independent codex+gemini critique of the spike outputs.
```
