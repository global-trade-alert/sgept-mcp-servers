# Layer 2 Assessment: GTA MCP Server
## Resources for Documentation - Analysis & Recommendations

**Assessment Date:** 2025-11-09
**Assessed By:** Claude Code
**MCP Server:** GTA MCP (`gta-mcp`)
**Version:** Current implementation
**Reference Framework:** [MCP Best Practices - Layer 2](./mcp_best_practices.md)

---

## Executive Summary

### Overall Layer 2 Maturity: ⭐⭐⭐⭐ (Excellent)

The GTA MCP server demonstrates **exemplary Layer 2 implementation** and serves as a strong reference for other MCP servers. The server successfully separates comprehensive documentation into on-demand resources, keeping tool descriptions concise while providing deep reference materials when needed.

**Key Metrics:**
- **16 resources** providing ~46,000 words of documentation
- **4 tools** with concise descriptions (~50 lines average)
- **Context savings:** ~40KB of documentation not loaded by default
- **Progressive disclosure:** 3-tier structure (tool → parameter → resource)

**Verdict:** This implementation already follows Layer 2 best practices. Recommendations focus on incremental improvements and exposing additional valuable content rather than fundamental restructuring.

---

## Current State Analysis

### 1. Resource Inventory

The GTA MCP server implements **16 resources** across two categories:

#### Reference Materials (Lookup Tables)
| Resource URI | Purpose | Size | Lines | Words |
|-------------|---------|------|-------|-------|
| `gta://reference/jurisdictions` | Complete country/jurisdiction codes | 18KB | 236 | 591 |
| `gta://reference/intervention-types` | Full intervention type catalog with examples | 152KB | 2,232 | 20,390 |
| `gta://reference/intervention-types-list` | Quick intervention type list | 7KB | 81 | - |
| `gta://reference/sectors-list` | CPC sector classification | 21KB | 333 | 2,356 |
| `gta://reference/mast-chapters` | MAST A-P taxonomy | 18KB | 421 | 2,492 |
| `gta://reference/eligible-firms` | Eligible firm types | 284B | 10 | - |
| `gta://reference/implementation-levels` | Government implementation levels | 454B | 8 | - |

#### Guides (How-To Documentation)
| Resource URI | Purpose | Size | Lines | Words |
|-------------|---------|------|-------|-------|
| `gta://guide/parameters` | Comprehensive parameter reference | 19KB | 568 | 2,222 |
| `gta://guide/query-examples` | 35+ real-world query examples | 20KB | 686 | 2,376 |
| `gta://guide/query-syntax` | Query syntax and strategy | 12KB | 429 | 1,551 |
| `gta://guide/exclusion-filters` | Keep_* parameter patterns | 14KB | 527 | 1,601 |
| `gta://guide/cpc-vs-hs` | Product classification guide | 7KB | 263 | 1,036 |
| `gta://guide/date-fields` | Date field explanations | 9KB | 230 | 1,266 |
| `gta://guide/searching` | Search best practices | 5KB | 155 | 696 |

#### Dynamic Resources (Lookup Functions)
| Resource URI Pattern | Purpose | Implementation |
|---------------------|---------|----------------|
| `gta://jurisdiction/{iso_code}` | Single jurisdiction lookup | Dynamic formatted output |
| `gta://intervention-type/{type_slug}` | Single intervention type details | Dynamic section extraction |

**Total Documentation: ~46,000 words / ~305KB**

### 2. Documentation Architecture

The implementation demonstrates excellent **three-tier progressive disclosure**:

#### Tier 1: Tool Descriptions (Always Loaded)
```python
@mcp.tool()
async def gta_search_interventions(params: SearchInput) -> str:
    """Search and filter trade policy interventions from the Global Trade Alert database.

    Use structured filters FIRST (countries, products, intervention types, dates),
    then add 'query' parameter ONLY for entity names (companies, programs).

    Key parameters:
    - implementing_jurisdictions: Countries implementing the measure
    - intervention_types: Specific intervention types
    - affected_products: HS codes or CPC codes for products
    - date_announced_gte/lte: Date range filters

    Common examples:
    1. US tariffs on China: implementing_jurisdictions=['USA'],
       affected_jurisdictions=['CHN'], intervention_types=['Import tariff']
    2. Global subsidies for Tesla: query='Tesla', mast_chapters=['L']

    For parameter reference: gta://guide/parameters
    For comprehensive examples: gta://guide/query-examples
    For query syntax: gta://guide/query-syntax
    For MAST chapters: gta://reference/mast-chapters
    """
```

**Analysis:**
- ✅ Concise purpose statement (2 sentences)
- ✅ Key guidance upfront ("Use structured filters FIRST")
- ✅ Parameter highlights (not full documentation)
- ✅ 2-3 concrete examples
- ✅ Clear resource pointers at end
- ✅ ~50 lines (well under 200-word guideline)

#### Tier 2: Parameter Descriptions (Pydantic Models)
```python
class SearchInput(BaseModel):
    implementing_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="List of implementing jurisdiction ISO codes (e.g., ['USA', 'CHN', 'DEU']). "
                   "Filter interventions by countries that implemented the measure. "
                   "See gta://reference/jurisdictions for complete list."
    )

    intervention_types: Optional[List[str]] = Field(
        default=None,
        description="List of specific intervention type names (e.g., ['Import tariff', 'State aid']). "
                   "Use for PRECISE targeting. For broader queries, use mast_chapters instead. "
                   "See gta://reference/intervention-types for complete catalog."
    )
```

**Analysis:**
- ✅ Brief inline examples (1-3 codes)
- ✅ Key distinction guidance ("PRECISE targeting vs broader queries")
- ✅ Resource pointer for comprehensive lists
- ✅ 2-3 lines per parameter (concise)

#### Tier 3: Resources (On-Demand Loading)
```markdown
# GTA Query Construction Guide

## MAST Chapters vs Intervention Types

**WHEN TO USE MAST CHAPTERS (Broad Categories):**
Use mast_chapters when you want comprehensive coverage of a policy category:
- "All subsidies" → mast_chapters=['L']
- "All import barriers" → mast_chapters=['E', 'F']
- "All trade defense measures" → mast_chapters=['D']

**WHEN TO USE INTERVENTION TYPES (Specific Measures):**
Use intervention_types when you need specific policy types:
- "Import tariffs only" → intervention_types=['Import tariff']
- "State aid only" → intervention_types=['State aid']
...
[Continues for 568 lines with exhaustive parameter documentation]
```

**Analysis:**
- ✅ Comprehensive decision frameworks
- ✅ Extensive examples for each parameter
- ✅ Only loaded when explicitly requested
- ✅ Cross-references to other resources
- ✅ Practical real-world guidance

### 3. Resource Organization Pattern

**File Structure:**
```
resources/
├── reference/                    # Lookup tables (static data)
│   └── mast_chapters.md
├── guides/                       # How-to documentation
│   ├── parameters.md
│   ├── query_examples.md
│   ├── query_syntax.md
│   └── exclusion_filters.md
└── [root level]                  # Core reference files
    ├── gta_jurisdictions.md
    ├── GTA intervention type descriptions.md
    ├── api_sector_list.md
    ├── cpc_vs_hs_guide.md
    └── date_fields_guide.md
```

**Resource Loader Implementation:**
```python
# resources_loader.py - Centralized resource management
_resource_cache: Dict[str, str] = {}

def load_resource(filename: str) -> str:
    """Load resource from markdown file with caching."""
    if filename not in _resource_cache:
        file_path = RESOURCES_DIR / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Resource file not found: {filename}")
        _resource_cache[filename] = file_path.read_text(encoding='utf-8')
    return _resource_cache[filename]
```

