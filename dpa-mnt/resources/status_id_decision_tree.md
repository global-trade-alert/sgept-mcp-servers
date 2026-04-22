# DPA Status ID Decision Tree

The `dpa_mnt_set_status` tool accepts one of **eight** status IDs from `lux_event_status_list`. `SetStatusInput.new_status_id` rejects anything else with a `ValidationError` enumerating the valid set.

| ID | Name | Who uses it | Typical trigger |
|----|------|-------------|-----------------|
| 1 | In Progress | Author (Buzetta Claudini, 9903) | Event just created; draft still being assembled |
| 2 | Step 1 Review (AT) | Author on handoff | Author finished drafting; ready for Activity Tracker review |
| 3 | Publishable (legacy) | Rarely written today | Early-system pre-verdict status |
| 4 | AT: Concern | Reviewer (Buzessa Claudini, 9902) | **FAIL (critical)** verdict — blocking issues found |
| 5 | AT: Under Revision | Reviewer | **CONDITIONAL** verdict — issues but not blocking |
| 6 | AT: Revised | Reviewer | **PASS** verdict — entry verified against source |
| 7 | Published | Editorial publishing step (not MNT) | After review outcome locked in, dashboard flips to 7 |
| 14 | Archived | Reviewer | **FAIL (out of scope)** verdict — entry not appropriate for DPA |

## BC review verdict → status mapping

This is the authoritative mapping used by the `/dpa-review-queue` command in `jf-thought/sgept-monitoring/dpa/.claude/commands/`:

| Verdict | new_status_id | status_name |
|---|---|---|
| PASS | `6` | AT: Revised |
| CONDITIONAL | `5` | AT: Under Revision |
| FAIL (critical) | `4` | AT: Concern |
| FAIL (out of scope) | `14` | Archived |

## Reviewer flow (Buzessa Claudini)

```
Event is in status 2 (Step 1 Review / AT)
        │
        ▼
Gate 0: dpa_mnt_get_intervention_context(intervention_id)
        │  — verify lifecycle / consistency against prior events
        ▼
Gate 1: dpa_mnt_get_event(event_id)
        │  — pull full event + intervention + sources + comments
        ▼
Gate 2: dpa_mnt_get_source(event_id, source_index=...)
        │  — fetch official source, extract evidence
        ▼
Run field-by-field checks (see review_criteria.md)
        │
        ├── No issues found ──────────▶ set_status(6, ...)          [PASS / AT: Revised]
        │                               add_review_tag(event_id)     (issue 83 on intervention)
        │
        ├── Issues but not blocking ──▶ set_status(5, ...)          [CONDITIONAL / Under revision]
        │   add_comment(issue ...)     add_review_tag(event_id)
        │
        ├── Critical issues ──────────▶ set_status(4, ...)          [FAIL / AT: Concern]
        │   add_comment(issue ...)     add_review_tag(event_id)
        │
        └── Out of scope ────────────▶ set_status(14, ...)          [FAIL out-of-scope / Archived]
            add_comment(issue ...)     add_review_tag(event_id)
```

Always finish with `dpa_mnt_log_review(decision, fields_validated, issues_found, actions_taken)` — the on-disk audit trail.

## Author flow (Buzetta Claudini)

Entry creation tools are not in v0.2.x; DPA MNT is review-only through at least v0.2. When author tools ship (v0.3+), the pattern will be:

```
create_event(...)                     # status 1 forced by the tool
        │
        ▼
add sources, relations, agents, ...
        │
        ▼
set_status(2, ...)                    # handoff to Step 1 review
```

## Do not

- **Do not** confuse DPA's `6` with GTA's `6`. On DPA, `6` = AT: Revised (PASS). On GTA, `6` = Under revision (FAIL). These are opposite outcomes. Cross-wiring between the two MCP servers is the single biggest class of silent mistake the validator guards against.
- **Do not** call `set_status(3, ...)` for new reviews. `3` (Publishable) is a legacy pre-verdict status; modern BC reviews write `4`, `5`, `6`, or `14`.
- **Do not** call `set_status(7, ...)` from MNT. Publishing is an editorial action; MNT tools don't own it.
- **Do not** invent IDs. Anything outside `{1, 2, 3, 4, 5, 6, 7, 14}` is rejected at the input validator — the error message lists every valid `id=name` pair.
