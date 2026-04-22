# DPA Comment Templates

The `comment_text` parameter of `dpa_mnt_add_comment` accepts free-form markdown. Three structured formats are canonical — they match the helpers in `src/dpa_mnt/formatters.py` and are what the human editor expects to see in Buzessa Claudini comments on the DPA Activity Tracker.

Use the Python helpers in application code rather than hand-assembling the markdown in prompts.

## 1. Issue comment

For a specific field that needs to change. **One comment per field**.

```python
from dpa_mnt.formatters import format_issue_comment

text = format_issue_comment(
    field="event_type",
    criticality="Critical",        # "Critical" | "Important" | "Minor"
    current_value="Guidance",
    suggested_value="Enforcement Action",
    rationale="Source announces a fine of EUR 10m under Article 83 GDPR, which is an enforcement action, not guidance.",
    source_quote="The Data Protection Authority imposed a fine of EUR 10,000,000 on Example Corp for infringement of Article 5(1)(a) GDPR.",
    source_ref="DPC press release, 12 Feb 2026",
)
dpa_mnt_add_comment(event_id=..., comment_text=text)
```

### Criticality levels

- **Critical**: the entry misclassifies the event in a way that changes its regulatory weight or jurisdictional reach; downstream consumers would draw wrong conclusions. Blocks publishing.
- **Important**: a meaningful field is wrong or missing, but the event's nature is correctly identified. Requires fix before publishing.
- **Minor**: cosmetic / formatting / optional-field drift. Publishable without fix; noted for the editor.

## 2. Verification comment

For a critical decision the entry got right. Positive evidence that a contested field was reviewed and stands.

```python
from dpa_mnt.formatters import format_verification_comment

text = format_verification_comment(
    decision="Event date correctly recorded as 2026-01-15",
    source_quote="Entered into force on 15 January 2026.",
    source_ref="Official Journal of the European Union, 2026/C 15/01",
    explanation="The source clearly states the entry-into-force date matches the entry's event_date value.",
)
```

## 3. Review-complete comment

Terminal comment summarising the review. One per event, at the end.

```python
from dpa_mnt.formatters import format_review_complete_comment

text = format_review_complete_comment(
    verified_fields=["event_title", "event_date", "event_type", "gov_body", "implementing_jurisdictions"],
    critical_decisions=["Event type (Enforcement Action, confirmed via fine amount)",
                        "Gov body (DPC, confirmed via signatory)"],
)
```

## Quote handling

All three helpers pass quoted text through unchanged. Long quotes get truncated to 500 chars with `[...]` via `formatters.truncate_quote(...)` — call it explicitly if you're hand-assembling text that might exceed 500 chars.

## What goes where

- **Issue comments**: written to `api_comment_log` via `dpa_mnt_add_comment`, and also appended to the on-disk `evt-<event_id>-comments.md` audit trail automatically. The DPA Activity Tracker reads from `api_comment_log`.
- **Review-complete comment**: same path. Always end with one for any reviewed event.
- **Review log**: separate artifact written by `dpa_mnt_log_review` to `evt-<event_id>-review-log.md` — the *structured* machine-readable summary, distinct from the human-readable comment thread.
