# GTA-MNT MCP Server

**Version:** 0.1.0
**Status:** Production Ready ✅
**Purpose:** Internal MCP server for automated GTA Step 1 review (Sancho Claudino system)

---

## Overview

The GTA-MNT (GTA Monitoring) MCP server powers the **Sancho Claudino automated review workflow** for Global Trade Alert entries. The system validates Step 1 entries against official sources and creates structured comments for human referee review.

### Key Features

- **Step 1 Queue Management:** List measures awaiting review, ordered by recency
- **Official Source Retrieval:** Fetch from S3 archives (priority) or direct URLs
- **PDF/HTML Text Extraction:** Extract text from archived documents using pypdf + BeautifulSoup
- **Structured Comment Creation:** Issue, verification, and review complete comments with markdown formatting
- **Status Management:** Update measure status (approve/send to revision)
- **Framework Tagging:** Mark reviewed measures with "sancho claudino review" framework ID 495
- **Template Library:** Access standardized comment templates
- **Persistent Artifact Storage:** Save sources, comments, and review logs to disk for audit trail

### Review Workflow

```
1. List queue → Get measure → Get source
2. AI validates against source
3. Add comments (issues OR verification)
4. Approve: Add framework tag
   Disapprove: Set status to "Under revision"
```

---

## Installation

### Prerequisites

- Python 3.10+
- `uv` package manager
- GTA account with API access (email/password for JWT authentication)
- AWS S3 credentials (for archived sources)

### Setup

```bash
# Navigate to project directory
cd sgept-dev/sgept-mcp-servers/gta-mnt

# Install dependencies (47 packages)
uv sync

# Set environment variables
export GTA_AUTH_EMAIL="your-email@globaltradealert.org"
export GTA_AUTH_PASSWORD="your-password"
export AWS_ACCESS_KEY_ID="your-aws-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret"
export AWS_S3_REGION="eu-west-1"
```

---

## Usage

### Running the Server Locally

```bash
# Standalone mode
uv run gta-mnt

# Via Python module
uv run python -m gta_mnt.server
```

### Claude Desktop Integration

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gta-mnt": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/johannesfritz/Documents/GitHub/jf-private/jf-dev/sgept-dev/sgept-mcp-servers/gta-mnt",
        "run",
        "gta-mnt"
      ],
      "env": {
        "GTA_AUTH_EMAIL": "your-email@globaltradealert.org",
        "GTA_AUTH_PASSWORD": "your-password",
        "AWS_ACCESS_KEY_ID": "your-aws-key",
        "AWS_SECRET_ACCESS_KEY": "your-aws-secret",
        "AWS_S3_REGION": "eu-west-1"
      }
    }
  }
}
```

### Available Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `gta_mnt_list_step1_queue` | List measures awaiting Step 1 review | `limit`, `offset`, `implementing_jurisdictions`, `date_entered_review_gte` |
| `gta_mnt_get_measure` | Get complete measure details with interventions and comments | `state_act_id`, `include_interventions`, `include_comments` |
| `gta_mnt_get_source` | Fetch official source (S3 priority, URL fallback) | `state_act_id`, `fetch_content` |
| `gta_mnt_add_comment` | Add structured review comment (authored by user_id=9900) | `measure_id`, `comment_text`, `template_id` (optional) |
| `gta_mnt_set_status` | Update measure status with log entry | `state_act_id`, `new_status_id`, `comment` (optional) |
| `gta_mnt_add_framework` | Tag measure with "sancho claudino review" (framework_id=495) | `state_act_id`, `framework_name` (optional) |
| `gta_mnt_list_templates` | List available comment templates | `include_checklist` |
| `gta_mnt_log_review` | Save review log to persistent storage | `state_act_id`, `source_url`, `fields_validated`, `issues_found`, `decision`, `actions_taken` |

### Example Workflow

```
# 1. List queue
gta_mnt_list_step1_queue(limit=10)

# 2. Get measure details
gta_mnt_get_measure(state_act_id=12345, include_interventions=True)

# 3. Get source document
gta_mnt_get_source(state_act_id=12345, fetch_content=True)

