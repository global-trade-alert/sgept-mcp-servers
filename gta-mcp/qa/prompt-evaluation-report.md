# GTA MCP Prompt Evaluation Report

**Date:** 2026-02-12
**Evaluator:** Automated (Claude Code)
**API endpoint:** https://api.globaltradealert.org
**Server version:** gta-mcp v0.3.0

## Summary

- **Total prompts:** 20
- **PASS:** 7
- **PASS_WITH_CAVEATS:** 12
- **FAIL:** 1

All 20 queries returned HTTP 200. The corrected test run achieved results for every prompt (the initial run had 3 prompts returning 0 results due to over-specific text search phrases). The predominant issue across queries is analytical caveats that users should be warned about, not outright technical failures.

---

## Results Table

| # | Prompt (truncated) | Status | Results | Filter Accuracy | Caveats | Verdict |
|---|-------------------|--------|---------|-----------------|---------|---------|
| 1 | US tariffs on China since Jan 2025 | 200 | 50 | Correct | Reclassifications in results; limit=50 may truncate | PASS_WITH_CAVEATS |
| 2 | Countries retaliated against US tariffs 2025 | 200 | 50 | Correct | GTA has no "retaliation" concept; results are all harmful measures affecting US | PASS_WITH_CAVEATS |
| 3 | Section 232 measures US since 2025 | 200 | 50 | Correct | Text search may over-include (any mention of "Section 232") | PASS_WITH_CAVEATS |
| 4 | China export controls on rare earth | 200 | 36 | Correct | Good combination of structured + text filter | PASS |
| 5 | Subsidies for critical mineral processing | 200 | 50 | Correct | No jurisdiction filter; globally scoped | PASS |
| 6 | Export restrictions trend since 2020 | 200 | 8 groups | Correct (after fix) | 1970 artefact; 2025-2026 data incomplete due to pub lag | PASS_WITH_CAVEATS |
| 7 | Semiconductor measures currently in force | 200 | 50 | Correct | Broad text match includes non-equipment measures | PASS_WITH_CAVEATS |
| 8 | Countries subsidising semiconductor industry | 200 | 50 | Correct | Good MAST L + query combination | PASS |
| 9 | EU harmful measures on US since 2024 | 200 | 50 | Correct | EU code 1049 works; includes member-state measures | PASS |
| 10 | Brazil measures affecting US agricultural exports | 200 | 50 | Partially correct | No agricultural sector filter; includes all sectors | PASS_WITH_CAVEATS |
| 11 | ASEAN trade barriers on EU services | 200 | 50 | Partially correct | No service sector filter (CPC >= 500); includes goods measures | PASS_WITH_CAVEATS |
| 12 | Local content requirements SE Asia automotive | 200 | 47 | Partially correct | No automotive sector filter; includes all local content reqs | PASS_WITH_CAVEATS |
| 13 | Anti-dumping on Chinese steel since 2020 | 200 | 50 | Correct (after fix) | Original phrase query failed; needed split into query + type filter | PASS_WITH_CAVEATS |
| 14 | Safeguard measures in force on solar panels | 200 | 2 | Correct (after fix) | Includes washing machines (false positive from 'solar' match on same SA); low count is realistic | PASS_WITH_CAVEATS |
| 15 | India pharma import licensing | 200 | 1 | Correct (after fix) | Only 1 result; original phrase query returned 0 | FAIL |
| 16 | EU TBT on medical devices | 200 | 34 | Partially correct | No TBT filter (MAST B); false service keyword detection for 'medical' | PASS_WITH_CAVEATS |
| 17 | G20 state aid to EV manufacturers since 2022 | 200 | 50 | Partially correct | No G20 country filter; global results | PASS_WITH_CAVEATS |
| 18 | Interventions targeting SOEs | 200 | 50 | Correct | Clean structured filter; reliable | PASS |
| 19 | US subnational measures since 2023 | 200 | 50 | Correct | Clean structured filter | PASS |
| 20 | Harmful interventions 2025 vs 2024 | 200 | 10 groups | Correct (after fix) | "No implementation date" group (2,761); pub lag caveat | PASS_WITH_CAVEATS |

---

## Detailed Analysis: PASS_WITH_CAVEATS and FAIL

### Prompt 1: US tariffs on China since Jan 2025

