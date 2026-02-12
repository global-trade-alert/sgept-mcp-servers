# Red Team Qualitative Evaluation Report

**Plan:** PLAN-2026-005 — GTA MCP Server v0.4.0 Public Release
**Date:** 2026-02-12
**Domain source:** `jf-thought/sgept-monitoring/gta/.claude/knowledge/` (reconciled rules, edge cases, monitoring standards)

---

## Why This Report Exists

The multi-pass evaluation report (`multipass-evaluation-report.md`) checks API plumbing: did the call return HTTP 200? Did the IDs come back? That is necessary but insufficient. It tells you the pipe works, not whether the water is clean.

This report evaluates whether the 20-prompt test suite produces **answers a trade policy professional would actually trust**. It applies the monitoring team's own analytical standards — particularly Monitoring Standard #1 ("Structured Filters First") and the domain knowledge encoded in the reconciled rule set and edge case library.

---

## Severity Definitions

| Level | Meaning |
|-------|---------|
| **CRITICAL** | User gets wrong answer or draws false conclusions. Blocks release. |
| **SIGNIFICANT** | Answer is materially incomplete or contaminated with noise. Should fix before release. |
| **MINOR** | Suboptimal but unlikely to mislead a domain user. Fix when convenient. |
| **GOOD** | Well-translated query; results match intent. |

---

## Per-Prompt Qualitative Assessment

### Prompt 1: "What tariffs has the US imposed on China since Jan 2025?"

**Filters:** `implementer: [840], affected: [156], intervention_types: [47], announcement_period: [2025-01-01, ...]`

**Verdict: GOOD**

All four dimensions of the question are captured. The `intervention_types: [47]` (Import tariff) is the correct structured filter per Monitoring Standard #1. Sample titles show reclassification/MFN duty changes — these are technically tariffs imposed on China, even if a user might primarily expect the headline Section 301 actions. Those should also appear in the result set alongside these reclassifications.

One subtlety: using `announcement_period` rather than `implementation_period` is the right choice per Monitoring Standard #3 ("use `date_announced_gte` for 'what's new' scans").

---

### Prompt 2: "Which countries have imposed tariffs affecting US exports in 2025?"

**Filters:** `affected: [840], intervention_types: [47], announcement_period: [2025-01-01, 2025-12-31]`

**Verdict: SIGNIFICANT — includes liberalising measures**

Good structure: no `implementer` constraint (since the question asks "which countries"), correct intervention type, bounded date range. But 623 results include **Green (liberalising) tariff changes** — the Australian sample record is evaluated Green (tariff concession). A user asking "which countries have imposed tariffs affecting US exports" expects harmful measures. Missing `gta_evaluation: [4]` (harmful = Red + Amber).

Per Monitoring Standard #5 and the reconciled rules (HBK-EVAL-001, API-EVAL-002): `gta_evaluation: [4]` is the correct filter for "harmful" measures, capturing both Red (certainly harmful) and Amber (likely harmful).

**Fix:** Add `gta_evaluation: [4]` to the filter set for this prompt.

---

### Prompt 3: "What export controls has China imposed on rare earth elements?"

**Filters:** `implementer: [156], mast_chapters: [14], query: "rare earth"`

**Verdict: GOOD**

Follows Monitoring Standard #1 correctly: structured filter (`mast_chapters: [14]` for export-related MAST chapter P) first, then `query: "rare earth"` only for the product-specific narrowing that structured filters cannot capture (no single HS code covers all rare earths). 36 results with relevant titles. Solid translation.

---

### Prompt 4: "Which countries have restricted exports of lithium or cobalt since 2022?"

**Filters:** `mast_chapters: [14], query: "lithium cobalt", announcement_period: [2022-01-01, ...]`

**Verdict: CRITICAL — zero results, query logic failure**

Returns 0 results. The `query: "lithium cobalt"` performs an AND-style or phrase match, requiring both terms. But the user means "lithium OR cobalt." Per Monitoring Standard #1, this should use **HS product codes** for lithium (e.g., 282520 lithium oxide, 283691 lithium carbonate) and cobalt (e.g., 810520 cobalt mattes), not free-text search.

The monitoring standards are explicit: "Free-text query searches intervention descriptions and may miss relevant results or return false positives." This is a textbook case of why.