# 4a. If issues found - add issue comment
gta_mnt_add_comment(
  measure_id=12345,
  comment_text="## FIELD: intervention_type\n**Criticality:** Critical..."
)

# 4b. Set to revision
gta_mnt_set_status(
  state_act_id=12345,
  new_status_id=6,  # Under revision
  comment="Critical field errors identified"
)

# OR 5a. If no issues - add framework tag
gta_mnt_add_framework(state_act_id=12345)

# 5b. Keep in Step 1 status (no action needed)
```

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│              Sancho Claudino Review Workflow                │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐ │
│  │ Quality      │──▶│ gta_mnt MCP  │──▶│ GTA Django API │ │
│  │ Reviewer     │   │ Server       │   │ + S3 Storage   │ │
│  │ Agent        │   └──────────────┘   └────────────────┘ │
│  └──────────────┘           │                  │           │
│                      ┌───────▼──────────────────▼────┐     │
│                      │ Tools (7):                    │     │
│                      │ • List queue                  │     │
│                      │ • Get measure                 │     │
│                      │ • Get source (S3→URL→PDF)     │     │
│                      │ • Add comment (user_id=9900)  │     │
│                      │ • Set status (2/3/6)          │     │
│                      │ • Add framework (id=495)      │     │
│                      │ • List templates              │     │
│                      └───────────────────────────────┘     │
└────────────────────────────────────────────────────────────┘
```

### Status IDs

| ID | Name | Meaning |
|----|------|---------|
| 2 | Step 1 | Awaiting initial review |
| 3 | Publishable | Passed review |
| 6 | Under revision | Issues found, sent back |

### Database IDs (configured in `constants.py`)

- **User ID:** 9900 (sancho_claudino) - Author of automated comments
- **Framework ID:** 495 ("sancho claudino review") - Tracks reviewed measures

---

## Persistent Artifact Storage

All review artifacts are automatically saved to disk for audit trail purposes.

### Storage Location

```
/Users/johannesfritz/Documents/GitHub/jf-private/jf-thought/sgept-monitoring/gta/sc-reviews/{state_act_id}/
```

### Artifacts Stored Per Review

Each reviewed measure gets a dedicated folder containing:

| File | Purpose | Updates |
|------|---------|---------|
| `source.{pdf\|html\|txt}` | Downloaded official source document | Overwrites on new fetch |
| `source-url.txt` | Original source URL for reference | Overwrites on new fetch |
| `comments.md` | All review comments posted | Appends each comment with timestamp |
| `review-log.md` | Review summary (fields, issues, decision, actions) | Overwrites with latest state |

### Automatic Storage Triggers

Storage happens automatically when you use these tools:

- **`gta_mnt_get_source`** → Saves source file + URL
- **`gta_mnt_add_comment`** → Appends to comments.md
- **`gta_mnt_log_review`** → Creates/updates review-log.md

### Example Folder Structure

```
sc-reviews/
├── 12345/
│   ├── source.pdf                # Original policy document
│   ├── source-url.txt            # https://example.com/policy.pdf
│   ├── comments.md               # All comments posted
│   └── review-log.md             # Review summary
├── 12346/
│   ├── source.html
│   ├── source-url.txt
│   ├── comments.md
│   └── review-log.md
```

### Review Log Format

```markdown
# Review Log - StateAct 12345

**Review Date:** 2026-02-01 10:30:00 UTC
**Decision:** APPROVE
**Source:** https://example.com/policy.pdf

---

## Fields Validated
- Title
- Implementation date
- Intervention type

---

## Issues Found
*No issues found - entry validated successfully*

---

## Actions Taken
- Framework tag added (id=495)

---

*Review conducted by Sancho Claudino automated system*
```

---

## Comment Formatters

The server provides pre-built comment formatters for structured feedback:

### Issue Comment
```python
format_issue_comment(
    field="intervention_type",
    criticality="Critical",
    current_value="Subsidy",
    suggested_value="Export tax",
    rationale="Source clearly states export tax...",
    source_quote="Article 3: An export tax of 5%...",
    source_ref="Official Gazette, 15 Jan 2026"
)
```

