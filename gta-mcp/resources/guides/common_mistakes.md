# Common Mistakes When Using GTA Data

## DO:

**Use gta_evaluation [4] for "all harmful measures" (Red + Amber combined)**
- Example: "Count all trade restrictions imposed by the US in 2024" → use `gta_evaluation: [4]` to capture both certainly harmful and likely harmful measures.

**Use gta_evaluation [1] for "certainly harmful" (Red only)**
- Example: "Count only measures that GTA has definitively classified as protectionist" → use `gta_evaluation: [1]` to exclude uncertain cases.

**Use date_announced_gte for "what's new" monitoring**
- Example: "What trade policy changes has China announced since January 2025?" → use `date_announced_gte: "2025-01-01"` to capture recent announcements regardless of implementation status.

**Use date_implemented_gte for "what's currently active"**
- Example: "What new measures came into force this quarter?" → use `date_implemented_gte: "2025-01-01"` to see measures that became legally binding.

**Use is_in_force: true to filter for currently active measures only**
- Example: "Which Chinese subsidies are still active today?" → combine `is_in_force: true` with `implementing_jurisdictions` to exclude removed/expired measures.

**Note India = code 699 (not 356) when using raw UN codes**
- Example: If constructing manual jurisdiction queries, use 699 for India. The GTA system uses this historical UN code for consistency.

**Use impact chains endpoint for bilateral trade coverage analysis**
- Example: "How much US-China trade is covered by tariffs?" → use the impact chains tool to calculate trade-weighted coverage ratios.

**Check count_variable to know if you're counting interventions or state acts**
- Example: When reporting statistics, specify "1,247 interventions" vs "894 state acts" to avoid ambiguity about what's being counted.

**Use gta://reference/glossary to understand unfamiliar GTA terminology**
- Example: If you encounter terms like "contingent trade-protective measure" or "behind-the-border instrument," check the glossary for GTA's specific definitions.

**Specify limit parameter to control response size (default is 50)**
- Example: For exploratory queries, use `limit: 10` to get quick results. For comprehensive analysis, use `limit: 1000` or higher.

## DON'T:

**Treat Amber as "neutral" — it means "likely harmful but uncertain"**
- Wrong: "Amber measures are neither good nor bad." Correct: "Amber measures are probably protectionist but lack sufficient evidence for Red classification."

**Expect evaluation=4 or evaluation=5 in individual intervention records**
- Wrong: Filtering for `gta_evaluation: 4` in intervention details. Correct: The values 4 and 5 are aggregation codes used in counting queries, not stored in individual records.

**Count by sector and report as "unique interventions" (overcounting risk)**
- Wrong: "China implemented 847 interventions in the steel sector." Correct: "China implemented interventions affecting 847 intervention-sector combinations in steel." The same intervention appears multiple times.

**Assume recent data is complete (publication lag is normal)**
- Wrong: "No new measures were announced in the last two weeks." Correct: "No new measures are recorded in GTA yet; there may be a publication lag of 2-4 weeks."

**Look for bilateral treaty implementations (excluded from GTA)**
- Wrong: "Find the implementation of the UK-Australia Free Trade Agreement." Correct: GTA excludes reciprocal trade liberalisation treaties and focuses on discriminatory unilateral measures.

**Look for data before November 2008 (database starts then)**
- Wrong: Querying for measures from 2007. Correct: GTA coverage begins in November 2008 following the global financial crisis.

**Use prior_level=0 at face value (likely artefact)**
- Wrong: "The prior tariff level was 0%." Correct: Zero values in prior_level often indicate missing data rather than genuinely zero tariffs. Verify from official sources.

**Search for "trade war" in the query field (use structured filters instead)**
- Wrong: Setting `query: "trade war"` expecting relevant results. Correct: Use structured filters for countries (`implementing_jurisdictions`, `affected_jurisdictions`) and date ranges to analyse trade conflicts.

**Assume date_implemented is always set**
- Wrong: Filtering by `date_implemented` and expecting complete results. Correct: Many interventions only have `date_announced`. Use `date_announced` for comprehensive monitoring.

**Confuse implementing_jurisdictions with affected_jurisdictions**
- Wrong: "Find measures that harm the US" → using `implementing_jurisdictions: ["United States"]`. Correct: Use `affected_jurisdictions: ["United States"]` for measures targeting US exports/firms.

**Assume count results by date_implemented capture all measures**
- Wrong: "Only 3,903 harmful measures were implemented in 2025." Correct: "At least 3,903 harmful measures have known implementation dates in 2025. Additionally, many announced measures lack implementation dates and are excluded from this count." Use `date_announced` for more complete counts.

**Trust anomalous date groups in count results at face value**
- Wrong: "6 export restrictions were announced in 1970." Correct: Pre-2008 dates in GTA count results are likely data quality artefacts. GTA monitoring begins November 2008. Filter or exclude pre-2008 groups from trend analysis.

**Set detail_level manually (the server handles this automatically)**
- Wrong: Always setting `detail_level: "overview"` or `detail_level: "standard"` on every query. Correct: The server auto-selects overview mode (compact, limit=1000) for broad searches and standard mode for specific intervention_id lookups. You rarely need to set `detail_level` explicitly.

**Expect full intervention details on a broad search (the default is compact overview)**
- Wrong: Expecting descriptions, product arrays, and sources from a broad search. Correct: Broad searches return a compact overview table (ID, title, type, evaluation, date, implementer). To get full details, pick the relevant intervention IDs and call again with `intervention_id: [selected IDs]`.

**Use date_modified_gte with -last_updated sorting for monitoring**
- Example: "What GTA entries were updated this week?" → use `date_modified_gte: "2026-02-05"` with `sorting: "-last_updated"` to see recently modified interventions first.

## Interpretation Guidance

**When you see gaps in recent data:**
- Normal publication lag is 2-4 weeks
- Complex measures take longer to verify and classify
- Don't interpret absence as evidence that nothing happened

**When dates conflict:**
- Announcement date is always most reliable (publicly observable)
- Implementation date may be estimated or incomplete
- Year-only dates are conservative estimates (default to end of year)

**When evaluations seem surprising:**
- Read the description field for GTA's reasoning
- Check sources for official documentation
- Remember that GTA evaluates measures against WTO principles, not political motives
