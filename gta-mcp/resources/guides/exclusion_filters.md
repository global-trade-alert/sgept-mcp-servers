# GTA Exclusion Filters Guide

## Overview

Most GTA search filters use **inclusion logic** by default - when you specify values, you get ONLY interventions matching those values.

The `keep_*` parameters **invert this logic**, enabling **exclusion-based filtering** to find "everything EXCEPT" the specified values.

---

## How Keep Parameters Work

### The Pattern

Every filterable field has a corresponding `keep_*` parameter that controls inclusion/exclusion:

| Filter Parameter | Keep Parameter | Purpose |
|-----------------|----------------|---------|
| `implementing_jurisdictions` | `keep_implementer` | Include/exclude implementing countries |
| `affected_jurisdictions` | `keep_affected` | Include/exclude affected countries |
| `intervention_types` | `keep_intervention_types` | Include/exclude policy types |
| `mast_chapters` | `keep_mast_chapters` | Include/exclude MAST chapters |
| `affected_sectors` | `keep_affected_sectors` | Include/exclude CPC sectors |
| `affected_products` | `keep_affected_products` | Include/exclude HS product codes |
| `implementation_levels` | `keep_implementation_level` | Include/exclude government levels |
| `eligible_firms` | `keep_eligible_firms` | Include/exclude firm types |
| `intervention_id` | `keep_intervention_id` | Include/exclude specific interventions |

### The Logic

**`keep_*=True` (DEFAULT)**:
- **Include ONLY** specified values
- This is normal filter behavior
- "Show me interventions matching these values"

**`keep_*=False`**:
- **Exclude** specified values, show everything else
- This enables "everything EXCEPT" queries
- "Show me all interventions EXCEPT those matching these values"

### Important Notes

- `keep_*=True` is the **default behavior** - you don't need to specify it
- Only specify `keep_*=False` when you want exclusion logic
- You can mix inclusion and exclusion logic across different parameters

---

## Complete Keep Parameter Reference

### 1. `keep_affected` - Affected Jurisdictions

**Controls**: Which countries are affected by the measure

**Usage**:
```python
# INCLUSION (default): Only measures affecting China
affected_jurisdictions=['CHN']
# keep_affected=True is implicit

# EXCLUSION: All measures EXCEPT those affecting China
affected_jurisdictions=['CHN']
keep_affected=False
```

**Common Use Cases**:
- Exclude specific markets from analysis
- Find interventions NOT targeting major economies
- Analyze measures affecting "rest of world"

**Example**:
```python
# Everything EXCEPT measures affecting US and EU
affected_jurisdictions=['USA', 'EU']
keep_affected=False
```

---

### 2. `keep_implementer` - Implementing Jurisdictions

**Controls**: Which countries implemented the measure

**Usage**:
```python
# INCLUSION (default): Only US measures
implementing_jurisdictions=['USA']

# EXCLUSION: All measures EXCEPT from G7 countries
implementing_jurisdictions=['USA', 'CAN', 'GBR', 'FRA', 'DEU', 'ITA', 'JPN']
keep_implementer=False
```

**Common Use Cases**:
- Exclude major economies to focus on emerging markets
- Find measures NOT from specific countries
- Analyze "rest of world" policy trends

**Example**:
```python
# All subsidy measures EXCEPT from China and US
mast_chapters=['L']
implementing_jurisdictions=['CHN', 'USA']
keep_implementer=False
```

---

### 3. `keep_intervention_types` - Intervention Types

**Controls**: Which policy types are included

**Usage**:
```python
# INCLUSION (default): Only tariffs
intervention_types=['Import tariff']

# EXCLUSION: All non-tariff measures
intervention_types=['Import tariff', 'Export tariff']
keep_intervention_types=False
```

**Common Use Cases**:
- Find non-tariff barriers (exclude tariffs)
- Analyze non-subsidy measures (exclude subsidies)
- Focus on "other" policy types

**Example**:
```python
# All trade measures EXCEPT tariffs
intervention_types=['Import tariff', 'Export tariff', 'Tariff-rate quota']
keep_intervention_types=False
```

---

### 4. `keep_mast_chapters` - MAST Chapters

**Controls**: Which MAST chapter categories are included

**Usage**:
```python
# INCLUSION (default): Only subsidies
mast_chapters=['L']

# EXCLUSION: All non-subsidy measures
mast_chapters=['L']
keep_mast_chapters=False
```

**Common Use Cases**:
- Analyze non-subsidy interventions
- Exclude specific policy categories
- Focus on subset of non-tariff measures

**Example**:
```python
# All measures EXCEPT subsidies and procurement restrictions
mast_chapters=['L', 'M']  # Subsidies + Government procurement
keep_mast_chapters=False
```

---

### 5. `keep_implementation_level` - Government Levels