### Verification Comment
```python
format_verification_comment(
    decision="Intervention type correctly classified",
    source_quote="Tariff schedule shows 10% duty",
    source_ref="Customs Notice 2026-01",
    explanation="The source clearly indicates..."
)
```

### Review Complete Comment
```python
format_review_complete_comment(
    verified_fields=["intervention_type", "affected_jurisdiction"],
    critical_decisions=["Tariff classification", "Sectoral scope"]
)
```

---

## Testing

### Run Tests

```bash
# All tests (35 tests, 100% pass rate)
uv run pytest -v

# Unit tests only
uv run pytest tests/unit/ -v

# With coverage
uv run pytest --cov=gta_mnt --cov-report=term-missing
```

### Test Coverage

- **API Client:** 9 tests (all CRUD operations, auth, error handling)
- **Formatters:** 13 tests (all formatters, markdown generation)
- **Source Fetcher:** 13 tests (S3/URL/PDF/HTML extraction, error handling)

**Total:** 35 tests, 100% pass rate ✅

---

## Development Status

**Current Phase:** Production Ready

**Completed:**
- ✅ PR-0/1: Database setup (user_id=9900, framework_id=495)
- ✅ PR-3/4/5: Spike reports (comment API, S3 access, PDF extraction)
- ✅ WS1: Project scaffolding and authentication (JWT)
- ✅ WS2: List Step 1 queue tool
- ✅ WS3: Get measure detail tool
- ✅ WS4: Get source tool (S3/URL/PDF/HTML)
- ✅ WS5: Add comment tool (user_id=9900)
- ✅ WS6: Set status tool
- ✅ WS7: Add framework tool (framework_id=495)
- ✅ WS9: Comment formatters (4 types)
- ✅ WS10: List templates tool
- ✅ WS11: Comprehensive test suite (35 tests)
- ✅ WS12: Documentation finalization

**Not Implemented:**
- ❌ WS8: Log review complete (deprecated - framework tagging handles this)

---

## API Reference

### Authentication

The server uses JWT authentication with automatic token refresh:

```python
JWTAuthManager(email, password)
# Automatically:
# - Fetches JWT tokens on first request
# - Refreshes expired tokens
# - Includes tokens in all API requests
```

### Error Handling

All tools return structured error messages:

```
✅ Success: {result message}
❌ Error: {specific error with context}
```

---

## Files Structure

```
gta-mnt/
├── src/gta_mnt/
│   ├── __init__.py
│   ├── server.py           # MCP tool definitions (7 tools)
│   ├── api.py              # GTA API client (6 methods)
│   ├── auth.py             # JWT authentication
│   ├── models.py           # Pydantic input/output models
│   ├── formatters.py       # Comment formatters (4 types)
│   ├── source_fetcher.py   # S3/URL/PDF/HTML retrieval
│   └── constants.py        # Database IDs (user, framework)
├── tests/
│   └── unit/
│       ├── test_api.py             # 9 tests
│       ├── test_formatters.py      # 13 tests
│       └── test_source_fetcher.py  # 13 tests
├── pyproject.toml          # Dependencies (47 packages)
├── pytest.ini              # Test configuration
├── README.md               # This file
└── QUICKSTART.md           # Quick setup guide
```

---

## Documentation

- **Technical Specification:** `inbox/specs/SPEC-gta-mnt-mcp-server.md`
- **UAT Protocol:** `.claude/protocols/uat-gta-mnt-mcp-server.md`
- **Implementation Plan:** `inbox/plans/PLAN-2026-011.md`
- **Execution Reports:**
  - WS1: `inbox/PLAN-2026-011-WS1-COMPLETE.md`
  - WS2-6: `inbox/PLAN-2026-011-WS2-WS6-COMPLETE.md`
  - WS5/7: `inbox/PLAN-2026-011-WS5-WS7-COMPLETE.md`

---

## Troubleshooting

### Token Refresh Issues
If JWT tokens expire mid-session, the auth manager auto-refreshes. Check logs for authentication errors.

### S3 Access Denied
Verify AWS credentials and region match S3 bucket configuration.

### PDF Extraction Returns Empty
Scanned PDFs may not extract text. The tool returns a warning message and suggests referring to source URL.

---

## License

Internal SGEPT tool - Not for public distribution.
