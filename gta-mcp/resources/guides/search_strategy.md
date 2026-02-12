# Search Strategy Guide

## How Search Works (Automatic)

The GTA MCP server automatically manages response size and completeness. You do not need to set `detail_level` or `show_keys` — the server selects the right mode based on your query:

| Your query | Server auto-selects | What you get |
|------------|--------------------|--------------|
| Broad search (no `intervention_id`) | **Overview mode**, limit=500 | Compact table: ID, title, type, evaluation, date, implementer |
| Specific IDs (`intervention_id: [...]`) | **Standard mode** | Analysis-ready: adds sectors, affected countries, all dates, MAST chapter |

This enables a natural two-step workflow:

1. **Search broadly** → see up to 500 interventions as a compact triage list
2. **Pick the relevant IDs** → call again with `intervention_id: [selected IDs]` for full analysis data

## Example Workflow

### Step 1: Broad search (automatic overview)

```
gta_search_interventions(
    implementing_jurisdictions: ["USA"],
    date_announced_gte: "2024-01-01"
)
```

Returns a compact table of up to 500 interventions. Scan titles, types, and evaluations to identify what's relevant.

### Step 2: Get details for relevant IDs

```
gta_search_interventions(
    intervention_id: [138295, 138296, 138301, ...]
)
```

Returns analysis-ready data (sectors, affected countries, all dates, MAST chapter) for exactly the interventions you selected. No limit concerns because you're fetching specific IDs.

### Step 3 (optional): Full detail for a single intervention

```
gta_get_intervention(intervention_id: 138295)
```

Returns everything: descriptions, sources, product-level detail, tariff rates.

## When to Override the Default

You rarely need to set `detail_level` explicitly. Use it only when:

**`detail_level: "standard"`** — Force standard detail on a broad search (when you're confident the query returns < 50 results and you want sectors/affected countries immediately).

**`detail_level: "full"`** — Force full detail including descriptions, sources, and product arrays. Best for small result sets (< 10 interventions). Warning: large responses may be truncated.

**`detail_level: "overview"`** — Explicitly request overview mode (rarely needed since it's the automatic default for broad searches).

## Monitoring with update_period

To track what changed recently in GTA:

```
gta_search_interventions(
    date_modified_gte: "2026-02-01",
    sorting: "-last_updated"
)
```

This shows interventions added or significantly modified since the specified date, ordered by most recent changes first. Useful for weekly monitoring.

## Custom Key Selection

For advanced use, the `show_keys` parameter lets you specify exactly which fields to return:

```
gta_search_interventions(
    implementing_jurisdictions: ["CHN"],
    mast_chapters: ["P"],
    show_keys: ["intervention_id", "state_act_title", "affected_products", "date_announced"]
)
```

This overrides the automatic mode and is useful when you need a specific field combination.