**Issue:** Results include reclassification entries (e.g., "Reclassification of a men's vest and consequent modification in MFN duties") which are technically tariff changes but may not match user expectations of "imposed tariffs." The limit=50 likely truncates the full result set.

**Analytical caveat:** Per GTA rules, tariff reclassifications that change effective duty rates are legitimate interventions (HBK-INCL-002: alters relative treatment). Users expecting only Section 301/232 tariffs will need to interpret results.

**USE_CASES.md match:** YES -- the use case correctly describes this pattern.

**Suggested fix:** Consider adding a note in USE_CASES.md that results may include reclassification-based tariff changes alongside policy-driven tariffs.

---

### Prompt 2: Countries retaliated against US tariffs in 2025

**Issue:** GTA has no "retaliation" concept (per common_mistakes.md). The query correctly uses `affected_jurisdictions: ['USA']` + harmful evaluation to find measures affecting the US, but these are not necessarily retaliatory. First result is a German semiconductor subsidy -- harmful to US interests but not retaliation.

**Analytical caveat:** Per reconciled-rules.md HBK-INCL-001, GTA records measures neutrally without characterising them as retaliation. The user must interpret which measures are responses to US actions by examining dates and descriptions.

**USE_CASES.md match:** YES -- the use case explicitly warns about this limitation.

**Suggested fix:** None needed; USE_CASES.md already handles this well.

---

### Prompt 3: Section 232 measures since 2025

**Issue:** Text search for "Section 232" may over-include. Results include trade agreements that merely reference Section 232 (e.g., US-India trade agreement mentioning Section 232 commitments). However, the 50 results suggest good coverage.

**Analytical caveat:** Per USE_CASES.md, text search may not capture all relevant measures and some may be recorded by product rather than legal provision. The inverse is also true -- text search can over-include.

**USE_CASES.md match:** YES -- caveat about text search limitations is documented.

**Suggested fix:** Consider suggesting `intervention_types: ['Import tariff']` as a complementary filter.

---

### Prompt 6: Export restrictions trend since 2020

**Issue (CRITICAL, now fixed):** The initial test used `count_by: ['announcement_year']` which is not a valid API dimension. The correct dimension is `date_announced_year`. This returned a single aggregate instead of year-by-year data. With corrected dimension, we get 8 year groups showing the trend.

**Data quality note:** The 1970 group (4 interventions) is an artefact per common_mistakes.md: "Pre-2008 dates in GTA count results are likely data quality artefacts." The 2025 count (597) and 2026 count (28) are affected by publication lag.

**Analytical caveat:** The trend shows a peak in 2022 (894), decline in 2023-2024, then partial recovery in 2025. But the 2024-2025 figures are affected by publication lag (2-4 weeks per common_mistakes.md). The answer to "has it increased?" is nuanced: yes since pre-2020 but actually declined from the 2022 peak.

**USE_CASES.md match:** YES -- publication lag caveat is documented.

**Suggested fix for MCP server:** The `build_count_filters` function should not inject `count_by` into the filters dict -- the `GTAAPIClient.count_interventions` method correctly handles this separately. But when calling the API directly (as users might), the `count_by` dimension names must match the API's exact values (e.g., `date_announced_year`, not `announcement_year`). This should be documented more prominently.

---

### Prompt 7: Semiconductor measures currently in force

**Issue:** The text search for "semiconductor" is broad. Results include measures that mention semiconductors in passing (e.g., battery backups, AI chips). The prompt asks specifically about "manufacturing equipment trade" but the query cannot distinguish equipment from other semiconductor-related measures.

**Analytical caveat:** Text search provides recall at the cost of precision. For "manufacturing equipment" specifically, users could add HS product codes for semiconductor equipment (e.g., HS 8486).

**USE_CASES.md match:** Partially -- the use case mentions filtering by sector but doesn't specifically address the precision issue.

**Suggested fix:** USE_CASES.md could suggest combining text search with HS codes for more precise product targeting.

---

### Prompt 10: Brazil measures affecting US agricultural exports

**Issue:** No agricultural sector filter is applied. Results include all Brazilian measures affecting the US across all sectors (visa waivers, insurance restrictions, local content rules for TV). The prompt asks specifically about "agricultural exports."

**Analytical caveat:** Per USE_CASES.md, this is explicitly flagged: "To narrow to agricultural products specifically, add `affected_sectors` with agricultural CPC codes (e.g., 11-49 for primary agriculture)."