**Fix:** Replace `query: "lithium cobalt"` with `affected_products: [282520, 283691, 810520, ...]` or run two separate queries (one for lithium, one for cobalt) and merge results.

---

### Prompt 5: "What measures currently affect semiconductor manufacturing equipment trade?"

**Filters:** `query: "semiconductor", in_force_on_date: "2026-02-12"`

**Verdict: SIGNIFICANT — overly broad, violates Monitoring Standard #1**

747 results using only a free-text query. No structured filter for intervention type, MAST chapter, sector, or product. The monitoring standards say: "Always use GTA structured query parameters before the free-text `query` parameter." Sample titles include deeptech VC investments, AI chip imports, and KRW 22 trillion general AI programmes — tangentially related at best to "semiconductor manufacturing equipment trade."

The prompt asks specifically about **trade** in **manufacturing equipment**. This should use:
- HS product codes for semiconductor manufacturing equipment (e.g., 848620 for wafer processing machines)
- Or at minimum, intervention types related to trade (tariffs, export controls, licensing)
- Or MAST chapters for trade restrictions (D, E, P) rather than all types including subsidies

**Fix:** Add structured filters. At minimum `mast_chapters` or `intervention_types` to narrow from "everything mentioning semiconductor" to trade measures specifically.

---

### Prompt 6: "What subsidies are governments providing for critical mineral processing?"

**Filters:** `mast_chapters: [10], query: "critical mineral"`

**Verdict: GOOD**

Correct application of Monitoring Standard #1: structured filter first (`mast_chapters: [10]` = MAST chapter L, subsidies), then text query for product narrowing. 191 results with highly relevant titles (EXIM critical minerals reserve, Australian mineral investments, Canadian critical materials funding). One of the best-translated prompts.

---

### Prompt 7: "Which countries subsidise their domestic semiconductor industry?"

**Filters:** `query: "semiconductor", in_force_on_date: "2026-02-12"`

**Verdict: CRITICAL — identical to Prompt 5, missing subsidy filter**

Produces **identical filters and identical 747 results** as Prompt 5 (semiconductor manufacturing equipment trade). The prompt explicitly says "subsidise" but no `mast_chapters: [10]` (subsidies) filter is applied. Compare with Prompt 6, which correctly uses `mast_chapters: [10]` for "subsidies."

The 747 results include export controls, import tariffs, FDI rules, and other non-subsidy measures. A trade policy professional asking about semiconductor subsidies would expect subsidy-type interventions only. Receiving the same results as a completely different question is a red flag.

Per the reconciled rules (HBK-MAST-001): each intervention type maps to exactly one MAST chapter. Subsidies are chapter L, which maps to `mast_chapters: [10]` in the API.

**Fix:** Add `mast_chapters: [10]` to match "subsidise" in the prompt. This alone would likely reduce 747 results to a more manageable and relevant set.

---

### Prompt 8: "Which G20 countries have increased state aid to EV manufacturers since 2022?"

**Filters:** `mast_chapters: [10], query: "electric vehicle", announcement_period: [2022-01-01, ...]`

**Verdict: SIGNIFICANT — missing G20 implementer constraint**

Good subsidy filter (mast_chapters: [10]). But the prompt says "G20 countries" and no `implementer` constraint is applied. Results include Hungary (not G20), Australia (G20 since 2023 only), and others. A domain user knows the G20 composition; returning non-G20 results erodes trust.

Per Monitoring Standard #4 ("Jurisdiction Precision"): the implementing jurisdiction should match the question. The G20 membership is a known set: ARG, AUS, BRA, CAN, CHN, FRA, DEU, IND, IDN, ITA, JPN, MEX, KOR, RUS, SAU, ZAF, TUR, GBR, USA, EU.

**Fix:** Add `implementer` with G20 country codes.

---

### Prompt 9: "What harmful measures has the EU imposed on US exports since 2024?"

**Filters:** `implementer: [1049], affected: [840], gta_evaluation: [4], announcement_period: [2024-01-01, ...]`

**Verdict: GOOD**

Excellent. All four dimensions captured. The `gta_evaluation: [4]` correctly filters for harmful (Red + Amber) per API-EVAL-002. EU as implementer, US as affected, date bounded. Sample titles show EU state aid measures — correctly classified as harmful to US commercial interests per HBK-EVAL-001 (discriminatory subsidies favour domestic firms over foreign competitors).

