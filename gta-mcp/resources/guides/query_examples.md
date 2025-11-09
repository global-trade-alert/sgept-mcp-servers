# GTA Query Examples Library

## Overview

This comprehensive library contains real-world query examples for the `gta_search_interventions` tool, organized by category. Use these examples as templates for constructing your own queries.

**How to use this guide:**
1. Find the category that matches your analysis goal
2. Copy the example closest to your needs
3. Modify parameters to fit your specific requirements
4. Refer to `gta://guide/parameters` for detailed parameter documentation

**Key principles demonstrated in these examples:**
- Use structured filters FIRST (jurisdictions, types, dates)
- Add `query` parameter ONLY for entity names not captured by filters
- Use `mast_chapters` for broad queries, `intervention_types` for specific measures
- Combine filters to narrow results progressively

---

## Basic Filtering Examples

### Example 1: Country-to-Country Tariffs with Time Filter

**Use case:** Track bilateral tariff measures over time

```python
implementing_jurisdictions=['USA']
affected_jurisdictions=['CHN']
intervention_types=['Import tariff']
date_announced_gte='2024-01-01'
```

**What this finds:** All import tariffs implemented by the United States that affect Chinese products, announced on or after January 1, 2024.

**When to use:** Bilateral trade policy analysis, tariff war tracking, specific country-pair relationships.

---

### Example 2: All Measures by Multiple Countries

**Use case:** Regional trade policy analysis

```python
implementing_jurisdictions=['USA', 'CAN', 'MEX']
date_announced_gte='2023-01-01'
```

**What this finds:** All trade measures implemented by the United States, Canada, or Mexico since January 2023.

**When to use:** NAFTA/USMCA analysis, regional trade policy trends, multi-country comparisons.

---

### Example 3: Measures Affecting a Specific Country

**Use case:** Identify all external pressures on a country

```python
affected_jurisdictions=['CHN']
gta_evaluation=['Red']
is_in_force=True
```

**What this finds:** All currently active harmful trade measures affecting China, implemented by any country.

**When to use:** Understanding trade restrictions faced by a country, market access analysis, defensive policy planning.

---

## MAST Chapter Queries (Broad Categorization)

### Example 4: All Subsidies from Any Country (BROAD)

**Use case:** Global subsidy landscape

```python
mast_chapters=['L']
```

**What this finds:** All subsidy measures (Chapter L) from all countries, all time periods.

**Why MAST:** Chapter L covers ALL subsidy types comprehensively (state aid, grants, tax breaks, loans, etc.). More comprehensive than listing specific intervention types.

**When to use:** Global subsidy analysis, comprehensive coverage needed, not focused on specific subsidy type.

---

### Example 5: EU Subsidies of All Types (BROAD)

**Use case:** EU state aid landscape

```python
implementing_jurisdictions=['EU']
mast_chapters=['L']
date_announced_gte='2020-01-01'
```

**What this finds:** All EU-level subsidy measures (supranational) announced since 2020, covering all subsidy types.

**When to use:** EU state aid policy analysis, comprehensive EU support measures, tracking European Commission decisions.

---

### Example 6: Trade Defense Measures Since 2020 (BROAD)

**Use case:** Global trade defense landscape

```python
mast_chapters=['D']
date_announced_gte='2020-01-01'
```

**What this finds:** All contingent trade-protective measures (Chapter D: anti-dumping, countervailing duties, safeguards) announced since 2020.

**Why MAST:** Chapter D covers all trade defense instruments. More comprehensive than specifying individual types.

**When to use:** Trade remedy trends, defensive trade policy analysis, protectionism monitoring.

---

### Example 7: All Import Restrictions Affecting US (BROAD)

**Use case:** Trade barriers faced by US exporters

```python
mast_chapters=['E', 'F']
affected_jurisdictions=['USA']
```

**What this finds:** All non-automatic licensing, quotas, prohibitions (E) and price-control measures (F) affecting US products or companies.