**Analysis:**
- ✅ Clear separation: `reference/` vs `guides/`
- ✅ Centralized loader with caching
- ✅ Consistent markdown format
- ✅ Reusable lookup functions
- ⚠️ Slight inconsistency: Some files in root, some in subdirectories

### 4. Resource URI Scheme

**Implemented URIs:**
- `gta://reference/*` - Reference lookup tables
- `gta://guide/*` - How-to guides
- `gta://jurisdiction/{code}` - Dynamic jurisdiction lookup
- `gta://intervention-type/{slug}` - Dynamic type lookup

**Analysis:**
- ✅ Clear semantic naming (`reference` vs `guide`)
- ✅ Supports dynamic parameters (`{iso_code}`, `{type_slug}`)
- ✅ Consistent `gta://` scheme
- ✅ Discoverable through MCP resources list

---

## Strengths (Best Practices Demonstrated)

### 1. ✅ Excellent Context Window Management

**Before (if all docs were in tools):** ~50KB loaded on every conversation
**After (current implementation):** ~5KB tool descriptions + resources on demand

**Impact:** 90% reduction in baseline context usage

### 2. ✅ Progressive Disclosure Architecture

The implementation creates a natural learning path:

1. **First contact:** User sees brief tool description with 2-3 examples
2. **Parameter exploration:** User reads 1-3 line parameter hints
3. **Deep dive:** User loads full resource when needed

**Example Journey:**
```
User needs to search subsidies
    ↓
Sees tool description: "Use mast_chapters=['L'] for subsidies"
    ↓
Wants to know what 'L' means
    ↓
Reads parameter: "See gta://reference/mast-chapters"
    ↓
Loads resource: Full MAST A-P taxonomy with decision guide
```

### 3. ✅ Rich, Actionable Documentation

Resources contain **decision frameworks**, not just reference data:

**Example from `gta://reference/mast-chapters`:**
```markdown
## L: Subsidies and Support Measures

**When to use this chapter:**
- You want ALL types of subsidies (grants, tax breaks, loans, state aid)
- You're researching government financial support broadly
- You don't need to distinguish between subsidy types

**When NOT to use (use intervention_types instead):**
- You need ONLY export subsidies (not domestic support)
- You're analyzing specific subsidy instruments (e.g., only tax breaks)
- You're conducting precise legal/regulatory analysis

**Common mistakes:**
❌ Using both mast_chapters=['L'] AND intervention_types=['State aid']
   → This is redundant; 'L' already includes state aid
✅ Use mast_chapters=['L'] for broad queries
✅ Use intervention_types=['State aid'] for precise targeting
```

This goes **beyond reference data** to teach users **when and how** to use features.

### 4. ✅ Extensive Real-World Examples

**Query Examples Resource** (`gta://guide/query-examples`) provides 35+ categorized examples:

```markdown
## Basic Filtering Examples

### Example 1: Country-to-Country Tariffs
**Use case:** Track bilateral tariff measures between two countries
**Query:**
```python
implementing_jurisdictions=['USA']
affected_jurisdictions=['CHN']
intervention_types=['Import tariff']
date_announced_gte='2024-01-01'
```
**What this finds:** All US tariffs imposed on Chinese products since Jan 2024
**When to use:** Trade war analysis, bilateral trade barriers
**Common variations:**
- Add `affected_products` to focus on specific sectors
- Use `date_announced_lte` to limit to specific period
```

**Impact:** Users can copy-paste-modify rather than construct from scratch

### 5. ✅ Smart Resource Granularity

The implementation provides **both summary and detail views**:

| Summary View | Detail View | Use Case |
|-------------|-------------|----------|
| `intervention-types-list` (7KB, 81 lines) | `intervention-types` (152KB, 2,232 lines) | Quick scan vs deep reference |
| Brief in-tool examples (2-3) | `query-examples` (686 lines, 35+ examples) | Getting started vs comprehensive library |
| Parameter hint (1 line) | `parameters` guide (568 lines) | Quick reminder vs full documentation |

**Progressive loading:** Users consume minimal info first, load heavy resources only when needed.

### 6. ✅ Dynamic Lookup Resources

Smart pattern for single-record lookups:

```python
@mcp.resource("gta://jurisdiction/{iso_code}")
async def get_jurisdiction(iso_code: str) -> str:
    """Look up details for a specific jurisdiction by ISO code."""
    full_table = load_jurisdictions_table()
    # Extract and format single jurisdiction entry
    for line in full_table.split('\n'):
        if f"| {iso_code.upper()} |" in line:
            return f"# Jurisdiction: {iso_code.upper()}\n\n{line}"
    return f"Jurisdiction code '{iso_code}' not found."
```

**Benefit:** Load single jurisdiction (50 bytes) instead of full table (18KB)

### 7. ✅ Consistent Documentation Format

All guides follow structured template:

```markdown
# [Topic Name]

## When to Use This
[Decision guidance]

## When NOT to Use This
[Anti-patterns]

## Examples
### Example 1: [Specific use case]
**Code:** [...]
**Explanation:** [...]
**Common mistakes:** [...]

## See Also
[Cross-references]
```

**Impact:** Predictable structure makes documentation easier to scan and use

---

## Gaps & Improvement Opportunities

Despite excellent overall implementation, several opportunities exist for incremental improvement:

### Gap 1: GTA Handbook Not Exposed 🟡 Medium Impact

**Current State:**
- `GTA Handbook.md` exists in resources directory (68KB, 605 lines, 8,812 words)
- Contains official methodology, database scope, taxonomy rationale
- **NOT exposed** via `@mcp.resource()` decorator
- Users cannot access this valuable context

**Example Content:**
```markdown
# The Global Trade Alert Database

## 1. Database Scope and Coverage

The GTA database tracks state acts that discriminate against commercial
interests located abroad. This includes:
- Import barriers (tariffs, quotas, licensing)
- Export incentives (subsidies, tax breaks)
- Government procurement restrictions
- Investment measures
...

## 2. What Qualifies as an Intervention

An intervention must meet three criteria:
1. Implemented by government agency or state-controlled entity
2. Discriminates in favor of or against commercial interests
3. Has cross-border implications
```

