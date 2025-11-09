# GTA Search Parameters Reference

## Overview

This guide provides comprehensive documentation for all search parameters available in the `gta_search_interventions` tool. Use this reference to understand parameter purposes, relationships, and best practices for constructing effective queries.

**Quick Start:** Most queries use 3-5 parameters. Start with jurisdiction filters, add intervention types or MAST chapters, then refine with dates and other filters as needed.

---

## Core Filter Parameters

### Jurisdiction Filters

#### `implementing_jurisdictions`

**Purpose:** Filter interventions by countries that implemented the measure.

**Type:** List of ISO 3-letter country codes (e.g., `['USA', 'CHN', 'DEU']`)

**Examples:**
- US measures only: `implementing_jurisdictions=['USA']`
- US or China measures: `implementing_jurisdictions=['USA', 'CHN']`
- EU-level measures: `implementing_jurisdictions=['EU']`
- German national measures: `implementing_jurisdictions=['DEU']`

**See also:** `gta://reference/jurisdictions` for complete country code list

---

#### `affected_jurisdictions`

**Purpose:** Filter interventions by countries affected by the measure (target countries).

**Type:** List of ISO 3-letter country codes (e.g., `['USA', 'CHN', 'DEU']`)

**Examples:**
- Measures targeting China: `affected_jurisdictions=['CHN']`
- Measures affecting US exports: `affected_jurisdictions=['USA']`
- Global measures (all countries): Omit this parameter

**Note:** An intervention can affect multiple countries. This filter returns interventions where ANY of the specified countries are affected.

---

### Product & Sector Filters

#### `affected_products`

**Purpose:** Filter interventions affecting specific products using HS (Harmonized System) codes.

**Type:** List of 6-digit HS product codes as integers (e.g., `[292149, 292229]`)

**When to use:**
- ✅ For specific goods (steel, semiconductors, cars)
- ✅ When you have exact HS codes
- ❌ For services (use `affected_sectors` instead)
- ❌ For broad categories (use `affected_sectors` instead)

**Examples:**
- Semiconductors: `affected_products=[854110, 854121, 854129]`
- Motor vehicles: `affected_products=[870310, 870380]`
- Rice: `affected_products=[100630]`

**See also:** `gta://guide/cpc-vs-hs` for guidance on when to use HS codes vs CPC sectors

---

#### `affected_sectors`

**Purpose:** Filter interventions by CPC (Central Product Classification) sector codes or names. Provides broader coverage than HS codes and is REQUIRED for services.

**Type:** List of sector codes (integers) or names (strings), or mix of both

**When to use:**
- ✅ **REQUIRED for services** (financial, legal, transport, etc.)
- ✅ For broad product categories
- ✅ When you need comprehensive coverage
- ❌ When you need specific product-level precision (use HS codes)

**Format options:**
- By ID: `[11, 21, 711]` (Cereals, Live animals, Financial services)
- By name: `['Cereals', 'Financial services', 'Textiles']`
- Mixed: `[11, 'Financial services', 412]`
- Fuzzy matching supported: `'financial'` matches `'Financial services'`

**Examples:**

**Services (ID >= 500):**
- Financial services: `affected_sectors=[711, 712, 713, 714, 715, 716, 717]` or `['Financial services']`
- Telecommunications: `affected_sectors=[841, 842, 843, 844, 845, 846]`
- Education: `affected_sectors=[921, 922, 923, 924, 929]`
- Legal services: `affected_sectors=['Legal services']`

**Goods (ID < 500):**
- Agricultural products: `affected_sectors=[11, 12, 13, 14, 15, 16, 17, 18, 19]`
- Food products: `affected_sectors=[211, 212, 213, 214, 215, 216, 217, 218, 219]`
- Metals: `affected_sectors=[411, 412, 413, 414, 415, 416]`
- Transport equipment: `affected_sectors=[491, 492, 493, 494, 495, 496, 499]`

**See also:**
- `gta://reference/sectors-list` for complete sector list
- `gta://guide/cpc-vs-hs` for CPC vs HS guidance

---

### Intervention Type Filters

#### `intervention_types`

**Purpose:** Filter by specific types of trade measures.

**Type:** List of intervention type names (strings)

**When to use:**
- ✅ For **SPECIFIC** measures (e.g., "Import tariff" only, not all trade defense)
- ✅ When you need precise filtering
- ✅ For narrow analysis

**Common types:**
- `'Import tariff'` - Tariffs on imports
- `'Export subsidy'` - Direct export subsidies
- `'State aid'` - Government financial assistance
- `'Export ban'` - Prohibitions on exports
- `'Export licensing requirement'` - Required licenses for exports
- `'Financial grant'` - Direct grants to companies
- `'Import ban'` - Prohibitions on imports
- `'Quota'` - Quantitative restrictions
- `'State loan'` - Government loans