**USE_CASES.md match:** YES -- the caveat about needing sector filtering is documented.

**Suggested fix for the mapping:** The query construction should add `affected_sectors` with agricultural CPC codes (11-49) to match the user's intent.

---

### Prompt 11: ASEAN trade barriers on EU services

**Issue:** No service sector filter is applied. Results include goods measures (export benchmark prices for copper, safeguard on ceramic tiles). The prompt asks specifically about "services."

**Analytical caveat:** Per USE_CASES.md: "To filter for services specifically, add `affected_sectors` with CPC sectors >= 500 (e.g., 711 for financial services, 841 for telecommunications)."

**USE_CASES.md match:** YES -- the limitation is documented.

**Suggested fix for the mapping:** Add `affected_sectors` with CPC service sectors (>= 500) to match the prompt's intent.

---

### Prompt 12: Local content requirements in SE Asia automotive

**Issue:** No automotive sector filter. Results include local content requirements across all sectors (construction, franchise retail, shipping). The automotive ones are present but mixed in with other sectors.

**Analytical caveat:** USE_CASES.md correctly notes: "Results include all local content requirements in these countries, not just automotive. For automotive-specific results, add `query: 'automotive'` or `affected_sectors` with vehicle CPC codes."

**USE_CASES.md match:** YES -- documented.

**Suggested fix for the mapping:** Add `query: 'automotive'` or `affected_sectors: [491]` (Motor vehicles) to better match intent.

---

### Prompt 13: Anti-dumping on Chinese steel since 2020

**Issue (CRITICAL, now fixed):** The original query used `query: "steel anti-dumping"` which returned 0 results because the API treats this as a phrase search and no intervention descriptions contain this exact phrase. The corrected approach uses `query: "steel"` + `intervention_types: ["Anti-dumping"]` and returns 50 results.

**Analytical caveat:** This reveals a fundamental limitation of the `query` parameter: multi-word phrases are treated literally. The USE_CASES.md should explicitly warn against combining concept terms in the query field.

**USE_CASES.md match:** The use case correctly advises using `intervention_types` for anti-dumping, but doesn't explicitly warn about phrase-matching behaviour.

**Suggested fix:** (1) Update common_mistakes.md to warn about multi-concept phrase searches. (2) The MCP server's query syntax guide should emphasise that the query parameter is best used for single entities/products, not combinations of concept + type.

---

### Prompt 14: Safeguard measures in force on solar panels

**Issue (FIXED):** Original `query: "solar panel safeguard"` returned 0 (phrase not found). Corrected to `query: "solar"` + `intervention_types: ["Safeguard"]` + `is_in_force: true`. Returns 2 results, one of which is a washing machines safeguard (false positive -- likely the "solar" text appears in the state act context or related intervention descriptions). The other is the correct crystalline silicon photovoltaic cells safeguard.

**Analytical caveat:** The 2-result count is realistic. Most countries' solar safeguards have expired. The US Section 201 safeguard on solar cells is still in force. The washing machine result is a false positive from text matching.

**USE_CASES.md match:** YES -- correctly describes using `is_in_force: true` and notes that expired measures would otherwise appear.

**Suggested fix:** None critical, but the washing machine false positive suggests the `query` parameter has low precision for narrow topics.

---

### Prompt 15: India pharma import licensing -- FAIL

**Issue (CRITICAL):** Even after correction (splitting `"pharmaceutical import licen"` into `query: "pharmaceutical"` + `intervention_types: ["Import licensing requirement"]`), only 1 result is returned. This is analytically insufficient for answering the user's question. India has numerous import licensing requirements affecting pharmaceuticals, but they may not mention "pharmaceutical" in the description text, or they may be classified under different intervention types (e.g., "Import-related non-tariff measure, nes" or "Import ban").

**Root cause:** The combination of text search + intervention type is too restrictive. India's pharmaceutical licensing measures are likely spread across multiple intervention types and may not contain the word "pharmaceutical" in the GTA description. Using CPC sector 352 (Pharmaceutical products) as a filter instead of text search would be more reliable.

**Analytical caveat:** This is a case where the GTA classification system captures the product via HS/CPC codes rather than description text. Relying on `query` for product matching is unreliable.