**Why This Matters:**
- Users asking "What types of policies does GTA track?" need this
- Understanding **methodology** helps construct better queries
- Clarifies **scope boundaries** (what's included/excluded)

**Impact Assessment:** 🟡 **Medium**
- **Frequency:** Occasional (new users, methodology questions)
- **Value:** High when needed (foundational understanding)
- **Effort:** Low (file exists, just needs exposure)

### Gap 2: Resource Organization Inconsistency 🟢 Low Impact

**Current State:**
- Some resources in subdirectories (`guides/`, `reference/`)
- Some resources at root level (`gta_jurisdictions.md`, `api_sector_list.md`)
- No clear pattern for which goes where

**Example:**
```
resources/
├── guides/
│   ├── parameters.md              ← In subdirectory
│   └── query_examples.md          ← In subdirectory
├── gta_jurisdictions.md           ← At root
├── api_sector_list.md             ← At root
└── date_fields_guide.md           ← At root (but it's a guide!)
```

**Recommendation:**
```
resources/
├── guides/
│   ├── parameters.md
│   ├── query_examples.md
│   ├── date_fields.md             ← Move here
│   ├── cpc_vs_hs.md               ← Move here
│   └── searching.md               ← Move here
├── reference/
│   ├── jurisdictions.md           ← Move here
│   ├── intervention_types.md      ← Move here
│   ├── sectors.md                 ← Move here
│   └── mast_chapters.md           ← Already here
└── methodology/
    └── handbook.md                ← New category
```

**Impact Assessment:** 🟢 **Low**
- **Frequency:** Developers only (users don't see file paths)
- **Value:** Improved maintainability
- **Effort:** Low (file moves + URI updates)

### Gap 3: No Quick-Start Prompt Template 🟡 Medium Impact

**Current State:**
- Resources provide comprehensive documentation
- Tools provide concise descriptions
- **Missing:** Guided workflow for first-time users

**Best Practices Recommendation (from reference doc):**
> Use MCP Prompts to create pre-configured query templates that users can select.

**What's Missing:**
```python
@mcp.prompt()
async def quick_start_guide() -> list:
    """Get started with GTA database - common queries and workflows."""
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": """# GTA Quick Start Guide

Let's explore common trade policy queries:

1. **Find recent tariffs:** Search import tariffs from a specific country
2. **Track subsidies:** Discover government support programs
3. **Analyze trade barriers:** Explore non-tariff measures
4. **Monitor specific companies:** Find policies affecting a firm

Which would you like to try? I'll construct the query for you."""
            }
        },
        {
            "role": "user",
            "content": {
                "type": "resource",
                "resource": {
                    "uri": "gta://guide/query-examples",
                    "mimeType": "text/markdown"
                }
            }
        }
    ]
```

**Impact Assessment:** 🟡 **Medium**
- **Frequency:** High (every new user)
- **Value:** Reduces learning curve significantly
- **Effort:** Medium (2-3 useful prompts needed)

### Gap 4: Missing Cross-Tool Workflow Guidance 🟢 Low Impact

**Current State:**
- Each tool documents itself well
- No guidance on **multi-tool workflows**

**Example Missing Workflow:**
```markdown
# Common Workflow: Deep Dive Analysis

## Step 1: Broad Search
Use `gta_search_interventions` to find relevant policies:
```python
mast_chapters=['L']
implementing_jurisdictions=['USA']
limit=50
```

## Step 2: Review Recent Activity
Use `gta_list_ticker_updates` to see what's new:
```python
jurisdiction_iso='USA'
limit=20
```

## Step 3: Get Full Details
For interesting interventions, use `gta_get_intervention`:
```python
intervention_id=12345
```

## Step 4: Analyze Supply Chain Impact
Use `gta_get_impact_chains` to trace effects:
```python
intervention_id=12345
```
```

**Impact Assessment:** 🟢 **Low**
- **Frequency:** Moderate (complex analysis tasks)
- **Value:** Moderate (helps advanced users)
- **Effort:** Low (new guide resource)

### Gap 5: Parameter Validation Messages Could Reference Resources 🔴 High Impact

**Current State:**
Parameter validation provides errors but doesn't guide users to documentation:

```python
# In models.py
class SearchInput(BaseModel):
    implementing_jurisdictions: Optional[List[str]] = Field(
        default=None,
        max_items=50  # ← What happens if exceeded?
    )
```

**Current Error (likely generic):**
```
ValidationError: implementing_jurisdictions: ensure this value has at most 50 items
```

**Better Error (educational):**
```python
from pydantic import field_validator

class SearchInput(BaseModel):
    implementing_jurisdictions: Optional[List[str]] = Field(default=None)

    @field_validator('implementing_jurisdictions')
    def validate_jurisdictions(cls, v):
        if v and len(v) > 50:
            raise ValueError(
                f"Too many jurisdictions ({len(v)}). Maximum is 50.\n\n"
                "TIP: For broad queries, try:\n"
                "- Use regional groupings (e.g., 'EU' instead of 27 countries)\n"
                "- Break query into multiple searches\n"
                "- See jurisdiction guide: gta://reference/jurisdictions"
            )
        return v
```

**Impact Assessment:** 🔴 **High**
- **Frequency:** High (users commonly make validation errors)
- **Value:** High (turns errors into learning moments)
- **Effort:** Medium (requires validator functions for each parameter)

### Gap 6: Resource Discovery Could Be Easier 🟡 Medium Impact

**Current State:**
- Resources listed in MCP protocol
- Users must call `resources/list` to discover
- No **categorized index** resource

**Proposed Addition:**
```python
@mcp.resource("gta://index")
async def get_resource_index() -> str:
    """Complete index of all GTA resources organized by category."""
    return """# GTA Resource Index

## 🚀 Getting Started
- `gta://guide/searching` - Search best practices and strategies
- `gta://guide/query-examples` - 35+ real-world query examples

## 📖 Reference Tables
- `gta://reference/jurisdictions` - Complete country codes (236 entries)
- `gta://reference/intervention-types` - All intervention types with examples
- `gta://reference/intervention-types-list` - Quick type list
- `gta://reference/sectors-list` - CPC sector classification
- `gta://reference/mast-chapters` - MAST A-P taxonomy

## 🎯 Parameter Guides
- `gta://guide/parameters` - Comprehensive parameter reference
- `gta://guide/query-syntax` - Query syntax and boolean logic
- `gta://guide/exclusion-filters` - Keep_* parameter patterns
- `gta://guide/date-fields` - Understanding date types

## 🔍 Decision Guides
- `gta://guide/cpc-vs-hs` - When to use CPC vs HS codes

## 🔧 Methodology
- `gta://methodology/handbook` - GTA database methodology

## 💡 Dynamic Lookups
- `gta://jurisdiction/{iso_code}` - Single jurisdiction details
- `gta://intervention-type/{type_slug}` - Single type details

---

**How to use:**
Copy a URI and request it to load that resource.
Example: "Show me gta://guide/query-examples"
"""
```

**Impact Assessment:** 🟡 **Medium**
- **Frequency:** High (every user needs to discover resources)
- **Value:** Medium (improves discoverability)
- **Effort:** Low (simple documentation resource)

---

## Prioritized Recommendations

### 🔴 HIGH IMPACT (Implement First)

#### Recommendation 1: Add Educational Validation Messages
**File:** `src/gta_mcp/models.py`
**Effort:** Medium (2-3 hours)
**Impact:** High - Every validation error becomes a learning opportunity

**Implementation:**

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class SearchInput(BaseModel):
    """Search parameters with educational validation."""

    implementing_jurisdictions: Optional[List[str]] = Field(
        default=None,
        description="List of implementing jurisdiction ISO codes. "
                   "See gta://reference/jurisdictions"
    )

    intervention_types: Optional[List[str]] = Field(
        default=None,
        description="List of specific intervention type names. "
                   "See gta://reference/intervention-types"
    )

    mast_chapters: Optional[List[str]] = Field(
        default=None,
        description="MAST chapter codes (A-P). "
                   "See gta://reference/mast-chapters"
    )

    query: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Text search query. "
                   "See gta://guide/query-syntax"
    )

    # Educational validators

    @field_validator('implementing_jurisdictions')
    def validate_jurisdictions_count(cls, v):
        """Limit jurisdiction count with helpful guidance."""
        if v and len(v) > 50:
            raise ValueError(
                f"Too many jurisdictions ({len(v)}). Maximum is 50 to prevent timeouts.\n\n"
                "💡 TIPS:\n"
                "- Use regional codes: 'EU' instead of listing 27 countries\n"
                "- Split into multiple targeted queries\n"
                "- See full list: gta://reference/jurisdictions"
            )
        return v

    @field_validator('intervention_types', 'mast_chapters')
    def validate_type_filters(cls, v, info):
        """Prevent redundant filter combinations."""
        # This validator runs for both fields; we need to check the combination
        # Note: field_validator doesn't have easy access to other fields during validation
        # This is a simplified example - full implementation needs model_validator
        return v

    @field_validator('query')
    def validate_query_complexity(cls, v):
        """Guide users toward better query construction."""
        if not v:
            return v

        word_count = len(v.split())

        if word_count > 20:
            raise ValueError(
                f"Query too complex ({word_count} words). The 'query' parameter works best "
                "with 1-5 keywords for entity names or concepts.\n\n"
                "💡 BETTER APPROACH:\n"
                "- Use structured filters (implementing_jurisdictions, intervention_types) "
                "for factual criteria\n"
                "- Use 'query' ONLY for:\n"
                "  • Company names (e.g., 'Tesla')\n"
                "  • Program names (e.g., 'Inflation Reduction Act')\n"
                "  • Technology terms (e.g., 'artificial intelligence')\n\n"
                "See examples: gta://guide/query-examples"
            )

        # Check for common mistakes
        if '&' in v or '|' in v:
            # User is using boolean operators - provide guidance
            return v  # Allow it but could add info message

        return v

    @model_validator(mode='after')
    def validate_filter_combinations(self):
        """Check for redundant or conflicting filter combinations."""

        # Check for redundant mast_chapters + intervention_types
        if self.mast_chapters and self.intervention_types:
            # Check if mast_chapters=['L'] + any subsidy intervention_types
            subsidy_types = {'State aid', 'Financial grant', 'Export subsidy',
                           'Tax or social insurance relief', 'In-kind grant'}
            if 'L' in self.mast_chapters and any(t in subsidy_types for t in self.intervention_types):
                raise ValueError(
                    "❌ REDUNDANT FILTERS: You specified mast_chapters=['L'] (all subsidies) "
                    "AND specific subsidy types in intervention_types.\n\n"
                    "💡 CHOOSE ONE APPROACH:\n"
                    "✅ Broad search: Use only mast_chapters=['L']\n"
                    "✅ Precise search: Use only intervention_types=['State aid', ...]\n\n"
                    "See guide: gta://reference/mast-chapters"
                )

        # Check for overly broad queries
        if (not self.implementing_jurisdictions and
            not self.affected_jurisdictions and
            not self.date_announced_gte and
            not self.intervention_types and
            not self.mast_chapters):

            raise ValueError(
                "❌ QUERY TOO BROAD: At least one filter is required to prevent timeouts.\n\n"
                "💡 ADD AT LEAST ONE OF:\n"
                "- implementing_jurisdictions (which countries?)\n"
                "- date_announced_gte (since when?)\n"
                "- intervention_types or mast_chapters (what policy types?)\n\n"
                "See examples: gta://guide/query-examples"
            )

        return self
```

**Testing:**
```python
# Test 1: Too many jurisdictions
try:
    SearchInput(implementing_jurisdictions=['USA'] * 51)
except ValueError as e:
    print(e)  # Should show helpful message

# Test 2: Redundant filters
try:
    SearchInput(
        mast_chapters=['L'],
        intervention_types=['State aid']
    )
except ValueError as e:
    print(e)  # Should explain redundancy

# Test 3: Too broad
try:
    SearchInput(query='subsidies')
except ValueError as e:
    print(e)  # Should require more specific filters
```

**Developer Notes:**
- Use `@field_validator` for single-field validation
- Use `@model_validator(mode='after')` for cross-field validation
- Include:
  - ❌ Clear statement of the problem
  - 💡 Actionable guidance
  - ✅ Specific examples of correct usage
  - 🔗 Resource URI for more info
- Test error messages in real LLM interactions to ensure clarity

---

### 🟡 MEDIUM IMPACT (Implement Second)

#### Recommendation 2: Expose GTA Handbook as Resource
**File:** `src/gta_mcp/server.py`
**Effort:** Low (30 minutes)
**Impact:** Medium - Valuable for methodology questions

**Implementation:**

```python
# In server.py, add new resource

@mcp.resource("gta://methodology/handbook")
async def get_gta_handbook() -> str:
    """
    Official GTA database methodology and scope documentation.

    Explains:
    - What types of policies GTA tracks
    - Inclusion/exclusion criteria
    - Data collection methodology
    - Taxonomy rationale
    - Quality assurance processes

    Use when:
    - Understanding GTA's scope and coverage
    - Answering "Does GTA track X?" questions
    - Learning about data quality and sources
    - Understanding the MAST classification system
    """
    return load_resource("GTA Handbook.md")
```

**Update Resource Index:**
```python
@mcp.resource("gta://index")
async def get_resource_index() -> str:
    """Complete index of all GTA resources."""
    return """# GTA Resource Index

## 🚀 Getting Started
...

## 🔬 Methodology & Background
- `gta://methodology/handbook` - **NEW** Official GTA methodology, scope, and taxonomy

...
"""
```

**Developer Notes:**
- File already exists at `resources/GTA Handbook.md`
- No changes to file needed, just expose it
- Consider whether to load full 68KB or create summary + detail views
- Alternative: Create `gta://methodology/handbook-summary` with key points only

---

#### Recommendation 3: Create Quick-Start Prompt Templates
**File:** `src/gta_mcp/server.py`
**Effort:** Medium (2-3 hours for 3-4 quality prompts)
**Impact:** Medium - Significantly improves new user experience

**Implementation:**

```python
# In server.py, add prompt templates

@mcp.prompt()
async def tariff_analysis(
    country: str = "USA",
    since_date: str = "2024-01-01"
) -> list:
    """
    Analyze tariff measures from a specific country.

    Args:
        country: Country ISO code (e.g., 'USA', 'CHN', 'DEU')
        since_date: Start date in YYYY-MM-DD format
    """
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""# Tariff Analysis: {country}

Analyze all tariff measures implemented by {country} since {since_date}.

## Step 1: Search for Tariffs
Use gta_search_interventions with:
```python
implementing_jurisdictions=['{country}']
intervention_types=['Import tariff']
date_announced_gte='{since_date}'
limit=100
```

## Step 2: Identify Patterns
From the results, summarize:
- Total number of tariff measures
- Top 5 affected countries (by measure count)
- Top 5 affected product categories (use HS codes)
- Temporal patterns (which months had most activity)

## Step 3: Highlight Notable Measures
Identify any unusual patterns:
- Retaliatory tariffs (matching dates with other countries)
- Sector-specific targeting
- Exceptionally high tariff rates

## Step 4: Deep Dive (if needed)
For significant measures, use gta_get_intervention to get full details
including implementation levels, exemptions, and current status.
"""
            }
        },
        {
            "role": "user",
            "content": {
                "type": "resource",
                "resource": {
                    "uri": "gta://guide/query-examples",
                    "mimeType": "text/markdown"
                }
            }
        }
    ]