**Examples:**
- Import tariffs only: `intervention_types=['Import tariff']`
- Export controls: `intervention_types=['Export ban', 'Export licensing requirement']`
- Specific subsidy types: `intervention_types=['State aid', 'Financial grant']`

**See also:**
- `gta://reference/intervention-types` for complete list with descriptions
- `gta://reference/intervention-types-list` for quick reference

---

#### `mast_chapters`

**Purpose:** Filter by UN MAST (Multi-Agency Support Team) chapter classifications for broad categorization.

**Type:** List of chapter codes - accepts letters (A-P), integer IDs (1-20), or special categories

**When to use:**
- ✅ For **BROAD** categorization (e.g., "all subsidies", "all import measures")
- ✅ For comprehensive coverage across related types
- ✅ For generic queries
- ❌ For specific measures (use `intervention_types` instead)

**⚠️ CRITICAL DECISION: MAST vs intervention_types**

**Use `mast_chapters` when:**
- Query is generic: "subsidies", "trade barriers", "export controls"
- Need comprehensive coverage: All subsidy types, not just one
- Broad analysis: All Chapter L measures

**Use `intervention_types` when:**
- Query is specific: "Import tariff", "State aid"
- Need precision: Only specific measure types
- Narrow filtering: Exact intervention type required

**Format options:**
- Letters: `['A', 'B', 'L']` (recommended for standard chapters A-P)
- Integer IDs: `[1, 2, 10]` (API IDs 1-20)
- Special categories: `['Capital control measures', 'FDI measures', 'Migration measures', 'Tariff measures']`

**Examples:**
- All subsidies: `mast_chapters=['L']`
- All import barriers: `mast_chapters=['E', 'F']`
- Trade defense measures: `mast_chapters=['D']`
- Technical barriers: `mast_chapters=['A', 'B']` (SPS + TBT)
- Export controls: `mast_chapters=['P']`

**See also:** `gta://reference/mast-chapters` for complete taxonomy with detailed descriptions

---

### Evaluation & Status

#### `gta_evaluation`

**Purpose:** Filter by GTA's assessment of the intervention's impact on trade.

**Type:** List of evaluation colors

**Values:**
- `'Red'` - Harmful to trade (protectionist, discriminatory)
- `'Amber'` - Mixed or uncertain impact
- `'Green'` - Liberalizing (reduces trade barriers)

**Examples:**
- Harmful measures only: `gta_evaluation=['Red']`
- Liberalizing measures: `gta_evaluation=['Green']`
- Harmful or mixed: `gta_evaluation=['Red', 'Amber']`

---

#### `is_in_force`

**Purpose:** Filter by whether the intervention is currently active or has been removed/expired.

**Type:** Boolean

**Values:**
- `True` - Only interventions currently in force
- `False` - Only interventions that have been removed/expired
- `None` (default) - Both active and removed interventions

**Examples:**
- Current measures only: `is_in_force=True`
- Historical/removed measures: `is_in_force=False`
- All measures regardless of status: Omit parameter

---

### Date Filters

#### `date_announced_gte` / `date_announced_lte`

**Purpose:** Filter by announcement date (when the intervention was announced/published).

**Type:** String in ISO format (YYYY-MM-DD)

**When to use:** Most common date filter - announcement dates are available for nearly all interventions.

**Examples:**
- Announced in 2024 or later: `date_announced_gte='2024-01-01'`
- Announced before 2023: `date_announced_lte='2022-12-31'`
- Announced in 2024 only: `date_announced_gte='2024-01-01', date_announced_lte='2024-12-31'`

---

#### `date_implemented_gte` / `date_implemented_lte`

**Purpose:** Filter by implementation date (when the intervention came into effect).

**Type:** String in ISO format (YYYY-MM-DD)

**When to use:** When you need to know when measures actually took effect (not just when announced).

**⚠️ Note:** Implementation dates may be missing (NA) for some interventions.

**Examples:**
- Implemented in 2024: `date_implemented_gte='2024-01-01'`
- Effective before 2023: `date_implemented_lte='2022-12-31'`

**See also:** `gta://guide/date-fields` for detailed explanation of all date fields and when to use each

---

### Query Parameter

#### `query`

**Purpose:** Full-text search for entity names and specific products ONLY.

**Type:** String

**⚠️ CRITICAL: Use query ONLY after exhausting structured filters!**

**QUERY STRATEGY CASCADE:**

1. **START with structured filters:**
   - `intervention_types` - For policy types
   - `implementing_jurisdictions` / `affected_jurisdictions` - For countries
   - `affected_products` - For HS codes when known
   - `mast_chapters` - For broad categories
   - Date filters - For time periods