**Controls**: Which government levels are included

**Usage**:
```python
# INCLUSION (default): Only national policies
implementation_levels=['National']

# EXCLUSION: Only subnational (exclude national/supranational)
implementation_levels=['National', 'Supranational']
keep_implementation_level=False
```

**Common Use Cases**:
- Focus on regional/local policies (exclude national)
- Exclude supranational measures
- Analyze non-central government policies

**Example**:
```python
# Regional development measures (subnational only)
implementation_levels=['National', 'Supranational', 'IFI', 'NFI']
keep_implementation_level=False
# This leaves only: Subnational and SEZ
```

---

### 6. `keep_eligible_firms` - Firm Types

**Controls**: Which firm types are eligible

**Usage**:
```python
# INCLUSION (default): Only SME-targeted measures
eligible_firms=['SMEs']

# EXCLUSION: Universal policies only (exclude targeted programs)
eligible_firms=['firm-specific', 'SMEs', 'state-controlled', 'sector-specific', 'location-specific']
keep_eligible_firms=False
# This leaves only: 'all' (universal policies)
```

**Common Use Cases**:
- Find universal vs targeted policies
- Exclude firm-specific interventions
- Analyze broad-based support measures

**Example**:
```python
# General policies affecting all companies (not targeted)
eligible_firms=['firm-specific', 'SMEs', 'location-specific']
keep_eligible_firms=False
```

---

### 7. `keep_affected_sectors` - CPC Sectors

**Controls**: Which CPC sectors are included

**Usage**:
```python
# INCLUSION (default): Only financial services
affected_sectors=[711, 712, 713, 714, 715, 716, 717]

# EXCLUSION: All sectors EXCEPT agriculture
affected_sectors=[11, 12, 13, 21, 22]  # Agricultural CPC codes
keep_affected_sectors=False
```

**Common Use Cases**:
- Exclude agricultural sectors
- Focus on non-service interventions
- Analyze specific sector subsets

**Example**:
```python
# All interventions EXCEPT those affecting agriculture and food
affected_sectors=[11, 12, 13, 21, 22, 211, 212, 213, 214, 215]
keep_affected_sectors=False
```

---

### 8. `keep_affected_products` - HS Product Codes

**Controls**: Which HS product codes are included

**Usage**:
```python
# INCLUSION (default): Only semiconductors
affected_products=[854110, 854121, 854129, 854140]

# EXCLUSION: All products EXCEPT semiconductors
affected_products=[854110, 854121, 854129, 854140]
keep_affected_products=False
```

**Common Use Cases**:
- Exclude specific HS code categories
- Find measures affecting "other products"
- Narrow by exclusion

**Example**:
```python
# US tariffs on ALL products except steel
implementing_jurisdictions=['USA']
intervention_types=['Import tariff']
affected_products=[720110, 720120, 720130, ...]  # Steel HS codes
keep_affected_products=False
```

---

### 9. `keep_implementation_period_na` - Implementation Date Handling

**Controls**: Whether interventions with NO implementation date are included

**Special Case**: This controls NULL/NA values, not specific dates

**Usage**:
```python
# INCLUSION (default): Include measures with AND without implementation dates
# keep_implementation_period_na=True is implicit

# EXCLUSION: Only measures with KNOWN implementation dates
keep_implementation_period_na=False
```

**Common Use Cases**:
- Filter out announced-but-not-yet-implemented measures
- Focus on measures with clear implementation dates
- Data quality filtering

**Example**:
```python
# Only subsidies that have been actually implemented (not just announced)
mast_chapters=['L']
keep_implementation_period_na=False
date_implemented_gte='2020-01-01'
```

**Important**: This works **independently** of `date_implemented_gte/lte` filters:
- `date_implemented_gte` filters dates when present
- `keep_implementation_period_na=False` excludes NULL dates entirely

---

### 10. `keep_revocation_na` - Revocation Date Handling

**Controls**: Whether interventions with NO revocation date are included

**Special Case**: This controls NULL/NA values for revoked measures

**Usage**:
```python
# INCLUSION (default): Include measures with AND without revocation dates
# keep_revocation_na=True is implicit

# EXCLUSION: Only measures that HAVE BEEN revoked (with known dates)
keep_revocation_na=False
```

**Common Use Cases**:
- Find only revoked/expired measures
- Analyze policy reversals with known dates
- Track measure lifecycle

**Example**:
```python
# Only measures that were revoked in 2024
keep_revocation_na=False
date_removed_gte='2024-01-01'
date_removed_lte='2024-12-31'
```

---

### 11. `keep_intervention_id` - Specific Interventions

**Controls**: Which specific intervention IDs are included

**Usage**:
```python
# INCLUSION (default): Only these specific interventions
intervention_id=[138295, 137842]

# EXCLUSION: All interventions EXCEPT these specific ones
intervention_id=[138295, 137842, 139103]
keep_intervention_id=False
```