@mcp.prompt()
async def subsidy_comparison(
    countries: str = "USA,CHN,EU",
    sector: str = "electric vehicles"
) -> list:
    """
    Compare subsidy measures across countries for a specific sector.

    Args:
        countries: Comma-separated country codes (e.g., 'USA,CHN,EU')
        sector: Sector name or keywords (e.g., 'electric vehicles', 'semiconductors')
    """
    country_list = [c.strip() for c in countries.split(',')]

    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""# Subsidy Comparison: {sector}

Compare {sector} subsidies across {', '.join(country_list)}.

## Step 1: Search Each Country
For each country ({', '.join(country_list)}), search:
```python
implementing_jurisdictions=['COUNTRY_CODE']
mast_chapters=['L']  # All subsidies
query='{sector}'
date_announced_gte='2022-01-01'  # Last 2-3 years
limit=50
```

## Step 2: Create Comparison Table
Build a table showing:

| Country | Total Subsidies | Common Types | Total Value (if available) | Key Programs |
|---------|----------------|--------------|----------------------------|--------------|
| ...     | ...            | ...          | ...                        | ...          |

## Step 3: Analyze Trends
Identify:
- Which country is most active in {sector} subsidies?
- Are there timing patterns (e.g., reactive policies)?
- Different subsidy instruments used (grants vs tax breaks vs loans)

