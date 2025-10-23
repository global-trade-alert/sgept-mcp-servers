# Understanding GTA Date Fields

The Global Trade Alert database tracks multiple dates for each intervention to capture the full lifecycle of trade policy measures. Understanding these different date fields is crucial for effective searching and analysis.

## Overview of Date Fields

The GTA tracks four primary date dimensions:

1. **Announcement Date** (date_announced) - When the policy was publicly announced
2. **Inception Date** (date_implemented) - When the policy took effect
3. **Removal Date** (date_removed) - When the policy was withdrawn
4. **Last Update Date** (date_modified) - When the database entry was modified

## 1. Announcement Date (date_announced)

**Definition:** The date when the policy decision was publicly announced by the implementing authority.

**This is the most important date for searching recent interventions.**

### Why Announcement Date Matters

The announcement date represents the first official disclosure of a trade policy measure. This is when:
- Governments publicly communicate their policy decisions
- Markets and trading partners become aware of upcoming changes
- Policy uncertainty begins to affect commercial decisions

### When to Use Announcement Date

✅ **USE announcement date when you want to:**
- Find the most recent policy developments
- Track when policies were first disclosed
- Monitor government policy activity over time
- Search for interventions in a specific time period

### Example Queries

- "What trade measures were announced in October 2025?"
  - Use: `date_announced_gte: "2025-10-01"`, `date_announced_lte: "2025-10-31"`

- "What has been announced in the last 30 days?"
  - Use: `date_announced_gte: "2025-09-23"`

- "What did the US announce in 2024?"
  - Use: `implementing_jurisdictions: ["USA"]`, `date_announced_gte: "2024-01-01"`, `date_announced_lte: "2024-12-31"`

## 2. Inception Date (date_implemented)

**Definition:** The date when the policy change was actually enforced or implemented - when it began affecting markets.

**Source (from GTA Handbook):**
> "The inception date designates when the documented policy change was enforced or implemented. This dimension is essential for identifying the scope at which trade policies take effect in markets. It distinguishes between when a policy was merely announced and when it actually began impacting commercial interests."

### Understanding the Announcement-Implementation Gap

There is often a delay between announcement and implementation:
- **Immediate implementation:** Some measures take effect on the announcement date
- **Future implementation:** Many measures are announced weeks or months before taking effect
- **Missing implementation date:** Some announced measures never implemented or pending

### When to Use Inception Date

✅ **USE inception date when you want to:**
- Identify which policies are currently affecting markets
- Determine when trade flows were actually disrupted
- Analyze the timing of policy impact
- Find policies that took effect in a specific period