2. **THEN add query ONLY for:**
   - Company names: `'Tesla'`, `'Huawei'`, `'BYD'`, `'TSMC'`
   - Program names: `'Made in China 2025'`, `'Inflation Reduction Act'`
   - Technology names: `'ChatGPT'`, `'5G'`, `'CRISPR'`, `'artificial intelligence'`
   - Specific entities not capturable by filters

3. **DO NOT use query for:**
   - ❌ Intervention types (use `intervention_types` parameter)
   - ❌ Generic policy terms ('subsidy', 'tariff', 'ban')
   - ❌ Country names (use jurisdiction parameters)
   - ❌ Concepts covered by structured filters

**Query syntax:**
- OR logic: `'Tesla | BYD | Volkswagen'` (matches any)
- AND logic: `'artificial intelligence & export'` (requires both)
- Exact phrases: `'electric vehicle'`
- Wildcards: `'subsidi#'` (matches subsidy, subsidies, subsidize, etc.)
- Parentheses: `'(Tesla | SpaceX) & Musk'`

**✅ CORRECT examples:**
```python
# Tesla subsidies
query='Tesla', mast_chapters=['L'], implementing_jurisdictions=['USA']

# AI export controls
query='artificial intelligence | AI', intervention_types=['Export ban', 'Export licensing requirement']

# Huawei sanctions
query='Huawei', intervention_types=['Import ban', 'Export ban']
```

**❌ INCORRECT examples:**
```python
# DON'T put intervention types in query!
query='electric vehicles & subsidy'  # Use intervention_types instead

# DON'T put countries in query!
query='China & tariff'  # Use implementing_jurisdictions instead
```

**See also:** `gta://guide/query-syntax` for complete syntax reference and strategy guide

---

### Advanced Filters

#### `eligible_firms`

**Purpose:** Filter by types of firms eligible for or targeted by the intervention.

**Type:** List of firm type names (strings) or IDs (integers)

**Valid types:**
- `'all'` (ID: 1) - Policy applies to all types of companies
- `'SMEs'` (ID: 2) - Small and medium enterprises, entrepreneurs, start-ups
- `'firm-specific'` (ID: 3) - Targeting a specific company or specific project
- `'state-controlled'` (ID: 4) - Companies with >50% public ownership stake
- `'state trading enterprise'` (ID: 5) - Majority publicly owned with monopoly privileges
- `'sector-specific'` (ID: 6) - Firms in enumerated economic activity
- `'location-specific'` (ID: 7) - Firms in specific sub-national location
- `'processing trade'` (ID: 8) - Firms that import, process, and export

**Examples:**
- SME-targeted subsidies: `eligible_firms=['SMEs']`
- Company-specific incentives (e.g., Tesla): `eligible_firms=['firm-specific']`
- State-owned enterprises: `eligible_firms=['state-controlled']`
- Regional development: `eligible_firms=['location-specific']`

**See also:** `gta://reference/eligible-firms` for complete reference

---

#### `implementation_levels`

**Purpose:** Filter by government level implementing the intervention.

**Type:** List of level names (strings) or IDs (integers)

**Valid levels:**
- `'Supranational'` (ID: 1) - Supranational bodies (e.g., European Commission)
- `'National'` (ID: 2) - Central government agencies, including central banks
- `'Subnational'` (ID: 3) - Regional, state, provincial, or municipal governments
- `'SEZ'` (ID: 4) - Special economic zones
- `'IFI'` (ID: 5) - International financial institutions (multi-country ownership)
- `'NFI'` (ID: 6) - National financial institutions (e.g., Export-Import banks)

**Examples:**
- EU-wide measures: `implementation_levels=['Supranational']`
- National policies only: `implementation_levels=['National']`
- State/provincial actions: `implementation_levels=['Subnational']`
- Development bank programs: `implementation_levels=['NFI']`

**See also:** `gta://reference/implementation-levels` for complete reference

---

### Pagination & Format

#### `limit`

**Purpose:** Maximum number of results to return.

**Type:** Integer (1-1000)

**Default:** 50

**Examples:**
- Quick overview: `limit=10`
- Standard search: `limit=50`
- Comprehensive: `limit=100`
- Maximum: `limit=1000`

---

#### `offset`

**Purpose:** Number of results to skip (for pagination).

**Type:** Integer (>= 0)

**Default:** 0

**Examples:**
- First page: `offset=0`
- Second page (with limit=50): `offset=50`
- Third page: `offset=100`

---

#### `sorting`

**Purpose:** Sort order for results.

**Type:** String

**Default:** `'-date_announced'` (newest first - RECOMMENDED for recent data)

**Common values:**
- `'-date_announced'` - Newest announcements first
- `'date_announced'` - Oldest announcements first
- `'-intervention_id'` - Highest ID first
- `'intervention_id'` - Lowest ID first

**Valid sort fields:**
- `date_announced`
- `date_published`
- `date_implemented`
- `date_removed`
- `intervention_id`