## Step 4: Notable Programs
For the largest/most significant programs, use gta_get_intervention
to get full details on eligibility, amounts, and implementation.
"""
            }
        },
        {
            "role": "user",
            "content": {
                "type": "resource",
                "resource": {
                    "uri": "gta://reference/mast-chapters",
                    "mimeType": "text/markdown"
                }
            }
        }
    ]


@mcp.prompt()
async def company_impact_tracking(
    company_name: str = "Tesla",
    policy_types: str = "all"
) -> list:
    """
    Track government policies affecting a specific company.

    Args:
        company_name: Company name (e.g., 'Tesla', 'Huawei', 'BYD')
        policy_types: 'subsidies', 'tariffs', 'export_controls', or 'all'
    """

    # Map policy types to filters
    policy_filters = {
        'subsidies': "mast_chapters=['L']",
        'tariffs': "intervention_types=['Import tariff']",
        'export_controls': "intervention_types=['Export ban', 'Export licensing requirement']",
        'all': "# No specific filter - all intervention types"
    }

    filter_code = policy_filters.get(policy_types, policy_filters['all'])

    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""# Policy Impact Tracking: {company_name}

Track all government policies affecting {company_name}.

## Step 1: Find Mentions
Search interventions mentioning {company_name}:
```python
query='{company_name}'
{filter_code}
date_announced_gte='2020-01-01'
limit=100
```

## Step 2: Categorize Policies
Group results by:
- **Support measures** (subsidies, grants, tax breaks)
- **Restrictive measures** (tariffs, export controls, bans)
- **Neutral regulations** (standards, licensing)

## Step 3: Geographic Analysis
Which countries are:
- Supporting {company_name}? (implementing support measures)
- Restricting {company_name}? (implementing barriers)

## Step 4: Trend Analysis
Timeline showing:
- When did policy attention to {company_name} increase?
- Clusters of activity (e.g., multiple countries acting in same period)
- Evolution of policy types over time

## Step 5: Supply Chain Implications
For key measures, use gta_get_impact_chains to understand:
- Which products are affected
- Upstream/downstream industry effects
"""
            }
        }
    ]


@mcp.prompt()
async def trade_war_monitor(
    country_a: str = "USA",
    country_b: str = "CHN"
) -> list:
    """
    Monitor bilateral trade tensions between two countries.

    Args:
        country_a: First country ISO code (e.g., 'USA')
        country_b: Second country ISO code (e.g., 'CHN')
    """
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""# Bilateral Trade Tensions: {country_a} ↔ {country_b}

Analyze trade measures between {country_a} and {country_b}.

## Step 1: {country_a} Measures Affecting {country_b}
```python
implementing_jurisdictions=['{country_a}']
affected_jurisdictions=['{country_b}']
date_announced_gte='2018-01-01'
limit=100
```

## Step 2: {country_b} Measures Affecting {country_a}
```python
implementing_jurisdictions=['{country_b}']
affected_jurisdictions=['{country_a}']
date_announced_gte='2018-01-01'
limit=100
```

## Step 3: Timeline Analysis
Create timeline showing:
- Initial measures (who started?)
- Retaliatory measures (matching dates)
- Escalation patterns
- De-escalation attempts

## Step 4: Product Analysis
Which products are most targeted?
- Identify HS codes appearing most frequently
- Categorize by sector (agriculture, tech, manufacturing)
- Calculate cumulative trade value affected

## Step 5: Current Status
For recent measures:
- Use gta_list_ticker_updates to see latest developments
- Check implementation status (announced vs implemented vs removed)
- Identify any settlement negotiations or exemptions
"""
            }
        },
        {
            "role": "user",
            "content": {
                "type": "resource",
                "resource": {
                    "uri": "gta://guide/date-fields",
                    "mimeType": "text/markdown"
                }
            }
        }
    ]
```

**Developer Notes:**
- Each prompt should:
  - Provide **concrete starting parameters** (not placeholders)
  - Include **multi-step workflow** (not just single query)
  - Load **relevant resources** automatically
  - Explain **what to do with results** (analysis steps)
- Test prompts with actual LLM to ensure:
  - Instructions are clear and actionable
  - Examples work as shown
  - Loaded resources are actually useful
- Consider adding more specialized prompts:
  - `regulatory_compliance_check` - Track regulations for specific product
  - `investment_screening_monitor` - Monitor FDI restrictions
  - `sanctions_tracker` - Track sanctions by country/entity

---

#### Recommendation 4: Create Resource Discovery Index
**File:** `src/gta_mcp/server.py`
**Effort:** Low (1 hour)
**Impact:** Medium - Improves resource discoverability

**Implementation:**

```python
@mcp.resource("gta://index")
async def get_resource_index() -> str:
    """
    Complete index of all GTA resources organized by category.

    Use this to discover what documentation is available and when to use each resource.
    """
    return """# 📚 GTA Resource Index

## 🚀 Getting Started (New Users Start Here)

### Quick Start
- **`gta://guide/searching`** - Search strategies and best practices
  - When to use: First-time users, understanding search approach
  - Length: 155 lines, ~5 min read

### Learn by Example
- **`gta://guide/query-examples`** - 35+ real-world query examples
  - When to use: Learning query patterns, copy-paste-modify approach
  - Length: 686 lines, organized by use case
  - Examples: Tariff tracking, subsidy searches, company monitoring

---

## 📖 Reference Tables (Quick Lookups)

### Countries & Jurisdictions
- **`gta://reference/jurisdictions`** - Complete country/jurisdiction codes (236 entries)
  - When to use: Finding ISO codes, understanding regional groupings
  - Format: Table with ISO codes, names, UN codes

- **`gta://jurisdiction/{iso_code}`** - Single jurisdiction lookup
  - When to use: Quick check of one country code
  - Example: `gta://jurisdiction/USA`

### Intervention Types
- **`gta://reference/intervention-types-list`** - Quick list of all types (81 types)
  - When to use: Scanning available intervention types
  - Length: Brief, 7KB

- **`gta://reference/intervention-types`** - Complete type descriptions
  - When to use: Understanding what each intervention type covers
  - Length: Comprehensive, 152KB with examples for each type
  - Includes: Definitions, MAST classifications, real-world examples

- **`gta://intervention-type/{type_slug}`** - Single type lookup
  - When to use: Details on one specific intervention type
  - Example: `gta://intervention-type/import-tariff`

### Product Classifications
- **`gta://reference/sectors-list`** - CPC sector codes (333 codes)
  - When to use: Finding sector codes for queries
  - Format: Table with CPC codes and descriptions

- **`gta://guide/cpc-vs-hs`** - CPC vs HS code guide
  - When to use: Deciding which product classification to use
  - Explains: Differences, when to use each, conversion tips

### Policy Classifications
- **`gta://reference/mast-chapters`** - MAST taxonomy A-P
  - When to use: Understanding broad policy categories
  - Length: 421 lines with decision guidance
  - Includes: When to use mast_chapters vs intervention_types

### Other References
- **`gta://reference/eligible-firms`** - Eligible firm types
- **`gta://reference/implementation-levels`** - Government levels

---

## 🎯 Parameter & Query Guides (How-To)

### Comprehensive References
- **`gta://guide/parameters`** - Complete parameter documentation
  - When to use: Understanding all available filters
  - Length: 568 lines covering every parameter
  - Includes: Types, examples, common mistakes for each

### Query Construction
- **`gta://guide/query-syntax`** - Query syntax and boolean logic
  - When to use: Using the 'query' parameter effectively
  - Covers: OR (|), AND (&), exact phrases, wildcards
  - Includes: Strategy cascade for refining searches

