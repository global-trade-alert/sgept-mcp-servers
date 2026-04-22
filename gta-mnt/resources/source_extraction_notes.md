# Source Extraction Notes

Practical gotchas for `gta_mnt_get_source`. Read this before hand-validating source mismatches that look like bugs — most of them are known, documented behaviour.

## Fetch priority

```
S3 archived file (authoritative) ─▶ if present, use this
             │ (not present)
             ▼
Direct URL fetch via httpx          ─▶ if 2xx, extract
             │ (404, 5xx, timeout)
             ▼
Error — raise ToolError
```

`gta_mnt_get_source` will write the fetched bytes to `$GTA_MNT_REVIEW_STORAGE_PATH/<state_act_id>/source.<ext>` on success. Subsequent calls do not re-fetch if the archived file already exists.

## PDF extraction

- **Scanned PDFs** (image-only, no text layer): `pypdf` returns empty strings. The tool emits a warning and points you at the source URL. **Do not** infer "the measure has no content" from an empty extract — the text is in the scan, just not machine-readable. Fall back to the source URL or ask for an OCR pass.
- **Multi-column layouts**: pypdf orders text by position, which mangles two-column legal documents. Reading pass-by-pass rather than trusting a single flat extract is safer.
- **Encrypted PDFs**: pypdf raises; the tool surfaces this as a generic error. Re-request with `fetch_content=False` and read the archived file directly.

## HTML extraction

- `BeautifulSoup.get_text()` with the `lxml` parser strips tags but does not strip nav / footer / cookie banners. Expect noise around the actual policy text. Don't quote boilerplate as evidence.
- Pages rendered client-side (React / Vue SPAs) return a shell without content. httpx does not execute JavaScript. If the extracted text is suspiciously short and the URL looks like a SPA, the content isn't there — go to the archived PDF if available.

## S3 retrieval

- Requires `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_REGION`. If any are missing, boto3 raises an unhandled exception (not a ToolError) — this is intentional. Missing credentials are a deployment bug, not an input error.
- `source-url.txt` is written alongside `source.<ext>` and preserves the original URL even after the S3 key rotates.

## Known-untrustworthy sources

Jurisdictions where the "official gazette" URL is notoriously unstable and the S3 archive is the only reliable copy:

- TODO: list jurisdictions / ministries that have broken their URL schemes repeatedly. Populate from observed failures.

## When the source contradicts the entry

This is the main reason to fetch sources at all. The canonical Sancho-Claudino pattern:

1. Extract the claim from the DB (via `gta_mnt_get_measure`).
2. Extract the evidence from the source (via `gta_mnt_get_source`).
3. If they disagree on a critical field, post an issue comment quoting the source verbatim (use `format_issue_comment`). Never paraphrase the quote.
4. If they agree on a contested field, post a verification comment (use `format_verification_comment`).