**Why MAST:** Chapters E and F cover all import restriction types. Comprehensive barrier analysis.

**When to use:** US export market access analysis, identifying trade barriers, comprehensive restriction mapping.

---

### Example 8: Technical Barriers (SPS and TBT)

**Use case:** Regulatory barrier analysis

```python
mast_chapters=['A', 'B']
affected_products=[100630]  # Rice
date_announced_gte='2023-01-01'
```

**What this finds:** All sanitary/phytosanitary measures (A) and technical barriers to trade (B) affecting rice products since 2023.

**Why MAST:** Chapters A and B cover all technical and regulatory measures. Essential for regulatory barrier analysis.

**When to use:** Standards and regulations analysis, technical barrier mapping, SPS/TBT compliance research.

---

## Specific Intervention Type Queries (Narrow Focus)

### Example 9: Specific German State Aid Only (NARROW)

**Use case:** Precise filtering for one intervention type

```python
implementing_jurisdictions=['DEU']
intervention_types=['State aid']
date_announced_gte='2020-01-01'
```

**What this finds:** ONLY state aid measures (not other subsidy types) from Germany since 2020.

**Why intervention_types:** When you need ONLY state aid, not export subsidies, grants, or other Chapter L measures.

**When to use:** Narrow subsidy type analysis, when specific measure type is the focus, comparing one type across countries.

---

### Example 10: Export Controls Only

**Use case:** Export restriction analysis

```python
intervention_types=['Export ban', 'Export licensing requirement']
date_announced_gte='2023-01-01'
```

**What this finds:** Only export bans and export licensing requirements (not other export measures).

**When to use:** Export control policy analysis, technology transfer restrictions, strategic goods monitoring.

---

### Example 11: Import Tariffs Only (Not Other Chapter P Measures)

**Use case:** Tariff-specific analysis

```python
intervention_types=['Import tariff']
implementing_jurisdictions=['USA']
date_announced_gte='2024-01-01'
```

**What this finds:** ONLY import tariffs, excluding export tariffs, tariff-rate quotas, and other tariff measures.

**When to use:** When you need precise tariff data without other measures, tariff rate analysis, specific measure type research.

---

## Entity Searches (Company/Program Names)

### Example 12: Tesla-Related Subsidies

**Use case:** Company-specific incentive analysis

```python
query='Tesla'
mast_chapters=['L']
implementing_jurisdictions=['USA']
```

**What this finds:** All US subsidy measures (Chapter L) that mention "Tesla" in title, description, or sources.

**Key pattern:** Structured filters (mast_chapters, jurisdictions) FIRST, then `query` for entity name.

**When to use:** Company-specific policy analysis, targeted incentive research, firm-level impact studies.

---

### Example 13: AI Export Controls

**Use case:** Technology-specific restrictions

```python
query='artificial intelligence | AI'
intervention_types=['Export ban', 'Export licensing requirement']
date_announced_gte='2023-01-01'
```

**What this finds:** Export bans and licensing requirements mentioning "artificial intelligence" OR "AI" since 2023.

**Key pattern:** OR logic in query (`|`) to catch variations. Structured filters narrow to export controls.

**When to use:** Technology export control analysis, strategic technology restrictions, dual-use goods monitoring.

---

### Example 14: Huawei Sanctions

**Use case:** Company-specific sanctions analysis

```python
query='Huawei'
intervention_types=['Import ban', 'Export ban']
affected_jurisdictions=['CHN']
```

**What this finds:** Import and export bans mentioning "Huawei" that affect China.

**When to use:** Entity-based sanctions analysis, company blacklist research, targeted restriction mapping.

---

### Example 15: Program Name Search

**Use case:** Named policy program tracking

```python
query='Inflation Reduction Act | IRA'
mast_chapters=['L']
date_announced_gte='2022-01-01'
```

**What this finds:** Subsidy measures mentioning "Inflation Reduction Act" or "IRA" since 2022.

**Key pattern:** Program name with acronym alternative using OR logic.