### Specialized Parameters
- **`gta://guide/exclusion-filters`** - Keep_* parameter patterns
  - When to use: Advanced filtering (keeping/excluding specific types)
  - Length: 527 lines with examples
  - Covers: keep_implementation_level, keep_type, etc.

### Date Handling
- **`gta://guide/date-fields`** - Understanding date types
  - When to use: Confused about date_announced vs date_implemented vs date_removed
  - Length: 230 lines with timeline examples
  - Explains: Different date fields and their meanings

---

## 🔬 Methodology & Background

- **`gta://methodology/handbook`** - Official GTA methodology
  - When to use: Understanding database scope, inclusion criteria, data sources
  - Length: 605 lines, comprehensive
  - Covers: What GTA tracks, assessment methodology, taxonomy rationale

---

## 💡 Common Usage Patterns

### "I want to..."

#### Find policies affecting a specific country
→ Start with `gta://guide/query-examples` → "Jurisdiction Filters" section
→ Use: `affected_jurisdictions` parameter

#### Search for subsidies
→ Read `gta://reference/mast-chapters` → Chapter L
→ Use: `mast_chapters=['L']`
→ See examples: `gta://guide/query-examples` → "Subsidy Searches"

#### Track a specific company
→ See `gta://guide/query-examples` → "Entity and Program Name Searches"
→ Use: `query='CompanyName'` parameter

#### Understand all available filters
→ Read `gta://guide/parameters` (comprehensive reference)

#### Decide between CPC and HS codes
→ Read `gta://guide/cpc-vs-hs`

#### Find intervention type codes
→ Quick scan: `gta://reference/intervention-types-list`
→ Full details: `gta://reference/intervention-types`

---

## 📝 How to Use Resources

**In conversation:**
Simply mention the resource URI, and I'll load it for you.

**Examples:**
- "Show me gta://guide/query-examples"
- "Load the MAST chapters reference"
- "I need the jurisdiction codes"

**Pro tip:** Start with example-based resources (`query-examples`) before
diving into comprehensive references (`parameters`).

---

