# DPA Status ID Decision Tree

The `dpa_mnt_set_status` tool accepts one of **six** status IDs from `lux_event_status_list`. `SetStatusInput.new_status_id` rejects anything else with a `ValidationError` enumerating the valid set.

| ID | Name | Who uses it | Typical trigger |
|----|------|-------------|-----------------|
| 1 | In Progress | Author (Buzetta Claudini, 9903) | Event just created; draft still being assembled |
| 2 | Step 1 Review (AT) | Author on handoff | Author finished drafting; ready for Activity Tracker review |
| 3 | Publishable (PASS) | Reviewer (Buzessa Claudini, 9902) | Passed review; safe to publish |
| 4 | Concern (CONDITIONAL / ESCALATION) | Reviewer | Review surfaced issues but not enough to fail; escalate before publish |
| 5 | Under Revision (FAIL) | Reviewer | Critical / important issues found; send back to author |
| 7 | Published | Editorial publishing step (not MNT) | After review outcome locked in, dashboard flips to 7 |

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
        ├── No issues found ──────────▶ set_status(3, ...)         [Publishable / PASS]
        │                               add_review_tag(event_id)    (issue 83 on intervention)
        │
        ├── Issues but not blocking ──▶ set_status(4, ...)         [Concern / CONDITIONAL]
        │   add_comment(issue ...)     add_review_tag(event_id)
        │
        └── Critical / important ────▶ set_status(5, ...)         [Under Revision / FAIL]
            issues found              add_comment(issue ...) for each
                                      add_review_tag(event_id)
```

Always finish with `dpa_mnt_log_review(decision, fields_validated, issues_found, actions_taken)` — the on-disk audit trail.

## Author flow (Buzetta Claudini)

Entry creation tools are not in v0.2.0; DPA MNT v0.2.0 is review-only. When author tools ship (v0.3+), the pattern will be:

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

- **Do not** call `set_status(3, ...)` as an author — that is a reviewer verdict.
- **Do not** call `set_status(6, ...)` in DPA. 6 is a **GTA** status (`Under revision` for GTA) and is NOT a valid DPA status. The validator will reject it. Cross-wiring the two servers silently used to be the most common LLM-drift bug.
- **Do not** call `set_status(7, ...)` from MNT. Publishing is an editorial action; MNT tools don't own it.
- **Do not** invent IDs. Anything outside `{1, 2, 3, 4, 5, 7}` is rejected at the input validator — the error message lists every valid `id=name` pair.
