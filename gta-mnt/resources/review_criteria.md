# Sancho Claudino — Review Criteria

A Step-1 review of a GTA entry is an independent check of the database content against the cited official source. The reviewer is not the author: the reviewer asks *does what the entry says match what the source says?* — not *did the author make the best possible choices?*.

## Fields to check (minimum set)

This is the minimum surface. A review that covers fewer fields is incomplete. A review that covers more is fine — the point is that *none* of these may be skipped.

| Field | What to check | Where it lives |
|---|---|---|
| `title` | Matches the measure name in the source | State act |
| `description` | Summarises (not copies) what the source announces | State act |
| `date_announced` | Matches the announcement date on the source | State act |
| `is_source_official` | Source is the implementing government / IO (1) or a news report (0) | State act |
| `intervention_type` | Measure class (tariff, subsidy, export quota, …) matches the source's own language | Intervention |
| `gta_evaluation_id` | Red (harmful) / Amber / Green assignment matches GTA handbook rules | Intervention |
| `affected_flow_id` | Inward / Outward / Outward-subsidy matches the measure's direction | Intervention |
| `implementing_jurisdictions` | Country / region imposing the measure | Intervention (via `add_ij`) |
| `affected_products` (HS) | HS codes covered actually line up with the source's product description | Intervention (via `add_product`) |
| `affected_sectors` (CPC) | Sectors line up with the source description | Intervention (via `add_sector`) |
| `date_implemented` | Effective date — often different from `date_announced` | Intervention |
| `rationales` | Motive tags supported by explicit source quotes (paired with `motive_quotes` rows) | Intervention + `gta_stated_motive_log` |

## Criticality rubric

Applied per issue found, when writing an issue comment:

- **Critical** — the field is wrong in a way that changes the measure's nature or direction. *Example:* entry classifies as Import tariff, source shows Export tax — these are opposite-direction measures affecting different firms. Blocks publishing.
- **Important** — the field is wrong but the measure's nature is correctly identified. *Example:* implementation date off by three months; HS code 720810 in entry, source specifies 720820. Requires fix before publishing.
- **Minor** — cosmetic, formatting, or optional-field drift that doesn't change any downstream analysis. *Example:* title casing, superfluous whitespace. Publishable without fix.

## Verdict mapping

Once the field-by-field scan is complete:

| Findings | Action (review tool calls in order) |
|---|---|
| No Critical and no Important issues | `add_framework(495)` → `set_status(3, "Publishable")` |
| Only Minor issues, or no issues but needs Step 2 | `set_status(19, "Passing to Step 2")` |
| Any Critical or Important | `add_comment(...)` per issue → `set_status(6, "Under revision")` |

Always finish with `log_review(decision, fields_validated, issues_found, actions_taken)` to write the audit trail.

## Hard rules

1. **Never publish something you cannot verify.** If the source is unreachable / unreadable, the verdict is `Under revision` with a comment stating the source issue — never `Publishable`.
2. **Never assert data exists when `*None recorded*` is shown.** That marker comes from `format_measure_detail` after the DB returned an empty set. It is the source of truth for that field in that query.
3. **Quote the source verbatim in any Critical / Important comment.** Paraphrasing makes the comment un-auditable.
4. **One issue per comment.** Do not stack multiple fields into a single comment block.
5. **Do not mix personas.** Always review under 9900 (Sancho Claudino). If you find yourself wanting to *edit* the entry, stop — that's the author persona's job (Sancho Claudito, 9901), and mixing corrupts the audit trail.

## TODO

This file captures the minimum mechanical review surface. Domain-specific GTA handbook rules (Red/Amber/Green thresholds, jurisdiction-code edge cases, horizontal-measure criteria) should be appended here as they're codified. The public `sgept-gta-mcp/resources/reference/glossary.md` is a useful starting point for terminology but was written for external users, not reviewers.