**Last updated:** 2025-11-09
**Total resources:** 16 (14 static + 2 dynamic lookups)
"""
```

**Developer Notes:**
- Organize by **user journey** (Getting Started → Reference → Advanced)
- Include "When to use" for each resource
- Provide **"I want to..."** section mapping goals to resources
- Update index when adding new resources
- Consider adding **estimated read time** for longer resources
- Link to related resources ("See also" sections)

---

### 🟢 LOW IMPACT (Nice to Have)

#### Recommendation 5: Reorganize Resource File Structure
**Files:** `resources/` directory
**Effort:** Low (1 hour)
**Impact:** Low - Improves maintainability for developers

**Current Structure:**
```
resources/
├── guides/
│   ├── parameters.md
│   ├── query_examples.md
│   ├── query_syntax.md
│   └── exclusion_filters.md
├── reference/
│   └── mast_chapters.md
├── gta_jurisdictions.md
├── GTA intervention type descriptions.md
├── GTA Handbook.md
├── api_sector_list.md
├── cpc_vs_hs_guide.md
├── date_fields_guide.md
├── searching_guide.md
├── eligible_firms.md
└── implementation_levels.md
```

**Proposed Structure:**
```
resources/
├── guides/                          # How-to documentation
│   ├── searching.md                 # Renamed from searching_guide.md
│   ├── parameters.md
│   ├── query_examples.md
│   ├── query_syntax.md
│   ├── exclusion_filters.md
│   ├── date_fields.md               # Moved from root
│   └── cpc_vs_hs.md                 # Moved from root
├── reference/                       # Lookup tables
│   ├── jurisdictions.md             # Renamed from gta_jurisdictions.md
│   ├── intervention_types.md        # Renamed from GTA intervention type descriptions.md
│   ├── intervention_types_list.md   # Generated from above
│   ├── sectors.md                   # Renamed from api_sector_list.md
│   ├── mast_chapters.md
│   ├── eligible_firms.md            # Moved from root
│   └── implementation_levels.md     # Moved from root
└── methodology/                     # Background & methodology
    └── handbook.md                  # Renamed from GTA Handbook.md
```

**Implementation Steps:**

1. **Create migration script:**
```python
# scripts/reorganize_resources.py
import shutil
from pathlib import Path

RESOURCES_DIR = Path("resources")

moves = [
    # Guides
    ("date_fields_guide.md", "guides/date_fields.md"),
    ("cpc_vs_hs_guide.md", "guides/cpc_vs_hs.md"),
    ("searching_guide.md", "guides/searching.md"),

    # Reference
    ("gta_jurisdictions.md", "reference/jurisdictions.md"),
    ("GTA intervention type descriptions.md", "reference/intervention_types.md"),
    ("api_sector_list.md", "reference/sectors.md"),
    ("eligible_firms.md", "reference/eligible_firms.md"),
    ("implementation_levels.md", "reference/implementation_levels.md"),

    # Methodology
    ("GTA Handbook.md", "methodology/handbook.md"),
]

# Create subdirectories
(RESOURCES_DIR / "methodology").mkdir(exist_ok=True)

# Move files
for old_path, new_path in moves:
    old = RESOURCES_DIR / old_path
    new = RESOURCES_DIR / new_path
    if old.exists():
        shutil.move(str(old), str(new))
        print(f"✓ Moved {old_path} → {new_path}")
    else:
        print(f"✗ Not found: {old_path}")
```

2. **Update `resources_loader.py`:**
```python
# Update file paths in load functions
def load_jurisdictions_table() -> str:
    return load_resource("reference/jurisdictions.md")  # Was: gta_jurisdictions.md

def load_intervention_types() -> str:
    return load_resource("reference/intervention_types.md")  # Was: GTA intervention type descriptions.md

def load_sectors_list() -> str:
    return load_resource("reference/sectors.md")  # Was: api_sector_list.md

# ... update all other load_* functions
```

3. **Update resource decorators in `server.py`:**
```python
# No changes needed to URIs (they're already clean)
# Just update load_resource() calls in implementation
```

4. **Update documentation:**
```markdown
# Update README.md or IMPLEMENTATION_SUMMARY.md
Resource files are now organized as:
- `guides/` - How-to documentation
- `reference/` - Lookup tables
- `methodology/` - Background information
```

**Benefits:**
- Clear semantic organization
- Easier to find files for editing
- Consistent naming (no "api_" or "GTA" prefixes)
- **No user-facing changes** (URIs stay the same)

**Risks:**
- Low risk (internal organization only)
- Ensure git history is preserved (`git mv` instead of manual moves)

---

#### Recommendation 6: Add Multi-Tool Workflow Guide
**File:** `resources/guides/workflows.md` (new)
**Effort:** Low (1-2 hours)
**Impact:** Low - Helps advanced users combine tools

**Implementation:**

```markdown
# GTA Multi-Tool Workflows

This guide shows how to combine GTA tools for comprehensive analysis.

---

## Workflow 1: Deep Intervention Analysis

**Goal:** Thoroughly analyze a specific policy measure and its impacts.

### Step 1: Find Interventions
Use `gta_search_interventions` to identify measures of interest:

```python
{
    "implementing_jurisdictions": ["USA"],
    "intervention_types": ["Import tariff"],
    "date_announced_gte": "2024-01-01",
    "limit": 50
}
```

**Output:** List of intervention IDs with brief summaries.

### Step 2: Get Full Details
For interesting interventions, use `gta_get_intervention`:

```python
{
    "intervention_id": 12345
}
```

**Output:** Complete intervention details including:
- Implementation dates and levels
- Affected products (HS codes, CPC codes)
- Affected jurisdictions
- Policy text and sources
- Current status

### Step 3: Analyze Supply Chain Impact
Use `gta_get_impact_chains` to understand broader effects:

```python
{
    "intervention_id": 12345,
    "direction": "both"  # upstream and downstream
}
```

**Output:** Map of affected industries and products through supply chains.

### Step 4: Monitor Updates
Use `gta_list_ticker_updates` to track changes:

```python
{
    "jurisdiction_iso": "USA",
    "limit": 20
}
```

**Output:** Recent modifications, implementations, or removals.

---

## Workflow 2: Comparative Country Analysis

**Goal:** Compare trade policy approaches across countries.

### Step 1: Baseline Search for Each Country
For each country, run identical search:

```python
{
    "implementing_jurisdictions": ["COUNTRY_CODE"],
    "mast_chapters": ["L"],  # Subsidies
    "date_announced_gte": "2023-01-01",
    "limit": 100
}
```

### Step 2: Aggregate Statistics
From search results, calculate:
- Total interventions per country
- Most common intervention types
- Average interventions per month
- Top affected sectors

### Step 3: Deep Dive on Outliers
For countries with unusual patterns, use `gta_get_intervention`
on their largest/most significant measures.

### Step 4: Cross-Reference Impact
Use `gta_get_impact_chains` on major interventions to:
- Identify which countries' policies affect same supply chains
- Find potential conflicts or coordination

---

## Workflow 3: Sector Monitoring

**Goal:** Track all policies affecting a specific sector over time.

### Step 1: Define Sector Scope
Use `gta://reference/sectors-list` to find relevant CPC codes.

Example (Electric Vehicles):
- CPC 49121: Passenger cars with electric motors
- CPC 49122: Goods transport vehicles with electric motors

### Step 2: Broad Search
```python
{
    "affected_products_cpc": ["49121", "49122"],
    "date_announced_gte": "2020-01-01",
    "limit": 200
}
```

### Step 3: Categorize by Policy Type
Group results by:
- Support measures (mast_chapters=['L'])
- Import barriers (intervention_types=['Import tariff', 'Import quota'])
- Export controls (mast_chapters=['P'])
- Standards/regulations (mast_chapters=['A', 'B'])

### Step 4: Timeline Analysis
Sort interventions by date to identify:
- Policy adoption waves
- Countries leading vs following
- Retaliatory patterns

### Step 5: Stay Updated
Set up regular checks with `gta_list_ticker_updates` filtered by sector.

---

## Workflow 4: Company-Specific Intelligence

**Goal:** Track government policies affecting a specific company.

### Step 1: Name-Based Search
```python
{
    "query": "Tesla",
    "date_announced_gte": "2020-01-01",
    "limit": 100
}
```

**Captures:** Policies explicitly mentioning the company.

### Step 2: Product-Based Search
Find company's product codes, then search:

```python
{
    "affected_products_hs": ["870380", "854140"],  # EVs and batteries
    "date_announced_gte": "2020-01-01",
    "limit": 200
}
```

**Captures:** Policies affecting company's products (even if not named).

### Step 3: Jurisdiction-Based Search
If company operates in specific countries:

```python
{
    "affected_jurisdictions": ["USA", "CHN", "DEU"],
    "intervention_types": ["Investment measure", "Localisation requirement"],
    "date_announced_gte": "2020-01-01"
}
```

**Captures:** Investment restrictions, local content requirements.

### Step 4: Consolidate and Deduplicate
Combine results from Steps 1-3, removing duplicates.

### Step 5: Impact Analysis
For major policies, use `gta_get_impact_chains` to understand:
- Supply chain disruptions
- Competitive effects (policies favoring competitors)

---

## Workflow 5: Trade Dispute Investigation

**Goal:** Analyze bilateral trade tensions.

### Step 1: Country A → Country B Measures
```python
{
    "implementing_jurisdictions": ["USA"],
    "affected_jurisdictions": ["CHN"],
    "date_announced_gte": "2018-01-01",
    "limit": 200
}
```

### Step 2: Country B → Country A Measures
```python
{
    "implementing_jurisdictions": ["CHN"],
    "affected_jurisdictions": ["USA"],
    "date_announced_gte": "2018-01-01",
    "limit": 200
}
```

### Step 3: Timeline Alignment
Sort both result sets by date to identify:
- Who initiated
- Retaliatory measures (matching announcement dates)
- Escalation vs de-escalation

### Step 4: Product Overlap Analysis
Identify products targeted by both sides:
- Extract HS codes from both result sets
- Find intersections (mutually targeted products)

### Step 5: Current Status Check
Use `gta_list_ticker_updates` for both countries to see:
- Recent removals (de-escalation signals)
- Recent additions (continued tensions)
- Implementation status changes

---

## Best Practices Across Workflows

### 1. Start Broad, Then Narrow
- Begin with minimal filters (e.g., just country + date range)
- Review results to understand patterns
- Add filters to focus on specific aspects

### 2. Use Appropriate Tools for Each Stage
- **Discovery:** `gta_search_interventions` (broad, pagination)
- **Detail:** `gta_get_intervention` (one intervention, full info)
- **Context:** `gta_get_impact_chains` (supply chain effects)
- **Monitoring:** `gta_list_ticker_updates` (recent changes)

### 3. Leverage Resources for Reference
While analyzing results, keep these resources handy:
- `gta://reference/intervention-types` - Understand policy types
- `gta://reference/mast-chapters` - Categorize broadly
- `gta://guide/date-fields` - Interpret dates correctly

### 4. Handle Pagination Wisely
- If search returns `total_count > limit`, you're seeing partial results
- Either increase `limit` or use `offset` for pagination
- For very large result sets, add filters rather than paginating

### 5. Cross-Check with Multiple Approaches
When critical, verify findings:
- Search by country AND by product (should overlap)
- Check both implementing and affected jurisdictions
- Use both `query` (text search) and structured filters

---

## Common Workflow Mistakes

### ❌ Mistake 1: Loading Too Much Detail Upfront
**Problem:** Calling `gta_get_intervention` on 100 IDs

**Better:**
1. Use `gta_search_interventions` to get summaries
2. Identify the 5-10 most relevant interventions
3. Get full details only for those

### ❌ Mistake 2: Not Tracking Temporal Changes
**Problem:** One-time search misses policy updates

**Better:**
1. Initial search with `gta_search_interventions`
2. Periodic checks with `gta_list_ticker_updates`
3. Re-run search for status changes (implemented, removed)

### ❌ Mistake 3: Ignoring Supply Chain Effects
**Problem:** Only analyzing direct impacts

**Better:**
1. Identify key interventions
2. Use `gta_get_impact_chains` to see ripple effects
3. Search for related products/sectors

---

## Tool Selection Matrix

| If you want to... | Use this tool | With these parameters |
|------------------|---------------|----------------------|
| Find policies matching criteria | `gta_search_interventions` | Filters for country, type, product, date |
| Get complete details on one policy | `gta_get_intervention` | `intervention_id` from search results |
| See supply chain effects | `gta_get_impact_chains` | `intervention_id` + `direction` |
| Monitor recent changes | `gta_list_ticker_updates` | `jurisdiction_iso` or `intervention_type` |
| Browse latest additions | `gta_list_ticker_updates` | No filters (shows all recent) |

---

**Next Steps:**
- Pick a workflow matching your use case
- Load relevant resources for parameter reference
- Start with Step 1 and iterate based on findings
```

**Add to server.py:**
```python
@mcp.resource("gta://guide/workflows")
async def get_workflows_guide() -> str:
    """
    Multi-tool workflow patterns for comprehensive analysis.

    Shows how to combine gta_search_interventions, gta_get_intervention,
    gta_get_impact_chains, and gta_list_ticker_updates for:
    - Deep intervention analysis
    - Comparative country studies
    - Sector monitoring
    - Company-specific intelligence
    - Trade dispute investigation
    """
    return load_resource("guides/workflows.md")
```

**Developer Notes:**
- Focus on **real-world analysis patterns**
- Include **what not to do** (common mistakes)
- Provide **tool selection matrix** for quick reference
- Update when new tools are added
- Consider adding **estimated time** for each workflow

---

## Implementation Roadmap

### Phase 1: Quick Wins (Week 1)
**Effort:** ~4 hours
**Impact:** Medium-High

1. ✅ **Expose GTA Handbook** (30 min)
   - Add `@mcp.resource("gta://methodology/handbook")`
   - Test loading

2. ✅ **Create Resource Index** (1 hour)
   - Implement `gta://index` resource
   - Organize by user journey
   - Add "I want to..." section

3. ✅ **Add Educational Validation** (2.5 hours)
   - Implement field validators for common errors
   - Add model validator for filter combinations
   - Test error messages with LLM

### Phase 2: Enhanced Discoverability (Week 2)
**Effort:** ~5 hours
**Impact:** Medium

4. ✅ **Create Quick-Start Prompts** (3 hours)
   - Implement 4 prompt templates:
     - `tariff_analysis`
     - `subsidy_comparison`
     - `company_impact_tracking`
     - `trade_war_monitor`
   - Test each prompt end-to-end

5. ✅ **Add Workflows Guide** (2 hours)
   - Create `guides/workflows.md`
   - Document 5 common multi-tool workflows
   - Add to resources

### Phase 3: Polish & Consistency (Week 3 - Optional)
**Effort:** ~2 hours
**Impact:** Low

6. ✅ **Reorganize File Structure** (1 hour)
   - Move files to subdirectories
   - Update loader paths
   - Test all resources still load

7. ✅ **Final Testing** (1 hour)
   - Test all resources load correctly
   - Verify URIs work
   - Check cross-references
   - Validate with LLM user experience

---

## Success Metrics

Track these metrics to measure Layer 2 effectiveness:

### 1. Context Efficiency
**Metric:** Average context tokens loaded per conversation

**How to measure:**
- Baseline: Tool descriptions only (~3,000 tokens)
- Compare: Add resource loads for typical queries
- **Target:** < 10,000 tokens per conversation on average

**Good sign:** Most conversations use 0-2 resources, not loading all documentation

### 2. Resource Utilization
**Metric:** Which resources are loaded most frequently

**How to measure:**
- Add logging to `load_resource()` function
- Track resource URI access counts
- Analyze top 5 most-accessed resources

**Expected pattern:**
- `query-examples` - High (users learn by example)
- `jurisdictions` - Medium (occasional lookups)
- `intervention-types` (full) - Low (only for deep dives)

**Red flag:** If full intervention-types loaded every conversation → create better summary

### 3. Error Rate Improvement
**Metric:** Validation errors before/after educational messages

**How to measure:**
- Track validation error frequency (before Rec #1)
- Track after implementing educational validators
- **Target:** 30% reduction in repeat errors

**Good sign:** Users self-correct based on error guidance

### 4. Prompt Adoption
**Metric:** Usage of prompt templates

**How to measure:**
- Track prompt invocations via MCP logs
- Survey users on usefulness
- **Target:** 40% of new users try at least one prompt

**Good sign:** Prompts reduce back-and-forth questions

### 5. Documentation Discoverability
**Metric:** Resource index access rate

**How to measure:**
- Track `gta://index` loads
- Monitor if users find resources without asking
- **Target:** Index accessed in 20% of new user sessions

**Good sign:** Users proactively explore resources

---

## Maintenance Guidelines

### When to Create New Resources

**✅ Create a resource when:**
- Content is > 500 words or > 50 lines
- Content is reference data (tables, code lists)
- Content is needed occasionally, not always
- Content is comprehensive documentation of a single topic

**❌ Don't create a resource when:**
- Content is < 10 lines (keep in tool/parameter description)
- Content is critical warnings (keep in tool docstring)
- Content is simple examples (2-3 in tool docstring is fine)

### Updating Existing Resources

**When content changes:**
1. Update markdown file in `resources/` directory
2. Clear resource cache (if using caching)
3. Test resource still loads via MCP
4. Update "Last updated" date in resource
5. If structure changes significantly, update index

**Version control:**
- Use git commit messages to track documentation changes
- Consider adding changelog to large resources

### Adding New Resources Checklist

When adding a new resource:

- [ ] Create markdown file in appropriate subdirectory
- [ ] Add `@mcp.resource()` decorator in `server.py`
- [ ] Write clear resource description (purpose, when to use)
- [ ] Add to resource index (`gta://index`)
- [ ] Cross-reference from related resources
- [ ] Update tool/parameter descriptions with URI reference
- [ ] Test loading via MCP protocol
- [ ] Test with LLM in real conversation
- [ ] Add to this assessment document

---

## Appendix: Technical Reference

### Resource Loader Architecture

**Current implementation:**
```python
# resources_loader.py
from pathlib import Path
from typing import Dict

RESOURCES_DIR = Path(__file__).parent / "resources"
_resource_cache: Dict[str, str] = {}

def load_resource(filename: str) -> str:
    """Load resource with caching."""
    if filename not in _resource_cache:
        file_path = RESOURCES_DIR / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Resource file not found: {filename}")
        _resource_cache[filename] = file_path.read_text(encoding='utf-8')
    return _resource_cache[filename]
```

**Performance considerations:**
- **Caching:** Resources loaded once per server session
- **Memory usage:** ~305KB total cached (acceptable)
- **Lazy loading:** MCP only loads when explicitly requested
- **No pre-processing:** Markdown served as-is (simple, fast)

**Future optimizations (if needed):**
- Add cache invalidation for development mode
- Implement resource compression for very large files
- Add cache warming for most-accessed resources
- Monitor memory usage as resource count grows

### MCP Protocol Details

**Resource requests flow:**
1. Client calls `resources/list` → sees all resource URIs
2. Client calls `resources/read` with URI → server loads file
3. Server returns resource content + metadata
4. Client (LLM) processes content in context

**Dynamic resources:**
```python
@mcp.resource("gta://jurisdiction/{iso_code}")
async def get_jurisdiction(iso_code: str) -> str:
    # URI pattern matching handled by FastMCP
    # {iso_code} captured as parameter
    full_table = load_jurisdictions_table()
    # Extract relevant section
    return formatted_section
```

**Resource metadata:**
```python
@mcp.resource(
    "gta://guide/parameters",
    name="Parameter Reference",
    description="Comprehensive documentation of all search parameters",
    mime_type="text/markdown"
)
```

---

## Conclusion

The GTA MCP server demonstrates **exemplary Layer 2 implementation** with:

✅ **Excellent separation** of concerns (concise tools + comprehensive resources)
✅ **Progressive disclosure** architecture (tool → parameter → resource)
✅ **Rich documentation** (~46,000 words) properly organized
✅ **Smart resource design** (summary + detail views, dynamic lookups)
✅ **Strong patterns** worth replicating in other MCP servers

**Recommendations focus on incremental improvements:**

🔴 **High Impact:**
1. Educational validation messages (turn errors into learning)

🟡 **Medium Impact:**
2. Expose GTA Handbook (methodology documentation)
3. Quick-start prompt templates (guided workflows)
4. Resource discovery index (improve navigation)

🟢 **Low Impact (polish):**
5. File structure reorganization (developer experience)
6. Multi-tool workflow guide (advanced users)

**Overall Assessment:** This server serves as an **excellent reference implementation** for Layer 2 best practices. The recommendations above enhance an already strong foundation rather than addressing fundamental gaps.

---

**Document Version:** 1.0
**Next Review:** After implementing Phase 1 recommendations
**Feedback:** Update this document based on real-world usage patterns