**Note:** Use `-` prefix for descending order. Can combine multiple fields with commas.

---

#### `response_format`

**Purpose:** Output format for the response.

**Type:** String (enum)

**Values:**
- `'markdown'` (default) - Human-readable formatted text
- `'json'` - Machine-readable structured data

---

## Exclusion/Inclusion Controls (keep_* Parameters)

All filterable parameters have corresponding `keep_*` parameters that control whether values are INCLUDED or EXCLUDED.

**Pattern:**
- `keep_*=True` (default) - Include ONLY specified values
- `keep_*=False` - EXCLUDE specified values, show everything else

**Available keep parameters:**
- `keep_affected` - Control affected jurisdictions inclusion/exclusion
- `keep_implementer` - Control implementing jurisdictions inclusion/exclusion
- `keep_intervention_types` - Control intervention types inclusion/exclusion
- `keep_mast_chapters` - Control MAST chapters inclusion/exclusion
- `keep_implementation_level` - Control implementation levels inclusion/exclusion
- `keep_eligible_firms` - Control firm types inclusion/exclusion
- `keep_affected_sectors` - Control sectors inclusion/exclusion
- `keep_affected_products` - Control products inclusion/exclusion
- `keep_implementation_period_na` - Include/exclude interventions with no implementation date
- `keep_revocation_na` - Include/exclude interventions with no revocation date
- `keep_intervention_id` - Control specific intervention IDs inclusion/exclusion

**Examples:**
```python
# All measures EXCEPT those by China and USA
implementing_jurisdictions=['CHN', 'USA'], keep_implementer=False

# Non-tariff barriers only (exclude tariffs)
intervention_types=['Import tariff', 'Export tariff'], keep_intervention_types=False

# All products EXCEPT semiconductors
affected_products=[854110, 854121, 854129], keep_affected_products=False

# All sectors EXCEPT agriculture
affected_sectors=[11, 12, 13, 21, 22], keep_affected_sectors=False

# Only measures with known implementation dates
keep_implementation_period_na=False

# Exclude subsidies
mast_chapters=['L'], keep_mast_chapters=False
```

**See also:** `gta://guide/exclusion-filters` for comprehensive guide to exclusion logic

---

## Parameter Selection Strategy

### Start Simple, Add Complexity

**Step 1:** Jurisdictions
- Who implemented? → `implementing_jurisdictions`
- Who was affected? → `affected_jurisdictions`

**Step 2:** Policy Type
- Generic query? → `mast_chapters` (e.g., all subsidies = `['L']`)
- Specific type? → `intervention_types` (e.g., import tariffs only)

**Step 3:** Products/Sectors
- Specific goods? → `affected_products` (HS codes)
- Broad categories or services? → `affected_sectors` (CPC codes)

**Step 4:** Time Period
- Usually: `date_announced_gte` (most reliable)
- If needed: `date_implemented_gte`

**Step 5:** Refinement (optional)
- Entity names? → `query`
- Firm targeting? → `eligible_firms`
- Government level? → `implementation_levels`
- Impact assessment? → `gta_evaluation`

### Filter Precedence

**Most restrictive first:**
1. Jurisdictions (narrows geography)
2. Dates (narrows time period)
3. Policy types (narrows measure category)
4. Products/sectors (narrows target)
5. Advanced filters (further refinement)
6. Query (entity search within filtered set)

### Common Parameter Combinations

**Country subsidy analysis:**
```python
implementing_jurisdictions=['USA']
mast_chapters=['L']
date_announced_gte='2020-01-01'
```

**Bilateral tariff tracking:**
```python
implementing_jurisdictions=['USA']
affected_jurisdictions=['CHN']
intervention_types=['Import tariff']
date_announced_gte='2024-01-01'
```

**Sector-specific interventions:**
```python
affected_sectors=['Financial services']
gta_evaluation=['Red']
is_in_force=True
```

**Company-specific measures:**
```python
query='Tesla'
eligible_firms=['firm-specific']
implementing_jurisdictions=['USA']
```

---

## See Also

- **`gta://guide/query-examples`** - Comprehensive example library
- **`gta://guide/query-syntax`** - Query syntax reference
- **`gta://guide/query-strategy`** - Decision tree for query construction
- **`gta://guide/exclusion-filters`** - Keep_* parameter guide
- **`gta://guide/date-fields`** - Date field explanations
- **`gta://guide/cpc-vs-hs`** - CPC sectors vs HS codes
- **`gta://reference/mast-chapters`** - Complete MAST taxonomy
- **`gta://reference/jurisdictions`** - Country code reference
- **`gta://reference/intervention-types`** - Intervention type descriptions
- **`gta://reference/sectors-list`** - CPC sector list
- **`gta://reference/eligible-firms`** - Firm type reference
- **`gta://reference/implementation-levels`** - Implementation level reference
