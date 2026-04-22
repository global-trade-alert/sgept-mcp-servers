# DPA Source Extraction Notes

Practical gotchas for `dpa_mnt_get_source`. Read this before hand-validating source mismatches that look like bugs — most of them are known, documented behaviour.

## Fetch priority

```
lux_source_log.source_url (primary)   ─▶ if reachable (2xx), fetch + extract
                    │
                    ▼ (null / unreachable)
lux_file_log.file_url (S3 HTTP)        ─▶ if reachable, fetch + extract
                    │
                    ▼
raise ToolError("No source URL available for event ...")
```

`dpa_mnt_get_source` writes the fetched bytes to `$DPA_MNT_REVIEW_STORAGE_PATH/<intervention_id>/evt-<event_id>-source.<ext>` on success, and the originating URL to the sibling `evt-<event_id>-source-url.txt`. Subsequent calls on the same event re-fetch (the server does not short-circuit from disk) — this is intentional, so the review always hits live source state.

## PDF extraction

- **Scanned PDFs** (image-only, no text layer): `pypdf` returns empty strings. The tool emits `[PDF extraction failed - likely scanned document. Refer to source URL.]`. **Do not** infer "the event has no content" from an empty extract — the text is in the scan, just not machine-readable. Fall back to the source URL or ask for an OCR pass.
- **Multi-column layouts**: pypdf orders text by position, which mangles two-column legal documents. Reading pass-by-pass rather than trusting a single flat extract is safer.
- **Encrypted PDFs**: pypdf raises; the tool wraps the message as `[PDF extraction error: ...]`. Re-request with `fetch_content=False` and read the archived file directly.

## HTML extraction

- `BeautifulSoup.get_text()` with the `lxml` parser strips tags but does not strip nav / footer / cookie banners. Expect noise around the actual policy text. Don't quote boilerplate as evidence.
- Pages rendered client-side (React / Vue SPAs) return a shell without content. httpx does not execute JavaScript. If the extracted text is suspiciously short and the URL looks like a SPA, the content isn't there — go to the S3 archive via `file_url` if available.
- DPA routinely cites press releases, regulator blog posts, and ministerial statements — all of which are dynamic pages. A minute spent confirming the fetched text looks like the policy (not a navigation shell) is cheap.

## Display flag semantics

`lux_event_source.display_on_flag`:
- `1` — primary source, shown on the DPA dashboard's front-page event view. This is the source the reviewer should treat as authoritative.
- `0` — contextual / background source. May be a news report rather than the implementing document. Use for corroboration, never as the sole evidence for a critical field.

MNT sorts sources by `display_on_flag DESC, source_id ASC`, so `source_index=0` is always the primary when one exists.

## S3 retrieval (via file_url)

- DPA uses HTTP S3 URLs (`https://s3.example.com/...`) rather than `s3://` URIs, so `httpx` handles them directly — no boto3 path. Credentials only matter if an internal S3 bucket requires signed URLs upstream; that's handled by whoever wrote `file_url`.
- If `file_url` returns 403 / 404 repeatedly, the S3 object was rotated or the upstream pipeline failed to upload. Fall back to `source_url` and log the issue for the editorial team.

## When the source contradicts the entry

This is the main reason to fetch sources at all. The canonical Buzessa pattern:

1. Extract the claim from the DB (via `dpa_mnt_get_event`).
2. Extract the evidence from the source (via `dpa_mnt_get_source`).
3. If they disagree on a critical field, post an issue comment quoting the source verbatim (use `format_issue_comment`). Never paraphrase the quote.
4. If they agree on a contested field, post a verification comment (use `format_verification_comment`).

## Known-noisy sources

Populate from observed failures as the editorial team reports them. Initial seed:

- TODO: list ministries / regulators whose "official" URL schemes break frequently, forcing S3 fallback.