A non-expert might be surprised to see "Germany: EUR 920 million grant to Infineon" as a measure the EU "imposed on US exports." This is a real explanation challenge for the MCP server's documentation: GTA evaluates the **commercial impact**, not the stated intent. A German semiconductor subsidy harms US semiconductor exporters because their European competitors receive subsidised production. This is a documentation/education issue, not a query issue.

---

### Prompt 10: "What measures has Brazil implemented affecting US agricultural exports?"

**Filters:** `implementer: [76], affected: [840], announcement_period: [1900-01-01, ...]`

**Verdict: CRITICAL — no agricultural filter, 1000 noise results**

Returns ALL 1000 (ceiling-hit) measures where Brazil affects the US. No filter for agriculture. Sample titles include electric motor quotas, battery storage BNDES loans, and generic tariff modifications. The user asked specifically about "agricultural exports" but receives results about every sector.

Per Monitoring Standard #7 ("HS Codes vs CPC Sectors"): agriculture should use HS chapters 01-24 or CPC sectors 01-25. The monitoring team routinely filters by product/sector when analysing specific industries.

The Pass 2 sample record happens to be agricultural (MODERFROTA scheme) — one lucky hit in 1000 generic results. A domain user would immediately see the noise.

**Fix:** Add `affected_products` with HS chapters for agriculture (0101-2400 range), or `affected_sectors` with agricultural CPC sectors.

---

### Prompt 11: "Find all anti-dumping investigations targeting Chinese steel since 2020"

**Filters:** `affected: [156], intervention_types: [51], query: "steel", announcement_period: [2020-01-01, ...]`

**Verdict: GOOD**

Follows Monitoring Standard #1 correctly. Structured filters handle the intervention type (anti-dumping), affected jurisdiction (China), and date. The `query: "steel"` is appropriate because steel products span many HS codes and a text search is the most practical narrowing strategy. 98 results with highly relevant titles (AD investigations on flat-rolled steel, welded mesh, silicomanganese from China).

Per EC-CLASS-004 (edge case library): anti-dumping investigations should be Amber. The results would correctly reflect this.

---

### Prompt 12: "What safeguard measures are currently in force on solar panels?"

**Filters:** `intervention_types: [52], query: "solar", in_force_on_date: "2026-02-12"`

**Verdict: MINOR — false positive from text search**

Only 2 results, but one is about **washing machines** (US safeguard on large residential washing machines). The text query "solar" matched somewhere in that record's description/metadata, not the title. This is the classic false positive that Monitoring Standard #1 warns about.

For a user asking about solar panels, seeing a washing machine result is confusing. However, with only 2 results, the user can easily identify and ignore the irrelevant one.

**Fix:** Use HS product codes for solar panels (e.g., 854140 for photovoltaic cells) instead of or in addition to `query: "solar"`.

---

### Prompt 13: "What local content requirements affect automotive production in Southeast Asia?"

**Filters:** `implementer: [360, 764, 704, 458, 608], intervention_types: [28]`

**Verdict: SIGNIFICANT — no automotive filter**

Good SE Asia country mapping (Indonesia, Thailand, Vietnam, Malaysia, Philippines). Correct intervention type for local content requirements. But **no automotive filter** — results include LCRs for shipping, telecommunications, corn/wheat absorption, and other non-automotive sectors.

Per Monitoring Standard #7: automotive production should use HS chapter 87 (vehicles) or relevant CPC sectors. The monitoring team's country analyst agent shows the standard pattern: always include sector/product filters when the question specifies a sector.

**Fix:** Add `query: "automotive"` or `affected_products` with HS chapter 87 codes.

---

### Prompt 14: "What import licensing requirements affect pharmaceutical products in India?"

**Filters:** `implementer: [699], intervention_types: [36], query: "pharmaceutical"`

**Verdict: GOOD**

Precise. India correctly coded as 699 (per EC-JURIS-002 from the edge case library). Structured type filter + text query for product narrowing. Only 1 result, directly relevant. The small result count is expected — import licensing requirements specifically mentioning pharmaceuticals in India is a narrow query.

---

### Prompt 15: "Has the use of export restrictions increased since 2020?"

**Verdict: GOOD (count query)**

Uses `mast_chapters: [14]` (MAST chapter P, export-related) and counts by announcement year. Returns 20 groups with clear trend data (2022 peak at 1100, post-2020 generally elevated). A domain user could directly answer the question from this data.

---

