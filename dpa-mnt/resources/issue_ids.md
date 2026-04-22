# DPA Issue IDs (BC review + thematic tags)

Issues in `lux_issue_list` function as **thematic tags** applied to interventions (not events). The DPA MNT server attaches exactly one of them — `BC_REVIEW_ISSUE_ID = 83` — via `dpa_mnt_add_review_tag`. The rest are listed here as the reviewer's working vocabulary when reading `intervention.issues` in event detail output.

## BC review tag (MNT-owned)

| ID | Name | Attached by | Purpose |
|----|------|-------------|---------|
| 83 | BC review | Buzessa Claudini (reviewer, 9902) | Marks that at least one event on the intervention has been reviewed by the Buzessa automated system. Idempotent — safe to call repeatedly for the same intervention. |

### When to attach

- Immediately after **any** completed review (PASS, CONDITIONAL, or FAIL). The tag records that review happened, not its outcome; the outcome lives in `lux_event_status_log`.
- Once per intervention is enough — the underlying insert is guarded by an existence check.

### When not to attach

- Never to an intervention you didn't review through this server. The tag is a claim of reviewership.

## Framework ID 496 (deprecated)

`DPA_FRAMEWORK_ID = 496` was the first-pass mechanism before the issue-tag approach was adopted. It is kept in `constants.py` only to read old records. **Do not write framework 496 from new code.** If you see it on an intervention, assume it was left by a legacy run and do not re-apply.

## Thematic tags (read-only from MNT's perspective)

The full `lux_issue_list` is maintained by the DPA editorial team and covers themes like GDPR compatibility, AI safety, platform liability, cross-border data flow. MNT reads them for context when reviewing (they're rendered on event detail and intervention context output) but does not create or delete them.

To enumerate the current set for display purposes, the dashboard's editorial UI is the canonical surface — run a one-off `SELECT issue_id, issue_name FROM lux_issue_list ORDER BY issue_name` to snapshot for a given review.

## Canonical source

`src/dpa_mnt/constants.py:BC_REVIEW_ISSUE_ID` is the single source of truth. If this file and `constants.py` disagree, `constants.py` wins — this file is documentation, not config.
