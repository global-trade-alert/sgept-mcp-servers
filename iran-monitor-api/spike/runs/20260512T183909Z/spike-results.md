# Iran Monitor API — Subagent Invocation Spike Results

**Generated:** 20260512T183909Z
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
| tetlock-forecaster | 0.022 | [0.01, 0.05] | 136.4 |  |
| schelling-bargaining | 0.015 | [0.01, 0.04] | 93.3 |  |
| wack-strategic | 0.013 | [0.01, 0.03] | 245.7 |  |

### Reasoning (full text)

#### tetlock-forecaster (p=0.022)

> The historical base rate for a publicly-attributed, meaningfully disruptive Iranian cyber attack on German critical infrastructure is effectively zero; no such event has occurred in the 72 days of active conflict despite Iran having both motive and opportunity. Fermi decomposition: P(Iran decides to target European CI) ≈ 3-4%, P(Germany selected among European targets) ≈ 25%, P(meaningful disruption achieved against hardened BSI-defended infrastructure) ≈ 15%, P(German government publicly attributes within 30 days) ≈ 20% — yielding a compound probability below 0.05%. Inside-view adjustments lift this modestly: PWL-026 confirms MuddyWater's new Dindoor backdoor deployment and Unit 42's elevated wiper-attack warning signal a real cyber escalation posture, and IRGC's 70% launcher attrition creates genuine incentive to shift toward asymmetric instruments. However, three structural factors dominate downward: (1) Iran has strong strategic incentives to preserve German and European neutrality during active diplomacy — attacking Germany risks foreclosing the one diplomatic track that could provide an exit; (2) the non-occurrence of European CI targeting over 72 conflict days is mildly diagnostic against the hypothesis (a Bayesian LR of ~0.5); (3) the Trump-Xi summit on 14–15 May creates a near-term diplomatic focal point that makes provocation especially costly for Iran right now. Scope insensitivity guard: MuddyWater's active operations are real but concentrated against US targets, and extrapolating from US-focused cyber escalation to German CI disruption requires an additional decision step Iran has not taken.

#### schelling-bargaining (p=0.015)

> The Schelling bargaining framework produces a likelihood ratio below 1 against the prior. Iran's current coercive game is targeted at the US, Gulf shipping states, and Israel — the coercive structure requires attacking the right actor, and Germany is not a node in that structure. Attacking German critical infrastructure would open a new NATO-member front with no corresponding coercive benefit: it cannot force Trump to exit, cannot reopen Hormuz negotiations, and cannot deter the IRGC's primary adversaries. PWL-026 confirms IRGC cyber command's active focus is US networks (MuddyWater Dindoor backdoor, US medical institutions), not European infrastructure. The attribution requirement adds a second barrier: Germany's political incentive is to remain outside the active coalition, so public attribution would require a politically costly decision to insert Germany into a bilateral US-Iran confrontation. The 30-day window is compressed: the Trump-Xi summit (14-15 May) is the dominant focal point for this period, and Iran has strategic incentives to avoid actions that undermine Chinese mediation.

#### wack-strategic (p=0.013)

> The scenario requires a compound condition: a meaningfully disruptive cyber attack on German critical infrastructure AND German government public attribution within 30 days. Wack's predetermined-vs-uncertain taxonomy identifies two structural constraints that bind simultaneously. First, Germany's non-belligerent status is a predetermined element — Germany declined coalition participation in this conflict, preserving Iran's European diplomatic channel; Iran's strategic interest in that channel is load-bearing for the Pakistan/Qatar mediation architecture, which Iran actively engages. Attacking a NATO member's critical infrastructure destroys that channel at maximum cost. Second, German public attribution within 30 days is structurally near-impossible: German institutional attribution processes historically run 6-12 months, and the political will to publicly accuse Iran while other EU governments avoid the primary conflict is a predetermined institutional friction. The only upward force is PWL-026 (IRGC 'Dindoor' cyber escalation, Ansoff Level 3): IRGC cyber command is actively developing new capabilities under wartime conditions, but the documented target set is US networks, not European infrastructure. IRGC institutional autonomy creates residual tail risk of unauthorised escalation beyond authorised targeting doctrine, but the compound probability (meaningful disruption AND public attribution within 30 days) lands below the prior.

### Aggregation + signed audit

```json
{
  "p_point": 0.016666666666666666,
  "p_range": [
    0.013,
    0.022
  ],
  "divergence_pp": 0.8999999999999999,
  "divergence_flag": false
}
```

Signature (base64 Ed25519): `QDiadBO5/Xle9NEyUrTp1ASepSJ+2j1B2aJp0RkquyvgkJqGcuJeJ39Sym2zC3I2CH3fSi7zTPjGJUHpY2jnDg==`

### Isolation probe — schelling-bargaining with/without distinctive prior

**Leak marker check:** no-leak (PASS)

Both runs are recorded under `isolation/` and `isolation-with-prior/`.

## S2-oil-yuan

**Scenario:** Iran and China sign a formal bilateral agreement enabling oil-for-yuan settlement (not crude swap, not informal credit) with at least one explicit volume commitment, within the next 30 days, publicly announced by both parties.

