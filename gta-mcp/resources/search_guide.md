# Searching the GTA Database: Best Practices

This guide helps you search the Global Trade Alert database effectively and avoid common pitfalls.

## Understanding Default Behavior

**IMPORTANT:** The GTA API returns oldest interventions first by default (sorted by intervention ID ascending). This means:

❌ Searching without date filters or sorting will return data from 2009-2015
❌ You won't see recent interventions unless you explicitly request them
✅ **Always use date filters or sorting to find recent data**

## Finding Recent Interventions

### Method 1: Use Date Filters (Recommended)

The most reliable way to find recent interventions is to specify date ranges:

```
date_announced_gte: "2025-01-01"  # Interventions announced from 2025 onwards
date_announced_lte: "2025-12-31"  # Interventions announced up to end of 2025
```

**Examples:**
- Find interventions from the last month: `date_announced_gte: "2025-09-23"`
- Find interventions from 2024: `date_announced_gte: "2024-01-01", date_announced_lte: "2024-12-31"`
- Find interventions from the last year: `date_announced_gte: "2024-10-23"`

### Method 2: Use Sorting

The `sorting` parameter controls the order of results:

```
sorting: "-date_announced"  # Newest announcements first (RECOMMENDED)
sorting: "date_announced"   # Oldest announcements first
sorting: "-intervention_id" # Highest ID first (usually newest)
```

**Default behavior:** If you don't specify sorting, the MCP now defaults to `"-date_announced"` (newest first).

### Method 3: Combine Both

For best results, combine date filters with sorting:

```
date_announced_gte: "2025-01-01"
sorting: "-date_announced"
```

## Common Search Patterns

### Pattern 1: "What are the most recent trade interventions?"

**Use:**
```
sorting: "-date_announced"
limit: 20
```

This returns the 20 most recently announced interventions across all countries and types.

### Pattern 2: "What has [country] done recently?"

**Use:**
```
implementing_jurisdictions: ["USA"]
date_announced_gte: "2025-01-01"
sorting: "-date_announced"
```

This finds all interventions implemented by the USA announced in 2025, newest first.

### Pattern 3: "Find recent [intervention type] measures"

**Use:**
```
intervention_types: ["Export ban"]
date_announced_gte: "2024-01-01"
sorting: "-date_announced"
```

This finds recent export bans, newest first.

### Pattern 4: "What interventions are currently in force?"

**Use:**
```
is_in_force: true
sorting: "-date_announced"
```

This finds all currently active interventions, showing most recently announced first.

### Pattern 5: "What happened in [specific time period]?"

**Use:**
```
date_announced_gte: "2024-10-01"
date_announced_lte: "2024-10-31"
sorting: "-date_announced"
```

This finds all interventions announced in October 2024, newest to oldest.

## Troubleshooting: "No Recent Data Found"

If you're getting old results (2009-2015) when you expect recent data:

1. **Check your date filters:** Make sure you're using `date_announced_gte` with a recent date
2. **Check your sorting:** Verify `sorting: "-date_announced"` is set (it's now the default)
3. **Check the date range:** Don't use future dates or overly restrictive ranges
4. **Try without filters first:** Test with just `sorting: "-date_announced"` to verify data exists

## Understanding Date Fields

The GTA tracks several different dates for each intervention:

- **date_announced**: When the policy was publicly announced (USE THIS for recent searches)
- **date_implemented**: When the policy actually took effect (may be weeks/months after announcement)
- **date_published**: When official documentation was published
- **date_removed**: When the policy was terminated or expired

**For finding recent interventions, always use `date_announced`** as this captures the policy's initial disclosure.

## Sorting Options Reference

Valid fields for sorting:
- `date_announced` - Announcement date (recommended for recent data)
- `date_published` - Publication date of official documentation
- `date_implemented` - Implementation/inception date
- `date_removed` - Removal/expiration date
- `intervention_id` - Internal GTA identifier

**Sorting syntax:**
- Prefix with `-` for descending (newest/highest first): `-date_announced`
- No prefix for ascending (oldest/lowest first): `date_announced`
- Combine multiple fields with commas: `date_announced,intervention_id`

## Using Evaluation Filters

The `gta_evaluation` parameter filters interventions by their trade impact assessment:

**Individual values (appear in actual records):**
- `"Red"` — Certainly harmful, discriminatory measures
- `"Amber"` — Likely harmful but uncertain outcome (includes all trade defence investigations)
- `"Green"` — Liberalizing measures

**Filter-only convenience values (for searching):**
- `"Harmful"` — Shorthand for Red + Amber combined (most common analytical definition)
- `"Liberalizing"` — Same as Green

⚠️ Note: Individual intervention records always contain "Red", "Amber", or "Green". You will never
see "Harmful" or "Liberalizing" in actual records — these are filter shortcuts only.

**Recommendation:** Use `gta_evaluation: ["Red", "Amber"]` instead of relying on the convenience
value to make your intent explicit.

## Best Practices Summary

✅ **DO:**
- Use `sorting: "-date_announced"` (now the default) for recent data
- Specify date ranges with `date_announced_gte/lte` when searching specific time periods
- Start broad and add filters incrementally
- Check the most recent data first to understand what's available
- Use `gta_evaluation: ["Red", "Amber"]` to filter for harmful measures

❌ **DON'T:**
- Search without date filters or sorting if you want recent data
- Use future dates in your filters
- Expect to see "Harmful" or "Liberalizing" in intervention records (filter-only values)
- Assume the first results are the most recent (without sorting)
- Use only `date_implemented` for recent searches (many measures have no implementation date yet)

## Data Availability

The GTA database is updated regularly with new interventions. As of October 2025, the database contains interventions announced as recently as today. The database has comprehensive coverage from November 2008 onwards.
