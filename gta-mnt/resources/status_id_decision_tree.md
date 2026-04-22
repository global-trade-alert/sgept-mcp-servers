# Status ID Decision Tree

The `gta_mnt_set_status` tool accepts one of **five** status IDs. `SetStatusInput.new_status_id` rejects anything else with a `ValidationError`.

| ID | Name | Who uses it | Typical trigger |
|----|------|-------------|-----------------|
| 1 | In progress | Author (Sancho Claudito, 9901) | Entry just created; still being drafted |
| 2 | Step 1 | Author on handoff | Author finished drafting; ready for first review |
| 3 | Publishable | Reviewer (Sancho Claudino, 9900) | Passed review; safe to publish |
| 6 | Under revision | Reviewer | Critical / important issues found; send back to author |
| 19 | Step 2 | Reviewer | Passed Step 1; requires second-stage review |

## Reviewer flow (Sancho Claudino)

```
Measure is in status 2 (Step 1)
        │
        ▼
Run checks (source match, field completeness, classification)
        │
        ├── No issues found ──────────▶ set_status(3, ...)   [Publishable]
        │                               add_framework("sancho claudino review")
        │
        ├── Pass Step 1, needs more ──▶ set_status(19, ...)  [Step 2]
        │   review
        │
        └── Critical / important ────▶ set_status(6, ...)    [Under revision]
            issues found              add_comment(issue comment) for each
```

## Author flow (Sancho Claudito)

```
gta_mnt_create_state_act(...)                 # status 1 is forced by the tool
        │
        ▼
Add interventions, products, sectors, etc.
        │
        ▼
set_status(2, ...)                            # handoff to Step 1 review
add_framework("sancho claudito reported")     # audit tag
```

## Do not

- **Do not** call `set_status(3, ...)` as an author. Publishable is a reviewer verdict.
- **Do not** call `set_status(1, ...)` as a reviewer unless you have explicit instruction to rewind a published measure.
- **Do not** invent IDs. Anything outside `{1, 2, 3, 6, 19}` is rejected at the input validator — see the message it emits for the authoritative list.