**Intel-base hash:** `sha256:688028d990580189611326674316b847aa5a7a4953add4395a53b38d8c5263fc`

### Per-perspective outputs

| Perspective | p_point | interval | runtime (s) | evidence URLs |
|---|---|---|---|---|
| tetlock-forecaster | 0.040 | [0.02, 0.07] | 141.4 |  |
| schelling-bargaining | 0.030 | [0.01, 0.06] | 138.6 | [1](https://www.aljazeera.com/news/2026/5/10/iran-sends-response-to-us-proposal-to-end-war-via-mediator-pakistan) [2](https://www.chinatechnews.com/2026/05/10/121435-u-s-treasury-sanctions-chinese-tech-companies-over-alleged-support-for-iranian-missile-and-drone-programs) [3](https://www.bloomberg.com/news/articles/2026-05-10/us-awaits-iran-reply-as-aramco-says-hormuz-opening-no-quick-fix) |
| wack-strategic | 0.035 | [0.01, 0.06] | 135.1 |  |

### Reasoning (full text)

#### tetlock-forecaster (p=0.040)

> Outside view: formal public bilateral oil-for-yuan agreements with explicit volume commitments have a near-zero historical base rate in any 30-day window; no state pair has achieved this format on that timeline even under sustained strategic pressure. China's unprecedented sanctions defiance order (Day 65) is the strongest positive signal and warrants a Bayesian update of roughly 2× above base, but a compliance directive to domestic firms is categorically different from a formal public agreement inviting maximum US secondary-sanctions targeting. The Hormuz yuan payment infrastructure ('at least two vessels paid in yuan') shows informal yuanization is advancing, but the scenario explicitly excludes these crude-swap and informal-credit arrangements. The binding constraint is China's structural preference for deniable informality: announcing explicit volume commitments publicly would expose Chinese entities to US sanctions enforcement in a way the compliance directive does not, and would directly undermine China's positioning as a neutral ceasefire mediator (Wang Yi–Araghchi meeting, Day 69). Fermi decomposition: P(China willing to formalize and publicize) ≈ 0.12 × P(Iran willing) ≈ 0.65 × P(terms agreed in 30 days if both willing) ≈ 0.45 × P(explicit volume commitment included) ≈ 0.35 ≈ 0.012; adjusted upward to 0.04 to account for the unprecedented China sanctions escalation and Trump–Xi summit pressure on 14–15 May as a possible catalyst for a provocative Chinese signal, but the formal/public/volume threshold remains the load-bearing constraint that base rates and China's diplomatic tradition both drive toward the low end.

#### schelling-bargaining (p=0.030)

> From a bargaining structure perspective, China's strategic leverage against the US in this conflict derives entirely from maintaining ambiguity. A formal, publicly announced bilateral oil-for-yuan settlement agreement with explicit volume commitments would convert China's current coercive posture — credible but deniable — into a fixed, attributable commitment that invites immediate US escalation and destroys China's negotiating room. China has already played its most credible informal commitment device (the May 3 formal order for firms to ignore US Iran sanctions); formalising further adds cost without adding coercive power. The Trump-Xi summit on 14-15 May falls squarely within the 30-day window and is specifically identified as expected to centre on Iran; a formal bilateral oil-for-yuan announcement in that window would constitute a focal point violation — handing Trump domestic justification for escalating against China right before both sides are trying to manage the relationship. The scenario specification (formal, public, explicit volume commitments, not informal credit) describes precisely the format China's sanctions-circumvention architecture is designed to avoid: informal directives, de facto yuan payments in Hormuz transit fees, and Caspian-route hardware deliveries already achieve the functional outcome without generating commitment costs. US Treasury sanctions of Chinese satellite firms on 10 May confirm the US is actively raising the price of Chinese support, reinforcing China's incentive to preserve deniability rather than formalise. The Schelling commitment problem is inverted here: Iran wants formalisation, China rationally refuses because ambiguity is more coercively valuable than a signed agreement.

#### wack-strategic (p=0.035)

> Predetermined elements cut sharply against this scenario. China's strategic ambiguity doctrine — avoiding formalised alignment during active US military operations against Iran — is a structural force, not a contingency. US secondary sanctions enforcement is operational; a public, formal yuan-settlement agreement with explicit volume commitments would maximise Chinese financial institution exposure, a risk China has consistently refused to accept during 72 days of active conflict. The scenario's own exclusions ('not crude swap, not informal credit') eliminate the informal, grey-channel mechanisms China actually deploys. The 30-day horizon adds a further structural barrier: Iranian government bandwidth is consumed by ceasefire mechanics, military operations, and regime stability, not trade architecture negotiations. The prior of 4% is approximately calibrated; my framework yields a marginally lower posterior (3.5%) because the public dual-announcement requirement — which is the scenario's distinguishing feature — is precisely the thing China's institutional playbook is designed to avoid.

### Aggregation + signed audit

```json
{
  "p_point": 0.035,
  "p_range": [
    0.03,
    0.04
  ],
  "divergence_pp": 1.0000000000000002,
  "divergence_flag": false
}
```

Signature (base64 Ed25519): `BP/1awe3f/RJEjY70yJIV+fMUgXy3BV6LYqTP2+bE6kufaUeyMZSSZ/+S+DGBqHOXzCd+hn5jSuWQ2cQw7rhAQ==`

## S3-houthi-redsea

**Scenario:** Houthi forces conduct a multi-vessel attack on commercial shipping in the Red Sea within the next 30 days that causes ≥3 vessel casualties (sunk, severely damaged, or crew casualties), prompting at least one Western navy to declare an Article 5-equivalent response posture.

**Intel-base hash:** `sha256:688028d990580189611326674316b847aa5a7a4953add4395a53b38d8c5263fc`

### Per-perspective outputs

| Perspective | p_point | interval | runtime (s) | evidence URLs |
|---|---|---|---|---|
| tetlock-forecaster | 0.030 | [0.01, 0.06] | 121.2 |  |
| schelling-bargaining | 0.020 | [0.01, 0.04] | 119.1 |  |
| wack-strategic | 0.016 | [0.01, 0.04] | 284.7 | [1](https://www.aljazeera.com/news/liveblog/2026/5/10/iran-war-live-irgc-warns-us-against-attacks-on-ships-israel-bombs-lebanon) [2](https://www.cnbc.com/2026/05/10/tanker-crosses-strait-of-hormuz-as-us-awaits-iran-response-.html) [3](https://www.bloomberg.com/news/articles/2026-05-10/us-awaits-iran-reply-as-aramco-says-hormuz-opening-no-quick-fix) |

### Reasoning (full text)

#### tetlock-forecaster (p=0.030)

> The scenario requires two conjunctive conditions, each independently improbable. First, a Trump-Houthi commercial shipping ceasefire has been in place since 6 May 2026 and held as of Day 72; breaking it and producing ≥3 vessel casualties in a coordinated multi-vessel attack within 30 days requires both ceasefire collapse (~35-40% probability) and a rare Houthi mass-casualty operation given their historical pattern of single-vessel targeting (~15-20% conditional probability). Second, and decisively, an Article 5-equivalent response posture from any Western navy is historically unprecedented: during 18+ months of Houthi Red Sea attacks that sank four vessels and disrupted global shipping, Operation Prosperity Guardian and its successors never produced a collective-defense invocation; the UK's HMS Dragon deployment is explicitly framed 'not NATO, not wider war'. The joint probability — ceasefire collapse × mass-casualty attack × Article 5-equivalent declaration — yields roughly 0.38 × 0.18 × 0.04 ≈ 0.003, lifted slightly by the IRGC 30-day deadline running to early June and the 35% B4 scenario weight, producing a point estimate of ~3%.

#### schelling-bargaining (p=0.020)

> A Houthi-US commercial shipping ceasefire has been in effect since 6 May (Day 69 of the conflict), representing a tacit Schelling bargain both sides have incentives to maintain while Iran-US negotiations over a 14-point MoU remain live. Breaking this focal point within 30 days requires either Iran signalling a green light (which would mean negotiations have effectively collapsed) or independent Houthi action without Tehran's approval — both conditioning events are possible but not probable on this horizon. Even conditional on ceasefire breakdown, achieving ≥3 vessel casualties in a concentrated multi-vessel attack is operationally demanding given current Houthi fire rates, and the Article 5-equivalent response threshold is a near-independent barrier: Western navies have operated continuously in the Red Sea under Operation Prosperity Guardian and similar missions without invoking collective-defence language even after vessel strikes, because commercial shipping vessels are not alliance territory and the commitment problem of invoking Article 5 against a non-state actor creates enormous precedent risk that NATO members would resist.

#### wack-strategic (p=0.016)

> Two conjunctive components, both severely constrained by predetermined elements. Component 1 (multi-vessel Houthi commercial shipping attack causing ≥3 casualties): an active Houthi-US commercial shipping ceasefire has been in force since 6 May 2026 — a near-predetermined structural barrier. The deal persists because it serves Houthi operational interests; breaking it within 30 days requires a specific catalyst not currently visible. Even conditional on breakdown, a single operation causing ≥3 vessel casualties (sunk, severely damaged, or crew casualties) would represent a threshold Houthis have historically not crossed in a single coordinated strike. Component 2 (Article 5-equivalent Western navy declaration): 2+ years of extensive Houthi attacks on commercial shipping, including strikes near US naval escorts, have produced zero Article 5-equivalent declarations — this is a near-predetermined institutional impossibility, not merely an unlikely event. Current US strategic overextension in the Hormuz theatre, Saudi Arabia's refusal of base access (Day 69), and documented allied reluctance to escalate further entrench this predetermined element. Joint probability of both components: substantially below the prior.

### Aggregation + signed audit

```json
{
  "p_point": 0.022000000000000002,
  "p_range": [
    0.016,
    0.03
  ],
  "divergence_pp": 1.4,
  "divergence_flag": false
}
```

Signature (base64 Ed25519): `oqLaHAT7zHLuyUOgpPDyxN9Lmb/XsFtCLfylXCDjA3I51xf3uSJUs8HPdR0/JYzKokKFfu5nANN4U4MubW+TAw==`

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