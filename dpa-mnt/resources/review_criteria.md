# Buzessa Claudini — DPA Review Criteria

A Step-1 review of a DPA event is an independent check of the database content against the cited official source. The reviewer is not the author: the question is *does what the entry says match what the source says?* — not *did the author make the best possible choices?*

## Fields to check (minimum set)

This is the minimum surface. A review that covers fewer fields is incomplete. A review that covers more is fine — the point is that **none** of these may be skipped.

| Field | What to check | Where it lives |
|---|---|---|
| `event_title` | Matches the short name used in the source | `lux_event_log` |
| `event_description` | Summarises (not copies) what the source announces | `lux_event_log` |
| `event_date` | Matches the dated action in the source | `lux_event_log` |
| `event_type_id` | Event class (Bill Introduction, Guidance, Enforcement Action, etc.) matches the source's own language | `lux_event_log` → `lux_event_type_list` |
| `action_type_id` | Action taken (Announcement, Update, Publication, Withdrawal, etc.) matches the source | `lux_event_log` → `lux_action_type_list` |
| `gov_branch_id` / `gov_body_id` | The branch and specific body named on the source | `lux_event_log` → `lux_government_branch_list` / `lux_government_body_list` |
| `is_case` | True only if the event records a specific adjudicated case, not a generic rule | `lux_event_log` |
| `intervention_title` | Short name of the parent intervention matches what the source calls this initiative | `lux_intervention_log` |
| `policy_area` | Primary policy area + M2M policies matches the source's subject matter | `lux_intervention_log.policy_area_id` + `lux_intervention_policy_area` |
| `intervention_type` | Instrument class (Statute, Regulation, Guidance, Executive Order, etc.) matches the source | `lux_intervention_type_list` |
| `implementation_level` | National / subnational / regional level matches the enacting authority | `lux_implementation_level_list` |
| `implementing_jurisdictions` | Jurisdiction(s) enacting the measure | `lux_intervention_implementer` |
| `economic_activities` | Sectors covered actually line up with the source's scope | `lux_intervention_econ_activity` |
| `sources` | Cited URL is the authoritative source; `display_on_flag` correctly flags primary vs contextual | `lux_event_source` → `lux_source_log` |
| `benchmarks` | Any external frameworks the intervention benchmarks against (GDPR, etc.) match the source | `lux_intervention_benchmark_log` |

## Criticality rubric

Applied per issue found, when writing an issue comment:

- **Critical** — the field is wrong in a way that changes the event's nature or jurisdictional reach. *Example:* entry classifies as Guidance, source shows Enforcement Action with a €10m fine — these have materially different regulatory weight. Blocks publishing.
- **Important** — the field is wrong but the event's nature is correctly identified. *Example:* implementation date off by a month; wrong government body within the correct branch. Requires fix before publishing.
- **Minor** — cosmetic, formatting, or optional-field drift that doesn't change downstream analysis. Publishable without fix; noted for the editor.

## Verdict mapping

Once the field-by-field scan is complete:

| Findings | Verdict | Action (review tool calls in order) |
|---|---|---|
| No Critical, no Important issues | PASS | `add_review_tag(event_id)` → `set_status(6, "Revised")` |
| Issues but none blocking | CONDITIONAL | `add_comment(...)` per issue → `add_review_tag(event_id)` → `set_status(5, "Under revision")` |
| Any Critical or Important | FAIL (critical) | `add_comment(...)` per issue → `add_review_tag(event_id)` → `set_status(4, "Concern")` |
| Event not appropriate for DPA | FAIL (out of scope) | `add_comment(...)` explaining → `add_review_tag(event_id)` → `set_status(14, "Archived")` |

Always finish with `dpa_mnt_log_review(decision, fields_validated, issues_found, actions_taken)` to write the audit trail.

## Hard rules

1. **Never pass something you cannot verify.** If the source is unreachable / unreadable, the verdict is `Under revision (5)` with a comment stating the source issue — never `Revised (6)`.
2. **Never assert data exists when a field renders blank.** Empty means the DB returned nothing for that join; treat that as ground truth for the query, not as an omission to fill in.
3. **Quote the source verbatim in any Critical / Important comment.** Paraphrasing makes the comment un-auditable.
4. **One issue per comment.** Do not stack multiple fields into a single comment block.
5. **Do not mix personas.** Always review under 9902 (Buzessa Claudini). If the entry needs *editing*, stop — that is the author persona's job (Buzetta Claudini, 9903), and mixing corrupts the audit trail.
6. **Gate 0 is mandatory.** Always call `dpa_mnt_get_intervention_context` before reviewing any event. Published siblings (status 7) are the verified context the review compares against.