**When to use:** Policy program impact analysis, tracking specific legislation, program-linked measures.

---

## CPC Sector Queries (Services and Broad Categories)

### Example 16: Financial Services Interventions (SERVICES - REQUIRED)

**Use case:** Services sector analysis

```python
affected_sectors=['Financial services']
implementing_jurisdictions=['USA']
date_announced_gte='2020-01-01'
```

**What this finds:** All measures affecting financial services (CPC IDs 711-717) implemented by the US since 2020.

**⚠️ CRITICAL:** Services REQUIRE CPC sectors. HS codes only cover goods.

**When to use:** Financial sector policy analysis, service trade barriers, regulatory measures for services.

---

### Example 17: Agricultural Product Subsidies (BROAD - CPC sectors)

**Use case:** Broad agricultural support analysis

```python
affected_sectors=[11, 12, 13]
mast_chapters=['L']
date_announced_gte='2020-01-01'
```

**What this finds:** All subsidies affecting agricultural sectors (cereals, vegetables, fruits, nuts, etc.) since 2020.

**Why CPC:** Broader coverage than specific HS codes. Captures all agricultural products comprehensively.

**When to use:** Agricultural policy analysis, farm support measures, broad sector subsidy analysis.

---

### Example 18: Steel Industry Measures (CPC sectors for broad coverage)

**Use case:** Steel sector interventions

```python
affected_sectors=['Basic iron and steel', 'Products of iron or steel']
date_announced_gte='2020-01-01'
```

**What this finds:** All measures affecting basic iron/steel and steel products since 2020.

**Why CPC:** Captures all steel-related measures across different intervention types and sub-categories.

**When to use:** Steel industry analysis, metal sector policies, comprehensive sector coverage.

---

### Example 19: Technology Sector Restrictions (Services + Goods)

**Use case:** Technology sector analysis

```python
affected_sectors=['Telecommunications', 'Computing machinery']
gta_evaluation=['Red']
```

**What this finds:** Harmful measures affecting telecommunications services and computing machinery.

**Why CPC:** Captures both services (telecommunications) and goods (computing), which HS codes alone cannot.

**When to use:** Tech sector trade barriers, comprehensive technology policy analysis, digital economy measures.

---

## Firm Targeting & Implementation Levels

### Example 20: SME-Targeted Subsidies Only

**Use case:** Small business support analysis

```python
eligible_firms=['SMEs']
intervention_types=['State aid', 'Financial grant']
implementing_jurisdictions=['DEU']
```

**What this finds:** State aid and grants specifically targeting SMEs (small/medium enterprises) in Germany.

**When to use:** SME policy analysis, small business support measures, firm-size-specific incentives.

---

### Example 21: National-Level Policies (Exclude Subnational)

**Use case:** Federal/central government measures only

```python
implementation_levels=['National']
implementing_jurisdictions=['USA']
date_announced_gte='2023-01-01'
```

**What this finds:** Only national-level (federal) US measures since 2023, excluding state/local measures.

**When to use:** Federal policy analysis, distinguishing national from state measures, central government trends.

---

### Example 22: EU Commission Measures (Supranational)

**Use case:** EU-wide supranational policy

```python
implementation_levels=['Supranational']
implementing_jurisdictions=['EU']
```

**What this finds:** Only measures implemented at the EU Commission level (supranational), not member state national measures.

**When to use:** EU-level policy analysis, distinguishing EU Commission from member state measures, supranational governance.

---

### Example 23: State-Owned Enterprise Requirements

**Use case:** SOE-specific policies

```python
eligible_firms=['state-controlled']
implementing_jurisdictions=['CHN']
intervention_types=['State loan', 'Financial grant']
```

**What this finds:** State loans and grants targeting state-controlled companies (>50% public ownership) in China.

**When to use:** SOE policy analysis, state-controlled firm incentives, ownership-based measures.

---

### Example 24: Firm-Specific Measures (Named Companies)

**Use case:** Company-targeted interventions

