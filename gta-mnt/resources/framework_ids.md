# Framework IDs

Framework tags are attached via `gta_mnt_add_framework(state_act_id, framework_name)`. The server rejects any framework name not in this table with a `ToolError` before touching the DB.

| ID | Name | Attached by | Purpose |
|----|------|-------------|---------|
| 495 | `sancho claudino review` | Sancho Claudino (reviewer, 9900) | Marks a measure as having passed Sancho Claudino's review. Used by `exclude_framework_id=495` on the queue listings to skip already-reviewed measures. |
| 500 | `sancho claudito reported` | Sancho Claudito (author, 9901) | Marks a measure as first-drafted by Sancho Claudito. Used for provenance auditing. |

## When to attach

- **495**: immediately after a measure passes review with no issues. Part of the "publishable" path (`set_status(3, ...)` + `add_framework(495)`).
- **500**: immediately after `gta_mnt_create_state_act` completes successfully, before handing off to Step 1 review via `set_status(2, ...)`.

## When not to attach

- Never attach 495 if the review turned up critical or important issues. Those measures go to `set_status(6, "Under revision")` without the tag.
- Never attach 495 or 500 to a measure you didn't create/review yourself in this workflow — the tag is a claim of authorship/reviewership and corrupts the audit trail if misused.

## Canonical source

`src/gta_mnt/constants.py:FRAMEWORK_IDS` is the single source of truth. If this file and `constants.py` disagree, `constants.py` wins — this file is documentation, not config.