### Prompt 16: "How many harmful interventions were implemented globally in 2025 versus 2024?"

**Verdict: GOOD (count query)**

Uses `gta_evaluation: [4]` (harmful = Red + Amber) and `implementation_period` for the correct date dimension. Returns 3,903 for 2025 vs 4,439 for 2024. Clear, directly answerable.

One caveat per the common mistakes guide: the "No implementation date" group (2,760) means many interventions lack implementation dates and are excluded from this comparison. An honest answer should note this.

---

### Prompt 17: "Which interventions target state-owned enterprises specifically?"

**Filters:** `eligible_firms: [4]`

**Verdict: GOOD**

Uses the correct structured field per HBK-FIRM-001: eligible firms category 4 = state-controlled enterprises. No text query needed. 158 results. Clean use of a structured filter for a question that maps directly to a GTA field.

---

### Prompt 18: "What subnational measures has the US implemented since 2023?"

**Filters:** `implementer: [840], implementation_level: [3], announcement_period: [2023-01-01, ...]`

**Verdict: GOOD**

Excellent. Uses `implementation_level: [3]` (subnational) — the correct structured field per API-IMPL-001. Sample titles are all US state-level measures (Texas, Indiana, California). Per EC-JURIS-005: subnational title format should be "Country (Subnational): Action" — and the results confirm this format.

---

### Prompt 19: "What FDI screening measures target Chinese investments in European technology sectors?"

**Filters:** `affected: [156], intervention_types: [25], query: "technology"`

**Verdict: SIGNIFICANT — missing European implementer constraint**

The prompt says "European technology sectors" but no implementer filter restricts results to European countries. Results include USA, India, and other non-European implementers. Only 2 of 5 results are European (EU and Germany).

Per Monitoring Standard #4 ("Jurisdiction Precision"): `implementing_jurisdictions` should capture the "European" constraint. At minimum, `implementer: [1049]` (EU), or all EU-27 member state codes plus UK, Norway, Switzerland.

**Fix:** Add European implementer codes.

---

### Prompt 20: "What measures have G7 countries coordinated against Russia since February 2022?"

**Filters:** `implementer: [840, 826, 251, 276, 381, 392, 124], affected: [643], announcement_period: [2022-02-01, ...]`

**Verdict: MINOR — structurally correct but very broad**

Good G7 country mapping (all 7 correct). Russia as affected is correct. Date from February 2022 matches. The 1000-result ceiling is hit because this captures ALL G7 measures affecting Russia — not just sanctions but also domestic subsidies that GTA classifies as affecting Russian commercial interests.

The word "coordinated" cannot be captured structurally. A domain user would understand that "coordinated" is an analytical judgment the LLM makes during triage, not something the API can filter. The overview table gives the LLM enough material to identify truly coordinated (concurrent, similar-type) measures across multiple G7 implementers.

---

## Summary of Findings

### Severity Distribution

| Severity | Count | Prompts |
|----------|-------|---------|
| **CRITICAL** | 3 | 4 (zero results), 7 (duplicate of 5), 10 (no sector filter) |
| **SIGNIFICANT** | 4 | 2 (includes Green), 5 (no structured filter), 8 (no G20 constraint), 13 (no automotive filter), 19 (no European constraint) |
| **MINOR** | 2 | 12 (false positive), 20 (very broad) |
| **GOOD** | 11 | 1, 3, 6, 9, 11, 14, 15, 16, 17, 18 |

### Root Cause Analysis

The issues cluster into three patterns:

#### Pattern A: Missing structured filter for a key concept in the prompt (5 prompts)

| Prompt | Missing filter | Concept in prompt |
|--------|---------------|-------------------|
| 2 | `gta_evaluation: [4]` | "imposed" (implies harmful) |
| 7 | `mast_chapters: [10]` | "subsidise" |
| 8 | `implementer: [G20 codes]` | "G20 countries" |
| 10 | HS/CPC agriculture codes | "agricultural exports" |
| 13 | HS ch.87 or `query: "automotive"` | "automotive production" |

This violates **Monitoring Standard #1**: "Always use GTA structured query parameters before the free-text `query` parameter."

#### Pattern B: Relying on free-text `query` where structured filters exist (2 prompts)

