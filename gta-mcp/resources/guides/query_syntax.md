# GTA Query Syntax and Strategy Guide

## Overview

The `query` parameter enables full-text search across intervention titles, descriptions, and sources. However, it should be used **strategically and sparingly** - structured filters are almost always more effective.

**Key Principle**: Structured filters FIRST, query parameter ONLY for named entities not captured by standard filters.

---

## The 3-Step Query Strategy Cascade

Follow this cascade for EVERY search:

### Step 1: Start with Structured Filters ✅

**ALWAYS begin with these parameters:**

| Filter Type | Parameters | Examples |
|-------------|-----------|----------|
| **Policy Types** | `intervention_types`, `mast_chapters` | `['Import tariff']`, `['L']` (subsidies) |
| **Countries** | `implementing_jurisdictions`, `affected_jurisdictions` | `['USA']`, `['CHN']` |
| **Products** | `affected_products` (HS codes), `affected_sectors` (CPC sectors) | `[870310]` (cars), `['Financial services']` |
| **Dates** | `date_announced_gte`, `date_announced_lte`, `date_implemented_gte` | `'2024-01-01'` |
| **Evaluation** | `gta_evaluation` | `['Red']` (harmful), `['Green']` (liberalizing) |

**Why structured filters first?**
- More precise and reliable than text search
- Faster query execution
- Better coverage (don't miss interventions that use different wording)
- Cleaner results

### Step 2: Add Query for Named Entities ONLY

**Use `query` ONLY for:**

✅ **Company names**: `'Tesla'`, `'Huawei'`, `'BYD'`, `'TSMC'`, `'Boeing'`
✅ **Program names**: `'Made in China 2025'`, `'Inflation Reduction Act'`, `'Chips Act'`
✅ **Technology/product names not in HS codes**: `'ChatGPT'`, `'artificial intelligence'`, `'5G'`, `'quantum computing'`, `'CRISPR'`
✅ **Specific named entities** that cannot be filtered otherwise

**Pattern:**
```python
# Structured filters define the scope
intervention_types=['State aid', 'Financial grant']
implementing_jurisdictions=['USA']
date_announced_gte='2023-01-01'

# Query adds the named entity
query='Tesla'
```

### Step 3: DO NOT Use Query For

❌ **Intervention types**: Use `intervention_types` or `mast_chapters` parameters
- Wrong: `query='subsidy | tariff | ban'`
- Right: `intervention_types=['State aid']` or `mast_chapters=['L']`

❌ **Generic policy terms**: Use structured filters
- Wrong: `query='trade barrier | import restriction'`
- Right: `mast_chapters=['E', 'F']`

❌ **Country names**: Use jurisdiction parameters
- Wrong: `query='China | United States'`
- Right: `implementing_jurisdictions=['CHN', 'USA']`

❌ **Concepts already covered by filters**
- Wrong: `query='renewable energy subsidy'`
- Right: `mast_chapters=['L']`, `affected_sectors=['Electricity generation']`

---

## Query Syntax Reference

### Single Word Searches

#### Exact Match
```python
query='WTO'
# Finds: interventions containing 'WTO'
```

#### Wildcard (#) for Spelling Variations
```python
query='utili#ation'
# Matches: 'utilization', 'utilisation'

query='subsidi#'
# Matches: 'subsidy', 'subsidies', 'subsidize', 'subsidise', 'subsidizing', 'subsidizing'

query='organi#ation'
# Matches: 'organization', 'organisation'
```

**Symbol Handling**: Symbols like `-`, `+`, `*` in words are automatically treated as wildcards
```python
query='non-tariff'
query='non+tariff'
query='non*tariff'
# All treated as: 'non#tariff' → matches 'non-tariff', 'nontariff', 'non tariff'
```

### Phrase Searches

#### Exact Phrase Match
```python
query='electronic commerce'
# Matches: the complete phrase "electronic commerce"
# Does NOT match: "electronic" in one place and "commerce" elsewhere
```

```python
query='Made in China 2025'
# Matches: the exact program name
```

### Boolean Logic

#### OR Logic (|) - Match Either Term

**Use for alternatives:**
```python
query='Tesla | BYD | Volkswagen'
# Finds interventions mentioning ANY of these companies

query='artificial intelligence | AI | machine learning'
# Covers different ways to reference AI

query='electric vehicle | EV | battery electric'
# Captures various EV terminologies
```

#### AND Logic (&) - Require Both Terms

**Use sparingly - typically for program names with multiple parts:**
```python
query='Made in China & 2025'
# Both terms required (useful for program name)

query='5G & Huawei'
# Interventions mentioning both 5G and Huawei
```

⚠️ **Warning**: Using & for policy concepts often reduces results unnecessarily. Use structured filters instead.

**Bad example:**
```python
query='semiconductor & tariff'  # ❌ DON'T
# Better:
intervention_types=['Import tariff']
affected_products=[854110, 854121, 854129]  # Semiconductor HS codes
```

#### Parentheses for Complex Logic

**For hierarchical logic:**
```python
query='(Tesla | SpaceX) & Musk'
# Finds: interventions mentioning (Tesla OR SpaceX) AND Musk

query='(5G | sixth generation) & (Huawei | ZTE)'
# Finds: (5G OR "sixth generation") AND (Huawei OR ZTE)

query='(artificial intelligence | AI | machine learning) & (export control | export ban)'
# Complex AI export control search
```

⚠️ **Caution**: The second part `(export control | export ban)` should usually be handled by `intervention_types` parameter instead.

---

## Search Scope

The query parameter searches across:

1. **Intervention Title** - Short policy name
2. **Intervention Description** - Detailed explanation of the measure
3. **Sources** - Official documents, news articles, announcements

**This means:**
- Entity names mentioned anywhere in these fields will be found
- Company names in source citations count
- Technology terms in descriptions are searchable

---

## Complete Examples: Structured Filters + Query

### Example 1: Tesla-Specific Subsidies ✅

```python
# Structured filters define scope
mast_chapters=['L']  # All subsidies
implementing_jurisdictions=['USA']
date_announced_gte='2020-01-01'

# Query adds entity
query='Tesla'
```

**What this finds**: US subsidy measures since 2020 that mention Tesla

**Why this works**: Structured filters narrow to subsidies, query finds the specific company

### Example 2: AI Export Controls ✅

```python
# Structured filters define scope
intervention_types=['Export ban', 'Export licensing requirement']
implementing_jurisdictions=['USA']
date_announced_gte='2023-01-01'

# Query adds technology terms
query='artificial intelligence | AI | machine learning'
```

**What this finds**: US export controls on AI technologies since 2023

**Why this works**: intervention_types captures the policy type precisely, query finds AI-related measures

### Example 3: Huawei Sanctions ✅

```python
# Structured filters define scope
intervention_types=['Import ban', 'Export ban', 'State enterprise restrictions']
affected_jurisdictions=['CHN']

# Query adds company
query='Huawei'
```

**What this finds**: Sanctions affecting China that specifically mention Huawei

**Why this works**: Combines policy types + country + company name

### Example 4: Electric Vehicle Subsidies ✅

```python
# Structured filters define scope
mast_chapters=['L']  # Subsidies
affected_products=[870310, 870320, 870380]  # EV HS codes
date_announced_gte='2022-01-01'

# Query adds EV terminology
query='electric | EV | battery electric'
```

**What this finds**: Subsidies for electric vehicles (by HS code) with EV terminology

**Why this works**: Product codes define exact goods, query ensures EV context

### Example 5: Semiconductor Export Controls to China ✅

```python
# Structured filters define scope
intervention_types=['Export ban', 'Export licensing requirement']
implementing_jurisdictions=['USA', 'NLD', 'JPN']  # Chip alliance
affected_jurisdictions=['CHN']
affected_products=[854110, 854121, 854129, 854140]  # Chip HS codes

# Query adds technology specifics
query='semiconductor | chip | ASML | lithography'
```

**What this finds**: Chip export controls from US/NLD/JPN to China

**Why this works**: Comprehensive structured filters + technology terms

---

## Common Mistakes and Corrections

### Mistake 1: Putting Policy Types in Query

❌ **WRONG:**
```python
query='import tariff on steel'
```

✅ **CORRECT:**
```python
intervention_types=['Import tariff']
affected_sectors=['Basic iron and steel']
# No query needed!
```

### Mistake 2: Putting Countries in Query

❌ **WRONG:**
```python
query='China & United States'
```

✅ **CORRECT:**
```python
implementing_jurisdictions=['CHN']
affected_jurisdictions=['USA']
# No query needed!
```

### Mistake 3: Over-Complex Query Expressions

❌ **WRONG:**
```python
query='(semiconductor | chip) & (tariff | import restriction | ban) & (China | Chinese)'
```

✅ **CORRECT:**
```python
intervention_types=['Import tariff', 'Import ban']  # Policy types as filters
implementing_jurisdictions=['USA', 'EU']  # Implementers as filter
affected_jurisdictions=['CHN']  # Affected country as filter
affected_products=[854110, 854121, 854129]  # Semiconductor HS codes
query='semiconductor | chip'  # ONLY the product terms
```

**Why the correction is better:**
- More reliable (doesn't miss interventions using different wording)
- Faster execution
- Cleaner results
- Captures ALL relevant measures, not just those using specific terms

### Mistake 4: Using Query Instead of Sectors

❌ **WRONG:**
```python
query='financial services | banking | insurance'
```

✅ **CORRECT:**
```python
affected_sectors=['Financial services', 'Insurance services']
# Or by ID:
affected_sectors=[711, 712, 713, 714, 715, 716, 717]
```

### Mistake 5: Generic Subsidy Search with Query

❌ **WRONG:**
```python
query='subsidy | state aid | grant | financial support'
```

✅ **CORRECT:**
```python
mast_chapters=['L']  # Covers ALL subsidy types comprehensively
# No query needed!
```

---

## Advanced Query Patterns

### Multi-Company Search

**Find interventions affecting multiple companies:**
```python
mast_chapters=['L']  # Subsidies
implementing_jurisdictions=['USA']
query='Tesla | Rivian | Lucid | Ford | GM'  # Any EV manufacturer
```

### Program Name with Variations

**Capture different ways to reference a program:**
```python
intervention_types=['State aid']
implementing_jurisdictions=['CHN']
query='Made in China 2025 | MiC2025 | MIC2025'
```

### Technology with Alternative Terms

**Cover different terminologies:**
```python
intervention_types=['Export ban', 'Export licensing requirement']
query='quantum computing | quantum information | quantum technology | qubits'
```

### Company and Product Combined

**Find company-specific product interventions:**
```python
mast_chapters=['L']
implementing_jurisdictions=['CHN']
query='CATL & battery'  # Chinese battery company support
```

---

## Query Performance Tips

### DO:
✅ Keep queries focused on named entities
✅ Use OR (|) to capture variations of the same concept
✅ Combine with precise structured filters
✅ Use wildcards (#) for spelling variations
✅ Search for specific, unique terms

### DON'T:
❌ Use query for things that have dedicated filter parameters
❌ Create overly complex boolean expressions
❌ Use generic terms that would match too broadly
❌ Rely solely on query without structured filters
❌ Use & (AND) unnecessarily - usually filters work better

---

## When in Doubt

**Ask yourself:**
1. "Can this be filtered with a structured parameter?" → Use the parameter
2. "Is this a named entity (company, program, specific technology)?" → Use query
3. "Would this query term appear in 100s of unrelated interventions?" → Don't use query

**Remember**: The query parameter is a **precision tool** for finding named entities, not a general search mechanism. Structured filters are the foundation of every good GTA search.

---

## Related Resources

- **Query Examples**: See `gta://guide/query-examples` for 35+ real-world query examples
- **Parameters Guide**: See `gta://guide/parameters` for complete parameter reference
- **MAST Chapters**: See `gta://reference/mast-chapters` for policy categorization
- **Search Best Practices**: See `gta://guide/searching` for overall search strategy

---

**Last Updated**: 2025-01-09