❌ **DON'T USE inception date for:**
- Finding the most recent announcements (use announcement date instead)
- Tracking new policy developments (many announced policies don't have implementation dates yet)

### Important Notes

⚠️ **Many interventions have no inception date yet** - they have been announced but:
- Are pending legislative approval
- Have future implementation dates
- Are under investigation or review
- Were announced but not yet enforced

This means searching by `date_implemented` will **miss many recent announcements**.

## 3. Removal Date (date_removed)

**Definition:** The date when the policy action was withdrawn, expired, or replaced.

**Source (from GTA Handbook):**
> "The removal date field identifies when the reported policy action was withdrawn or replaced. When selected, it delimits the effects of the policy action on market access."

### When to Use Removal Date

✅ **USE removal date when you want to:**
- Find policies that ended in a specific period
- Track how long policies remained in force
- Identify which measures have been withdrawn
- Analyze policy reversals

### Important Notes

⚠️ **Most active policies have no removal date** - they are still in force

## 4. Last Update Date (date_modified)

**Definition:** The date when the database entry was last modified with content-related changes.

**Source (from GTA Handbook):**
> "The last update date field identifies when content-related modifications were applied to an existing intervention entry. The last update date helps track non-meaningful changes affecting policies over time and determines when such additional information was included in the database."

### What Triggers an Update

Database updates occur when:
- Additional information becomes available about an existing measure
- Policies are extended or modified (without creating a new intervention)
- Sources are added or corrected
- Implementation details are clarified

### When to Use Last Update Date

✅ **USE last update date when you want to:**
- Track which interventions were recently updated
- Monitor evolving information about policies
- Identify interventions with new details

### Example from Handbook

"An example of such a content-related update is a government announcement extending the duration of a temporary export quota. This scenario would trigger an update to the removal date field, as this change provides relevant information about policy evolution while failing to meet the threshold for creating a new intervention entry."

## Choosing the Right Date Field

### For Finding Recent Trade Policy Developments

**PRIMARY:** Use `date_announced` with sorting
```
date_announced_gte: "2025-01-01"
sorting: "-date_announced"
```

**WHY:** Announcement date captures when policies first become public, giving you the earliest possible awareness of trade measures.

### For Finding Currently Active Policies

**COMBINE:** Use `is_in_force` flag with announcement date
```
is_in_force: true
sorting: "-date_announced"
```

**WHY:** The `is_in_force` flag identifies currently active policies regardless of when they were announced or implemented.

### For Understanding Policy Timeline

**USE ALL DATES:** Query with minimal filters and examine full date range
```
intervention_id: [specific ID]
```

**EXAMINE:** announcement_date, date_implemented, date_removed to understand full policy lifecycle

## Common Mistakes to Avoid

❌ **MISTAKE 1:** Using only `date_implemented` to find recent policies
- **PROBLEM:** Many recent announcements don't have implementation dates yet
- **SOLUTION:** Use `date_announced` instead

❌ **MISTAKE 2:** Not using sorting with date searches
- **PROBLEM:** Results come back in random (oldest-first) order
- **SOLUTION:** Always add `sorting: "-date_announced"`

❌ **MISTAKE 3:** Assuming all interventions have all dates
- **PROBLEM:** Not all fields are populated for all interventions
- **SOLUTION:** Design queries that work with missing data (use announcement date as baseline)

## Date Field Reference Table

| Field | Population Rate | Best Use Case | Search Priority |
|-------|----------------|---------------|-----------------|
| **date_announced** | ~100% | Finding recent policies | **PRIMARY** |
| **date_implemented** | ~60-70% | Finding active policies | Secondary |
| **date_removed** | ~10-20% | Finding expired policies | Specialized |
| **date_modified** | Variable | Tracking updates | Specialized |

## Real-World Examples

### Example 1: Recent Export Restrictions

**Question:** "What export restrictions have been announced in 2025?"

**Query:**
```
intervention_types: ["Export ban", "Export licensing requirement", "Export quota"]
date_announced_gte: "2025-01-01"
sorting: "-date_announced"
```

**Why this works:** Uses announcement date to capture all recent restrictions, regardless of implementation status.

### Example 2: Active Import Tariffs

**Question:** "What import tariffs are currently in force?"

**Query:**
```
intervention_types: ["Import tariff"]
is_in_force: true
sorting: "-date_announced"
```

**Why this works:** The `is_in_force` flag handles both announced and implemented policies that are currently active.

### Example 3: Policy Changes in October

**Question:** "What changed in October 2025?"

**Query:**
```
date_announced_gte: "2025-10-01"
date_announced_lte: "2025-10-31"
sorting: "-date_announced"
```

**Why this works:** Date range on announcement captures all policy developments in that month.

## Summary: Best Practices

✅ **For recent data:** Always use `date_announced` (not `date_implemented`)
✅ **For sorting:** Always use `sorting: "-date_announced"` to get newest first
✅ **For active policies:** Use `is_in_force: true` instead of date filters
✅ **For specific periods:** Use date ranges with `date_announced_gte/lte`
✅ **For policy lifecycle:** Examine all date fields together to understand full timeline

The announcement date is your primary tool for finding recent interventions and tracking policy developments in real-time.