| Prompt | What `query` does | What should be used |
|--------|-------------------|---------------------|
| 4 | `"lithium cobalt"` (AND/phrase) | `affected_products` with HS codes for lithium and cobalt |
| 5 | `"semiconductor"` (broad text match) | MAST chapters for trade measures + HS codes for equipment |

This is the exact failure mode the monitoring standards predict: "Free-text query may miss relevant results or return false positives."

#### Pattern C: Missing implementer constraint for geographic scope (2 prompts)

| Prompt | Missing constraint | Concept in prompt |
|--------|-------------------|-------------------|
| 8 | G20 country codes | "G20 countries" |
| 19 | European country codes | "European technology sectors" |

Per **Monitoring Standard #4**: "implementing_jurisdictions = who enacted the measure."

### What This Means for Public Release

These findings reveal a gap not in the **MCP server** (which correctly returns what the API provides for the given filters) but in how well a **non-expert LLM user** would construct queries. The test script simulates what Claude might do when translating natural language to API parameters — and it gets it right 55% of the time (11/20) and materially wrong 35% of the time (7/20).

This has direct implications for the documentation:

1. **USE_CASES.md prompts should include the expected filters** — not just the natural language, but "Claude will use these parameters: ..." so users can verify.

2. **The search strategy guide should emphasise Pattern A explicitly** — "if your question mentions a measure type, always map it to a MAST chapter or intervention type filter."

3. **The common mistakes guide should add a 'Query vs Filters' warning** — showing the lithium/cobalt example as a case where free-text fails.

4. **The glossary should define "query parameter" clearly** — it is a description search, not an intelligent NLP search.

---

## Recommendations

### Must-fix before release (CRITICAL)

1. **Prompt 4:** Document that commodity-specific queries should use HS product codes, not free-text `query`. Add examples to the search strategy guide showing HS code lookup patterns for common commodities (rare earths, lithium, cobalt, steel, semiconductors).

2. **Prompt 7:** The documentation should show that "subsidies" maps to `mast_chapters: [10]` or specific `intervention_types` (Financial grant, State loan, Tax relief, etc.). This is the most common mapping a user needs.

3. **Prompt 10:** Add guidance that sector-specific queries (agriculture, automotive, pharmaceuticals) should always include HS product codes or CPC sectors.

### Should-fix before release (SIGNIFICANT)

4. **Search strategy guide update:** Add a "Natural Language to Filters" cheat sheet:
   - "subsidies" → `mast_chapters: [10]`
   - "tariffs" → `intervention_types: [47]` or `mast_chapters: [3]`
   - "export controls" → `mast_chapters: [14]`
   - "harmful/restrictive" → `gta_evaluation: [4]`
   - "G7/G20/EU/BRICS" → specific implementer code lists
   - "agricultural" → HS chapters 01-24
   - "automotive" → HS chapter 87
   - "semiconductors" → HS 8541, 8542

5. **Common mistakes guide update:** Add the "query is not NLP" mistake with the lithium/cobalt zero-result example.

### Nice to have

6. Update the test script itself to use correct filters, so future evaluations measure answer quality not just API success.

---

## Comparison with Monitoring Team Standards

| Monitoring Standard | Compliance in test suite |
|--------------------|-----------------------|
| #1 Structured Filters First | **7/20 violate** — rely on `query` where structured filters should be primary |
| #2 Reference Lists Are Sacred | N/A (test script doesn't check reference output) |
| #3 Date Discipline | **Good** — most prompts correctly choose announcement vs implementation |
| #4 Jurisdiction Precision | **2/20 violate** — missing implementer constraints |
| #5 Evaluation Colours | **1/20 violates** — Prompt 2 should filter for harmful |
| #6 MAST Chapters vs Types | **Partially followed** — some correct (6, 8), some miss it (5, 7) |
| #7 HS Codes vs CPC Sectors | **3/20 violate** — agriculture, automotive, commodities missing |
| #8 Balanced Reporting | N/A (test script doesn't assess output framing) |

---

## Conclusion

The MCP server itself works correctly. The documentation needs to do more work **bridging the gap between natural language questions and the structured query language GTA requires**. Non-expert users will write prompts like "What subsidies affect semiconductors?" and expect Claude to know that "subsidies" = MAST chapter L. The server cannot fix bad filters — but the documentation can teach both Claude and users how to construct good ones.

The search strategy guide, common mistakes guide, and USE_CASES.md are the right vehicles for this. The specific additions recommended above would address the three root cause patterns identified in this evaluation.