```python
eligible_firms=['firm-specific']
implementing_jurisdictions=['USA']
mast_chapters=['L']
```

**What this finds:** Subsidies targeting specific companies or projects (not broad eligibility) in the US.

**When to use:** Company-specific incentive analysis, targeted support measures, project-based subsidies.

---

## Negative Queries (Exclusion Using keep Parameters)

### Example 25: All Measures EXCEPT Those by China and USA

**Use case:** Rest-of-world analysis

```python
implementing_jurisdictions=['CHN', 'USA']
keep_implementer=False
```

**What this finds:** All interventions from ANY country EXCEPT China and USA.

**Key pattern:** `keep_implementer=False` inverts the logic to EXCLUDE specified countries.

**When to use:** Excluding major players, rest-of-world analysis, non-superpower policy trends.

---

### Example 26: Non-Tariff Barriers Only (Exclude All Tariffs)

**Use case:** NTB analysis

```python
intervention_types=['Import tariff', 'Export tariff']
keep_intervention_types=False
```

**What this finds:** ALL intervention types EXCEPT import and export tariffs.

**Key pattern:** `keep_intervention_types=False` excludes specified types.

**When to use:** Non-tariff barrier analysis, regulatory measure focus, excluding tariff measures.

---

### Example 27: All Products EXCEPT Semiconductors

**Use case:** Non-semiconductor analysis

```python
affected_products=[854110, 854121, 854129]
keep_affected_products=False
```

**What this finds:** Measures affecting any products EXCEPT the specified semiconductor HS codes.

**When to use:** Excluding specific products, rest-of-economy analysis, non-targeted sector research.

---

### Example 28: All Sectors EXCEPT Agriculture

**Use case:** Non-agricultural economy

```python
affected_sectors=[11, 12, 13, 21, 22]
keep_affected_sectors=False
date_announced_gte='2023-01-01'
```

**What this finds:** All measures since 2023 affecting any sector EXCEPT agricultural and food sectors.

**When to use:** Non-agricultural policy, industrial/service focus, excluding farm measures.

---

### Example 29: Only Measures with Known Implementation Dates (Exclude NA)

**Use case:** Effective date analysis

```python
keep_implementation_period_na=False
implementing_jurisdictions=['USA']
date_implemented_gte='2024-01-01'
```

**What this finds:** Only US measures with actual implementation dates (excludes interventions with missing implementation date), implemented since 2024.

**Key pattern:** `keep_implementation_period_na=False` excludes measures without implementation dates.

**When to use:** Effective date analysis, excluding announced-but-not-implemented measures, timeline accuracy.

---

### Example 30: Non-Subsidy Measures (Exclude Subsidies)

**Use case:** All measures except support

```python
mast_chapters=['L']
keep_mast_chapters=False
```

**What this finds:** ALL interventions EXCEPT subsidy measures (Chapter L).

**When to use:** Restrictive measures only, excluding supportive policies, barrier-focused analysis.

---

## Advanced Combination Examples

### Example 31: Recent Protectionist Measures in Automotive Sector

**Use case:** Sector-specific protectionism tracking

```python
affected_products=[870310, 870320, 870380]  # Motor vehicles
gta_evaluation=['Red']
date_announced_gte='2023-01-01'
is_in_force=True
sorting='-date_announced'
```

**What this finds:** Currently active harmful measures affecting motor vehicles, announced since 2023, sorted newest first.

**When to use:** Current sector barriers, protectionism monitoring, recent trade restrictions.

---

### Example 32: EU Green Subsidies with Entity Search

**Use case:** Environmental support policies

```python
implementing_jurisdictions=['EU']
mast_chapters=['L']
query='green | renewable | clean energy | climate'
date_announced_gte='2020-01-01'
```

**What this finds:** EU subsidies mentioning green/renewable/clean energy/climate since 2020.

**Pattern:** Broad MAST filter + multi-term entity search with OR logic.