**Common Use Cases**:
- Exclude known interventions from search
- Remove duplicates or outliers
- Refine search results by removing specific cases

**Example**:
```python
# US subsidies excluding three specific measures already analyzed
mast_chapters=['L']
implementing_jurisdictions=['USA']
intervention_id=[138295, 137842, 139103]
keep_intervention_id=False
```

---

## Advanced Patterns

### Pattern 1: Bilateral Analysis with Exclusions

**Use Case**: US measures affecting all countries EXCEPT allies

```python
implementing_jurisdictions=['USA']
affected_jurisdictions=['CAN', 'MEX', 'GBR', 'EU', 'AUS', 'JPN', 'KOR']
keep_affected=False
intervention_types=['Import tariff', 'Import ban']
```

### Pattern 2: Non-Tariff Barrier Analysis

**Use Case**: All trade restrictions EXCEPT tariffs

```python
implementing_jurisdictions=['CHN']
intervention_types=['Import tariff', 'Export tariff', 'Tariff-rate quota']
keep_intervention_types=False
date_announced_gte='2020-01-01'
```

### Pattern 3: Emerging Market Policies

**Use Case**: All measures EXCEPT from major economies

```python
implementing_jurisdictions=['USA', 'EU', 'CHN', 'JPN', 'GBR', 'DEU', 'FRA', 'ITA', 'CAN']
keep_implementer=False
mast_chapters=['L']  # Subsidies
```

### Pattern 4: Targeted vs Universal Policies

**Use Case**: General policies affecting all companies (not targeted)

```python
mast_chapters=['L']
eligible_firms=['firm-specific', 'SMEs', 'state-controlled', 'sector-specific', 'location-specific']
keep_eligible_firms=False
# This leaves only: 'all' (universal policies)
```

### Pattern 5: Clean Data Analysis

**Use Case**: Only measures with complete date information

```python
keep_implementation_period_na=False  # Must have implementation date
keep_revocation_na=True  # Allow both active and revoked
date_implemented_gte='2018-01-01'
```

---

## Mixing Inclusion and Exclusion Logic

You can combine inclusion and exclusion across different parameters:

**Example**: US subsidies affecting China, excluding firm-specific programs

```python
implementing_jurisdictions=['USA']  # Include only US
affected_jurisdictions=['CHN']  # Include only measures affecting China
mast_chapters=['L']  # Include only subsidies
eligible_firms=['firm-specific']  # Specify firm-specific
keep_eligible_firms=False  # But EXCLUDE them (so universal programs only)
```

**Result**: Universal US subsidy programs affecting China (not company-specific)

---

## Common Mistakes

### Mistake 1: Forgetting to Set keep_*=False

❌ **WRONG** (will return ONLY tariffs, not non-tariff measures):
```python
intervention_types=['Import tariff', 'Export tariff']
# Missing: keep_intervention_types=False
```

✅ **CORRECT**:
```python
intervention_types=['Import tariff', 'Export tariff']
keep_intervention_types=False  # Exclude tariffs
```

### Mistake 2: Using Empty Lists

❌ **WRONG** (empty list with keep_*=False does nothing):
```python
intervention_types=[]
keep_intervention_types=False
```

✅ **CORRECT** (specify what to exclude):
```python
intervention_types=['Import tariff', 'Export tariff']
keep_intervention_types=False
```

### Mistake 3: Double Negation Confusion

❌ **CONFUSING** (what does this mean?):
```python
keep_implementer=False
keep_intervention_types=False
# Are we including or excluding?
```

✅ **CLEARER** (be explicit in variable names or comments):
```python
# Exclude G7 countries, exclude tariffs
implementing_jurisdictions=['USA', 'CAN', 'GBR', 'FRA', 'DEU', 'ITA', 'JPN']
keep_implementer=False

intervention_types=['Import tariff', 'Export tariff']
keep_intervention_types=False
```

---

## Troubleshooting

### "I'm getting too many results"
- Check if you meant to exclude something but forgot `keep_*=False`
- Verify you're specifying the right values to exclude

### "I'm getting no results"
- If using `keep_*=False`, make sure you're not excluding everything
- Check that your exclusion list is correct
- Try removing exclusions one at a time to find the issue

### "Results don't make sense"
- Verify you understand inclusion vs exclusion for each parameter
- Check if mixing inclusion and exclusion is creating unintended filters
- Test with simpler queries first, then add exclusions

---

## Related Resources

- **Parameters Guide**: See `gta://guide/parameters` for complete parameter reference
- **Query Examples**: See `gta://guide/query-examples` for more filtering examples
- **Search Guide**: See `gta://guide/searching` for overall search strategy

---

**Last Updated**: 2025-01-09