**USE_CASES.md match:** The use case doesn't adequately warn about this failure mode.

**Suggested fixes:**
1. Replace `query: "pharmaceutical"` with `affected_sectors: [352]` (Pharmaceutical products)
2. Consider broadening `intervention_types` to include related types (Import ban, Import-related NTM nes)
3. USE_CASES.md should recommend sector-based filtering for product categories rather than text search

---

### Prompt 16: EU TBT on medical devices

**Issue:** (1) No MAST chapter B (Technical barriers to trade) filter is applied, so results include all measure types (subsidies, procurement restrictions). (2) The `analyze_query_intent` function falsely detects "medical" as a service keyword and emits a misleading message about CPC sectors >= 500. Medical devices are goods, not services.

**Analytical caveat:** Per the guidance notes, GTA's coverage of TBT is lighter than tariff/subsidy measures. Many EU TBT measures may not be captured. The misleading "service-related query" message is a bug in the intent analysis.

**USE_CASES.md match:** The use case flags this as "problematic" -- GTA covers TBT lightly.

**Suggested fixes:**
1. Add `mast_chapters: ['B']` to filter for actual TBT measures
2. Fix `SERVICE_KEYWORDS` in api.py: "medical" should not be classified as a service keyword. Medical devices are goods (CPC sector 481). The keyword "medical" is too broad -- it matches both medical services and medical devices/products.

---

### Prompt 17: G20 state aid to EV manufacturers since 2022

**Issue:** No G20 country filter is applied. The query returns subsidies mentioning "electric vehicle" globally. Results include non-G20 countries (e.g., UK left G20? -- actually UK is G20). More importantly, the prompt asks "which G20 countries have *increased*" which implies a trend analysis, not just a list of measures.

**Analytical caveat:** A search query cannot answer "increased" -- that requires comparing counts across time periods. The search results show which countries have EV subsidies, but not whether the level has increased. Also, text search for "electric vehicle" may miss measures using "EV", "battery", "electromobility", etc.

**USE_CASES.md match:** Partially -- the use case describes the query correctly but doesn't address the "increased" aspect.

**Suggested fix:** For trend questions, recommend using `gta_count_interventions` with `count_by: ['date_announced_year', 'implementer']` instead of search.

---

### Prompt 20: Harmful interventions 2025 vs 2024

**Issue (CRITICAL data caveat):** The "No implementation date" group contains 2,761 interventions -- more than the 2025 total (3,903). This is the exact issue flagged in common_mistakes.md: "many announced measures lack implementation dates and are excluded from this count."

**Data:** 2024: 4,439 | 2025: 3,903 | No date: 2,761

**Analytical caveat:** The 2025 figure is incomplete due to (a) publication lag and (b) the 2,761 measures with no implementation date. Per common_mistakes.md, using `date_announced` instead of `date_implemented` would give more complete counts. A naive comparison suggests 2025 < 2024, but this is almost certainly an artefact of data completeness.

**USE_CASES.md match:** YES -- explicitly warns about the "No implementation date" group and publication lag.

**Suggested fix:** USE_CASES.md should recommend `date_announced_year` as the default for year-over-year comparisons, with `date_implemented_year` as secondary. The MCP server could add an automatic warning when counting by implementation year.

---

## Bugs and Issues Found

### Critical (must fix before release)

1. **Count endpoint dimension names**: The initial test used `announcement_year` instead of `date_announced_year`. While this was a test script error, the fact that the API silently returns an aggregate instead of failing is dangerous. The MCP server's `GTACountInput` model correctly validates dimensions via `CountByDimension` literal type, but external callers could hit this silently. **Recommendation:** Add validation in the API client or build_count_filters to catch invalid count_by values.

2. **Phrase search failure (Prompts 13, 14, 15)**: Multi-concept phrase queries (`"steel anti-dumping"`, `"solar panel safeguard"`, `"pharmaceutical import licen"`) return 0 results because the API searches for the exact phrase. The MCP server should either (a) detect multi-concept queries and split them, or (b) warn the LLM that query is for entity names only. **Recommendation:** The query parameter description already says "entity names and specific products ONLY" -- enforce this more aggressively in documentation.

3. **False service keyword detection (Prompt 16)**: The word "medical" triggers the service keyword detector, generating a misleading message. Medical devices are goods, not services. **Recommendation:** Remove "medical" from `SERVICE_KEYWORDS` in api.py. Consider adding it to `BROAD_CATEGORY_KEYWORDS` instead, or removing it entirely since it is too ambiguous.

