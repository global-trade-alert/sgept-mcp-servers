# Common Mistakes When Using GTA Data

## DO:

- Use gta_evaluation [4] for "all harmful measures" (Red + Amber combined)
- Use gta_evaluation [1] for "certainly harmful" (Red only)
- Use date_announced_gte for "what's new" monitoring
- Use date_implemented_gte for "what's currently active"
- Note India = code 699 (not 356) when using raw UN codes
- Use impact chains endpoint for bilateral trade coverage analysis
- Check count_variable to know if you're counting interventions or state acts

## DON'T:

- Treat Amber as "neutral" — it means "likely harmful but uncertain"
- Expect evaluation=4 or evaluation=5 in individual intervention records
- Count by sector and report as "unique interventions" (overcounting risk)
- Assume recent data is complete (publication lag is normal)
- Look for bilateral treaty implementations (excluded from GTA)
- Look for data before November 2008 (database starts then)
- Use prior_level=0 at face value (likely artefact)
