## Summary

**FAIL.**

The spike is strong on probability sanity, isolation as reported, and most perspective differentiation, but it does **not** satisfy all required conditions. Two blockers prevent PASS:

1. **Wack framework integrity is incomplete:** the Wack outputs consistently use “predetermined elements,” but they do **not name or present signposts**, despite the criterion requiring Wack to include “predetermined elements + signposts.”
2. **Grounding fails for at least one perspective:** **S2-oil-yuan / wack-strategic** does not clearly reference at least two specific intelligence items; it relies mostly on generic structural claims.

---

## Criteria review

### 1. Framework integrity — **FAIL / partial**

**Tetlock-forecaster: PASS.**  
Tetlock outputs clearly use base rates, outside view, Fermi decomposition, and calibration language.

- **S1 tetlock:** “The historical base rate…” and “Fermi decomposition: P(Iran decides…)…”  
- **S2 tetlock:** “Outside view: formal public bilateral oil-for-yuan agreements…” and “Fermi decomposition: P(China willing…)…”  
- **S3 tetlock:** “The scenario requires two conjunctive conditions…” with explicit conditional estimates: “0.38 × 0.18 × 0.04…”

**Schelling-bargaining: PASS.**  
Schelling outputs reason in terms of coercion, credibility, commitment, bargaining structure, focal points.

- **S1 schelling:** “Iran's current coercive game is targeted at the US, Gulf shipping states, and Israel…” and “the Trump-Xi summit… is the dominant focal point…”  
- **S2 schelling:** “China's strategic leverage… derives entirely from maintaining ambiguity,” “commitment device,” “focal point violation,” and “commitment problem is inverted…”  
- **S3 schelling:** “A Houthi-US commercial shipping ceasefire… representing a tacit Schelling bargain…” and “Breaking this focal point…”

**Wack-strategic: FAIL / incomplete.**  
The Wack outputs do use predetermined-elements language, but they do **not** provide explicit signposts. The brief specifically requires Wack to name “predetermined elements + signposts.”

- **S1 wack:** “Wack's predetermined-vs-uncertain taxonomy identifies two structural constraints…” but no signposts are named.  
- **S2 wack:** “Predetermined elements cut sharply against this scenario…” but again no signposts.  
- **S3 wack:** “Two conjunctive components, both severely constrained by predetermined elements…” but no signpost set.

The Wack reasoning is directionally Wack-like, but it misses a required component of the framework.

---

### 2. Grounding — **FAIL**

Most outputs are grounded in specific intelligence items, but **S2-oil-yuan / wack-strategic** falls short of the required “at least 2 specific intelligence items” threshold.

Examples of strong grounding:

- **S1 tetlock:** cites “PWL-026,” “MuddyWater's new Dindoor backdoor,” “Unit 42's elevated wiper-attack warning,” “IRGC's 70% launcher attrition,” and “Trump-Xi summit on 14–15 May.”  
- **S2 schelling:** cites “the May 3 formal order for firms to ignore US Iran sanctions,” “Trump-Xi summit on 14-15 May,” “US Treasury sanctions of Chinese satellite firms on 10 May,” “Hormuz transit fees,” and “Caspian-route hardware deliveries.”  
- **S3 tetlock:** cites “Trump-Houthi commercial shipping ceasefire… since 6 May 2026,” “18+ months of Houthi Red Sea attacks,” “Operation Prosperity Guardian,” and “UK's HMS Dragon deployment.”

Grounding failure:

- **S2 wack** mostly says: “China's strategic ambiguity doctrine,” “US secondary sanctions enforcement is operational,” “72 days of active conflict,” and “Iranian government bandwidth is consumed by ceasefire mechanics, military operations, and regime stability.”  
  These are plausible but largely generic. It does not name the stronger available specific items used by the other S2 agents, such as the May 3 order, Day 65 sanctions-defiance order, Wang Yi–Araghchi meeting, Trump-Xi summit, yuan payments by vessels, or May 10 Treasury sanctions.

Therefore the “each perspective references at least 2 specific intelligence items” requirement is not met.

---

### 3. Independence — **PASS**