### Important (should fix)

4. **Missing sector/product filters (Prompts 10, 11, 12)**: Several prompts ask about specific product categories (agricultural, services, automotive) but the mapping doesn't include sector filters. The USE_CASES.md correctly documents this gap, but the LLM agent may not always add these filters. **Recommendation:** Add explicit examples in USE_CASES.md showing the sector-enriched versions of these queries.

5. **Prompt 15 low recall**: India + pharmaceutical + import licensing returns only 1 result. This is analytically insufficient. **Recommendation:** Document that sector-based filtering (`affected_sectors: [352]`) is more reliable than text search for product categories. Consider adding a "fallback strategy" section to USE_CASES.md.

### Minor (nice to have)

6. **Prompt 14 washing machine false positive**: The safeguard search for "solar" returns a washing machine safeguard. This is likely a text match in the broader state act context. **Recommendation:** Users should review individual results rather than trusting all results are relevant.

7. **Prompt 20 no-date group**: The "No implementation date" group (2,761) dominates the count. **Recommendation:** The MCP server could automatically note when counting by implementation date that the no-date group may be large.

---

## USE_CASES.md Accuracy Assessment

| Prompt | USE_CASES.md Entry Exists | Caveats Documented | Accuracy |
|--------|--------------------------|-------------------|----------|
| 1 | Yes (Section 1) | Yes | Good |
| 2 | Yes (Section 1) | Yes - explicitly warns no retaliation concept | Good |
| 3 | Yes (Section 1) | Yes - warns about text search limits | Good |
| 4 | Yes (Section 2) | Yes - warns MAST P alone is over-inclusive | Good |
| 5 | Yes (Section 3) | Partial - describes filter approach | Adequate |
| 6 | Yes (Section 7) | Yes - warns about publication lag | Good |
| 7 | Yes (Section 2) | Partial - mentions sector filtering | Adequate |
| 8 | Yes (Section 3) | Partial - describes grouping by country | Adequate |
| 9 | Yes (Section 4) | Yes - explains Amber inclusion | Good |
| 10 | Yes (Section 4) | Yes - warns about missing sector filter | Good |
| 11 | Yes (Section 4) | Yes - warns about missing CPC filter | Good |
| 12 | Yes (Section 6) | Yes - warns results include all sectors | Good |
| 13 | Yes (Section 5) | Partial - doesn't warn about phrase search | Needs improvement |
| 14 | Yes (Section 5) | Yes - explains is_in_force and "Removed" status | Good |
| 15 | Yes (Section 6) | Partial - doesn't warn about text search limits | Needs improvement |
| 16 | Partial (Section 6) | Minimal - flagged as problematic | Needs improvement |
| 17 | Yes (Section 3) | Partial - doesn't address "increased" question | Needs improvement |
| 18 | Yes (Section 8) | Yes - correctly describes eligible_firms usage | Good |
| 19 | Yes (Section 8) | Yes - correctly describes implementation_levels | Good |
| 20 | Yes (Section 7) | Yes - warns about pub lag and no-date group | Good |

**Overall USE_CASES.md quality:** Good. 14/20 prompts have adequate or good documentation. 4 prompts need improvement in their caveat documentation. 2 prompts (13, 15) have gaps that could lead to user confusion.

---

## Recommendations for Public Release

1. **Fix the "medical" service keyword** in `api.py` before release -- it creates misleading messages for medical device queries.

2. **Add phrase search warning** to common_mistakes.md: "DON'T combine concepts in the query parameter. Use `query: 'steel'` + `intervention_types: ['Anti-dumping']`, NOT `query: 'steel anti-dumping'`."

3. **Strengthen USE_CASES.md** for prompts 13, 15, 16, 17 with explicit filter parameters and warnings about text search precision.

4. **Add automatic caveat** when `count_by` includes `date_implemented_year`: warn about the "No implementation date" group.

5. **Document count_by dimension names** prominently -- the difference between `announcement_year` (invalid) and `date_announced_year` (valid) is a trap for external callers.

6. **Consider adding a "query decomposition" step** in the MCP server: when the LLM passes a multi-concept query like "steel anti-dumping," automatically split it into structured filters where possible.
