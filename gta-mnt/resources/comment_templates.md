# Comment Templates

The `comment_text` parameter of `gta_mnt_add_comment` accepts free-form markdown. Three structured formats are canonical — they match the helpers in `src/gta_mnt/formatters.py` and are what the human referee expects to see in Sancho Claudino comments.

Use the Python helpers in application code rather than hand-assembling the markdown in prompts.

## 1. Issue comment

For a specific field that needs to change. One comment per field.

```python
from gta_mnt.formatters import format_issue_comment

text = format_issue_comment(
    field="intervention_type",
    criticality="Critical",        # "Critical" | "Important" | "Minor"
    current_value="Subsidy",
    suggested_value="Export tax",
    rationale="Source clearly states the new charge is an outbound duty on iron-ore shipments, not a subsidy to iron-ore producers.",
    source_quote="Article 3: An export tax of 5% applies to all iron-ore consignments exceeding 10,000 tonnes.",
    source_ref="Official Gazette, 15 Jan 2026",
)
gta_mnt_add_comment(measure_id=state_act_id, comment_text=text)
```

### Criticality levels

- **Critical**: the entry misclassifies the measure; consumers of the data would draw wrong conclusions. Blocks publishing.
- **Important**: a meaningful field is wrong or missing, but the measure's nature is correctly identified. Requires fix before publishing.
- **Minor**: cosmetic / formatting / optional-field drift. Publishable without fix.

## 2. Verification comment

For a critical decision the entry got right. Positive evidence that a contested field was reviewed and stands.

```python
from gta_mnt.formatters import format_verification_comment

text = format_verification_comment(
    decision="Intervention type correctly classified as Tariff",
    source_quote="Tariff schedule entry 7208.10 lists the new HS-specific duty at 10%.",
    source_ref="Customs Notice 2026-01",
    explanation="The 10% figure appears in the official tariff schedule under the HS chapter 72 entry that matches the product scope of this measure.",
)
```

## 3. Review-complete comment

Terminal comment summarising the review. One per measure, at the end.

```python
from gta_mnt.formatters import format_review_complete_comment

text = format_review_complete_comment(
    verified_fields=["intervention_type", "affected_jurisdiction", "implementation_date"],
    critical_decisions=["Tariff classification (confirmed via schedule lookup)",
                        "Sectoral scope (narrowed from all steel to HS 7208 only)"],
)
```

## Quote handling

All three helpers pass quoted text through `format_issue_comment`'s caller unchanged. Long quotes get truncated to 500 chars with `[...]` via `formatters.truncate_quote(...)` — call it explicitly if you're hand-assembling text that might exceed 500 chars.

## What goes where

- **Issue comments**: in the database via `gta_mnt_add_comment`, and also appended to the on-disk `comments.md` audit trail automatically.
- **Review-complete comment**: usually the same path. Always end with one for any reviewed measure.
- **Review log**: separate artifact written by `gta_mnt_log_review` to `review-log.md` — this is the *structured* machine-readable summary, distinct from the human-readable comment thread.