**When to use:** Environmental policy analysis, green transition support, climate-related incentives.

---

### Example 33: G7 Trade Defense Against Specific Country

**Use case:** Coordinated trade defense

```python
implementing_jurisdictions=['USA', 'CAN', 'GBR', 'FRA', 'DEU', 'ITA', 'JPN']
affected_jurisdictions=['CHN']
mast_chapters=['D']
date_announced_gte='2020-01-01'
```

**What this finds:** All trade defense measures (anti-dumping, safeguards, etc.) by G7 countries affecting China since 2020.

**When to use:** Coordinated policy analysis, multilateral trade defense, geopolitical policy alignment.

---

### Example 34: Subnational SME Support Measures

**Use case:** Regional/state SME programs

```python
implementation_levels=['Subnational']
eligible_firms=['SMEs']
mast_chapters=['L']
implementing_jurisdictions=['USA']
```

**What this finds:** State/regional (not federal) subsidy measures specifically targeting SMEs in the US.

**When to use:** Subnational policy analysis, regional support programs, state-level SME incentives.

---

### Example 35: Export Controls on Strategic Technologies (Complex Query)

**Use case:** Strategic export restrictions

```python
query='semiconductor | AI | quantum | hypersonic | biotech'
intervention_types=['Export ban', 'Export licensing requirement']
affected_jurisdictions=['CHN', 'RUS']
date_announced_gte='2022-01-01'
```

**What this finds:** Export bans and licensing requirements mentioning strategic technologies, affecting China or Russia, since 2022.

**Pattern:** Multi-term technology search + specific export control types + targeted countries + recent timeframe.

**When to use:** Strategic technology controls, geopolitical export restrictions, dual-use goods monitoring.

---

## Tips for Constructing Your Own Queries

### 1. Start Broad, Then Narrow

**Step 1:** Jurisdictions (who implemented/who affected?)
**Step 2:** Policy type (MAST chapters for broad, intervention_types for specific)
**Step 3:** Time period (date_announced_gte)
**Step 4:** Products/sectors (if relevant)
**Step 5:** Refinements (eligible_firms, implementation_levels, evaluation)
**Step 6:** Entity search (query parameter for names)

### 2. MAST vs Intervention Types Decision Tree

```
Is your query generic/broad?
├─ YES → Use mast_chapters
│   Examples: "all subsidies", "trade barriers", "export controls"
└─ NO → Use intervention_types
    Examples: "import tariff only", "state aid specifically"
```

### 3. When to Use Query Parameter

✅ **USE query for:**
- Company names: Tesla, Huawei, BYD
- Program names: Made in China 2025, IRA
- Technology names: AI, 5G, ChatGPT
- Specific entities not capturable by filters

❌ **DON'T use query for:**
- Intervention types (use intervention_types parameter)
- Country names (use jurisdiction parameters)
- Generic policy terms (use structured filters)

### 4. Keep Parameters for Exclusion

**Pattern:** Specify what to EXCLUDE, set `keep_*=False`

```python
# Exclude G7 countries
implementing_jurisdictions=['USA', 'CAN', 'GBR', 'FRA', 'DEU', 'ITA', 'JPN']
keep_implementer=False

# Exclude tariffs
intervention_types=['Import tariff', 'Export tariff']
keep_intervention_types=False
```

---

## See Also

- **`gta://guide/parameters`** - Detailed parameter documentation
- **`gta://guide/query-syntax`** - Query syntax reference
- **`gta://guide/query-strategy`** - Decision trees for query construction
- **`gta://reference/mast-chapters`** - Complete MAST taxonomy
- **`gta://reference/jurisdictions`** - Country code reference
- **`gta://reference/intervention-types`** - Intervention type descriptions
- **`gta://reference/sectors-list`** - CPC sector list
- **`gta://guide/date-fields`** - Date field explanations
- **`gta://guide/cpc-vs-hs`** - CPC vs HS code guidance
- **`gta://guide/exclusion-filters`** - Keep_* parameter guide