The three perspectives generally share a common intelligence spine while disagreeing through their own frameworks.

- **S1 shared spine:** Iran cyber capability, German neutrality, PWL-026/Dindoor, Trump-Xi summit.  
  - Tetlock emphasizes base rates and conjunctive probability.
  - Schelling emphasizes Germany not being a useful coercive target.
  - Wack emphasizes German non-belligerence and attribution-process friction.

- **S2 shared spine:** China prefers deniable support; formal public oil-for-yuan agreement is costly.  
  - Tetlock weights the unprecedented China sanctions signal upward.
  - Schelling frames ambiguity as China’s bargaining leverage.
  - Wack frames formalization as contrary to China’s structural playbook.

- **S3 shared spine:** Houthi ceasefire and Article 5-equivalent threshold.  
  - Tetlock decomposes ceasefire collapse × mass-casualty operation × Article 5 declaration.
  - Schelling frames the ceasefire as a tacit bargain/focal point.
  - Wack treats both the ceasefire and Article 5 reluctance as predetermined constraints.

There are repeated scenario-derived phrases such as “formal,” “public,” “explicit volume commitments,” and “Article 5-equivalent,” but not enough unusual verbatim overlap to create a copy-paste feel.

---

### 4. Isolation — **PASS with auditability caveat**

The artifact states:

- **S1 Isolation probe:** “Leak marker check: no-leak (PASS)”  
- It also says: “Both runs are recorded under `isolation/` and `isolation-with-prior/`.”

No marker leakage is visible in the captured reasoning. However, the actual paired isolation outputs are not included in the artifact, so this is accepted based on the artifact’s reported check rather than independently reverified from full transcripts.

No critical isolation failure is evident.

---

### 5. Probabilities sane — **PASS**

All `p_point` values are in `[0, 1]`, all intervals bracket the point estimates, and divergence flags are correct under the stated `max-min > 15pp` rule.

| Scenario | Points | Range | Max-min | Artifact divergence_pp | Flag | Correct? |
|---|---:|---:|---:|---:|---|---|
| S1-cyber-germany | 0.022, 0.015, 0.013 | [0.013, 0.022] | 0.009 = 0.9pp | 0.9 | false | Yes |
| S2-oil-yuan | 0.040, 0.030, 0.035 | [0.030, 0.040] | 0.010 = 1.0pp | 1.0 | false | Yes |
| S3-houthi-redsea | 0.030, 0.020, 0.016 | [0.016, 0.030] | 0.014 = 1.4pp | 1.4 | false | Yes |

---

## Scores

### Framework integrity scores

| Scenario | Tetlock | Schelling | Wack |
|---|---:|---:|---:|
| S1-cyber-germany | 5 | 5 | 3 |
| S2-oil-yuan | 5 | 5 | 3 |
| S3-houthi-redsea | 5 | 5 | 3 |

**Mean across all 9:** **4.33 / 5**

Rationale: Tetlock and Schelling are strong. Wack is recognizable but incomplete because signposts are absent.

---

### Grounding scores

| Scenario | Tetlock | Schelling | Wack |
|---|---:|---:|---:|
| S1-cyber-germany | 5 | 4 | 4 |
| S2-oil-yuan | 5 | 5 | 2 |
| S3-houthi-redsea | 5 | 4 | 4 |

**Mean across all 9:** **4.22 / 5**

Rationale: Most outputs cite multiple specific intelligence items. S2 Wack is the clear weak point.

---

### Disagreement quality

**Score: 4 / 5**

The agents disagree productively through different decompositions and causal weightings, while retaining a shared evidence spine. Divergence in numerical estimates is small, but the reasoning differences are meaningful and framework-specific.

---

### Production-readiness

**Score: 3 / 5**

The spike is promising but not ready for a paid pilot as-is. The main blockers are:

- Wack outputs need explicit signposts.
- Grounding enforcement should catch weak outputs like S2 Wack.
- The isolation probe should include the actual marker/no-marker transcript excerpts in the review artifact.
- Evidence URLs are mostly blank, though this was noted as a known caveat.

With those fixes, the subprocess pattern and aggregation behavior look directionally viable.
