# MCP Server Best Practices: Complex Database Query Interfaces

## The Core Problem

You have a complex database requiring extensive explanation to construct correct queries. Challenge: help the LLM query accurately without drowning it in documentation every time it loads your tools.

**Your current approach (embedding everything in tool descriptions) causes:**
- Context window bloat from documentation loading on every conversation
- Poor signal-to-noise ratio when LLM scans available tools
- Difficulty maintaining documentation (scattered across tool descriptions)
- No way to progressively disclose complexity

---

## Solution Architecture: Three-Layer Approach

### Layer 1: Minimal Tool Descriptions (Always in Context)

**Rule:** Tool descriptions should be < 200 words and focus on *what* and *when*, not *how*.

**Good:**
```python
@mcp.tool()
async def gta_search_interventions(params: SearchInput) -> str:
    """Search trade policy interventions with flexible filtering.
    
    Use for: Finding tariffs, subsidies, export controls, and other 
    government trade measures. Supports filtering by country, product, 
    date, and intervention type.
    
    Returns: Intervention summaries with pagination. For full details 
    on specific interventions, use gta_get_intervention.
    
    Start broad (fewer filters), then narrow based on results. Complex 
    filter syntax documented in 'gta://docs/query-guide' resource.
    """
```

**Bad (your current approach):**
```python
@mcp.tool()
async def gta_search_interventions(params: SearchInput) -> str:
    """Search trade policy interventions.
    
    CRITICAL QUERY GUIDELINES:
    - Use mast_chapters for BROAD queries (e.g., 'all subsidies')
    - Use intervention_types for SPECIFIC queries (e.g., 'Import tariff')
    - MAST chapters: A (SPS), B (TBT), C (Pre-shipment), D (Trade defense),
      E (Licensing), F (Price controls), G (Finance), H (Competition), 
      I (Investment), J (Distribution), K (Post-sales), L (Subsidies - 
      USE THIS FOR ANY SUBSIDY QUERY), M (Procurement), N (IP), O (Origin),
      P (Export measures)
    - When searching subsidies, ALWAYS use mast_chapters=['L'] not 
      intervention_types unless you need SPECIFIC subsidy types
    - For Tesla subsidies: query='Tesla', mast_chapters=['L']
    - For export controls on AI: query='artificial intelligence | AI',
      intervention_types=['Export ban', 'Export licensing']
    - Query syntax supports OR (|), AND (&), exact phrases ("..."), 
      wildcards (#)
    
    [... continues for 500 more words ...]
    """
```

---

### Layer 2: Resources for Documentation (Load on Demand)

**Move comprehensive documentation to MCP Resources.** Resources are separate from tools and only load when explicitly referenced.

#### Implementation Pattern (Python):

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gta_mcp")

@mcp.resource("gta://docs/query-guide")
async def get_query_guide() -> str:
    """Comprehensive guide to constructing GTA search queries."""
    return """
# GTA Query Construction Guide

## MAST Chapters vs Intervention Types

**WHEN TO USE MAST CHAPTERS (Broad Categories):**
Use mast_chapters when you want comprehensive coverage:
- "All subsidies" → mast_chapters=['L']
- "All import barriers" → mast_chapters=['E', 'F']
- "All trade defense measures" → mast_chapters=['D']

**WHEN TO USE INTERVENTION TYPES (Specific Measures):**
Use intervention_types when you need specific policy types:
- "Import tariffs only" → intervention_types=['Import tariff']
- "State aid only" → intervention_types=['State aid']
- "Export bans only" → intervention_types=['Export ban']

## MAST Chapter Reference

**L: Subsidies and Support (USE FOR ALL SUBSIDY QUERIES)**
Covers: Export subsidies, domestic support, state aid, grants, tax breaks, 
loan guarantees, capital injections, equity purchases

Examples:
- "Tesla subsidies" → query='Tesla', mast_chapters=['L']
- "EU green subsidies" → implementing_jurisdictions=['EU'], 
  mast_chapters=['L'], query='green | renewable | clean energy'

**D: Trade Defense Measures**
Covers: Anti-dumping, countervailing duties, safeguards

[... continues with full documentation ...]

## Query Syntax

### OR Logic (|)
Match any term: 'Tesla | BYD | Volkswagen'

### AND Logic (&)
Require both: 'electric vehicle & subsidy'

[... full syntax documentation ...]
    """

@mcp.resource("gta://docs/jurisdiction-codes")
async def get_jurisdiction_codes() -> str:
    """ISO country codes and jurisdiction identifiers."""
    return """
# GTA Jurisdiction Codes

## Major Jurisdictions
- USA: United States
- CHN: China
- EU: European Union (supranational)
- DEU: Germany
- FRA: France
- GBR: United Kingdom
- JPN: Japan

[... complete reference ...]
    """

@mcp.resource("gta://docs/product-codes")
async def get_product_codes() -> str:
    """HS 6-digit product codes with descriptions."""
    return """
# Harmonized System Product Codes

Use 6-digit codes for product filtering.

## Common Products
- 870310: Motor vehicles with spark-ignition engine (< 1000cc)
- 870380: Motor vehicles with spark-ignition engine (> 1500cc)
- 854140: Photosensitive semiconductor devices (solar cells)
- 292149: Aniline derivatives (pharmaceutical intermediates)

[... extensive product reference ...]
    """
```

**How this works:**
- Resources don't load unless explicitly requested
- LLM can discover available resources via `resources/list`
- LLM requests specific resource when needed: `resources/read gta://docs/query-guide`
- You can update documentation without changing tool code

**When LLM needs help:**
1. Sees brief tool description: "Complex filter syntax in 'gta://docs/query-guide'"
2. Calls `resources/read` with URI `gta://docs/query-guide`
3. Gets full documentation in context for that query only
4. Documentation drops from context after query completes

---

### Layer 3: Prompts for Guided Workflows (User-Invoked)

**Use MCP Prompts to create pre-configured query templates** that users can select.

#### Implementation Pattern (Python):

```python
@mcp.prompt()
async def tariff_analysis(
    country: str,
    timeframe: str = "2024-01-01"
) -> list:
    """Analyze tariff measures from a specific country.
    
    Args:
        country: Country code (e.g., 'USA', 'CHN')
        timeframe: Start date (YYYY-MM-DD)
    """
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Analyze all tariff measures implemented by {country} since {timeframe}.

Steps:
1. Search for tariffs: implementing_jurisdictions=['{country}'], 
   intervention_types=['Import tariff'], 
   date_announced_gte='{timeframe}'
   
2. Identify affected products and countries

3. Summarize by:
   - Total number of measures
   - Top 5 affected products (by measure count)
   - Top 5 affected countries
   - Temporal patterns (which months had most activity)

4. For any unusual patterns, fetch full intervention details
"""
            }
        },
        {
            "role": "user",
            "content": {
                "type": "resource",
                "resource": {
                    "uri": "gta://docs/query-guide",
                    "mimeType": "text/markdown"
                }
            }
        }
    ]

@mcp.prompt()
async def subsidy_comparison(
    countries: str,
    sector: str
) -> list:
    """Compare subsidy measures across countries for a specific sector.
    
    Args:
        countries: Comma-separated country codes (e.g., 'USA,CHN,EU')
        sector: Sector name or keywords
    """
    country_list = [c.strip() for c in countries.split(',')]
    
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Compare {sector} subsidies across {', '.join(country_list)}.

For each country, search:
- implementing_jurisdictions=[country_code]
- mast_chapters=['L']  # All subsidies
- query='{sector}'
- Limit to last 2 years

Then create comparison table showing:
- Total subsidy count
- Most common subsidy types
- Recent trends
- Key programs/initiatives
"""
            }
        }
    ]
```

**How this works:**
- Users see prompts as templates: "Tariff Analysis", "Subsidy Comparison"
- Selecting a prompt injects pre-configured instructions + relevant resources
- LLM follows structured workflow with correct query patterns
- Reduces need for user to understand query complexity

---

## Specific Implementation Strategies

### Strategy 1: Query Builder Tools (Progressive Complexity)

Instead of one complex tool, offer simple → advanced progression:

```python
@mcp.tool()
async def gta_simple_search(
    country: str,
    keywords: str,
    policy_type: Literal["tariffs", "subsidies", "export_controls", "all"] = "all"
) -> str:
    """Simple search for common queries. No complex filters needed.
    
    Just provide country, keywords, and general policy type.
    The tool handles filter translation automatically.
    """
    # Translate simple inputs to complex API parameters
    type_mapping = {
        "tariffs": {"intervention_types": ["Import tariff"]},
        "subsidies": {"mast_chapters": ["L"]},
        "export_controls": {"intervention_types": ["Export ban", "Export licensing requirement"]},
        "all": {}
    }
    
    params = {
        "implementing_jurisdictions": [country],
        "query": keywords,
        **type_mapping[policy_type]
    }
    
    return await _execute_search(params)

@mcp.tool()
async def gta_advanced_search(params: AdvancedSearchInput) -> str:
    """Advanced search with full filter control.
    
    For complex queries requiring precise filter combinations.
    See 'gta://docs/query-guide' resource for comprehensive documentation.
    
    Most users should start with gta_simple_search.
    """
    return await _execute_search(params.model_dump())
```

---

### Strategy 2: Smart Defaults + Constraints

Reduce decision space through intelligent defaults and schema constraints:

```python
from enum import Enum
from pydantic import BaseModel, Field

class PolicyScope(str, Enum):
    """Pre-defined common query patterns."""
    ALL_SUBSIDIES = "all_subsidies"  # Auto-sets mast_chapters=['L']
    ALL_TARIFFS = "all_tariffs"      # Auto-sets intervention_types=['Import tariff']
    TRADE_DEFENSE = "trade_defense"  # Auto-sets mast_chapters=['D']
    CUSTOM = "custom"                # User defines filters manually

class SearchInput(BaseModel):
    scope: PolicyScope = Field(
        default=PolicyScope.CUSTOM,
        description="Common query patterns. Use CUSTOM for manual filter control."
    )
    
    implementing_jurisdictions: list[str] = Field(
        default_factory=list,
        description="Country codes (e.g., ['USA', 'CHN'])",
        max_items=10
    )
    
    date_announced_gte: str = Field(
        default="2020-01-01",
        description="Start date (YYYY-MM-DD). Defaults to 2020.",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    
    limit: int = Field(
        default=20,
        description="Results per page",
        ge=1,
        le=100
    )
    
    # Only show complex filters when scope=CUSTOM
    mast_chapters: list[str] | None = Field(
        default=None,
        description="Only used when scope='custom'. See gta://docs/query-guide"
    )
    
    intervention_types: list[str] | None = Field(
        default=None,
        description="Only used when scope='custom'. See gta://docs/query-guide"
    )
```

---

### Strategy 3: Validation That Teaches

Use error messages as learning opportunities:

```python
async def validate_search_params(params: dict) -> None:
    """Validate parameters and provide actionable guidance."""
    
    # Detect common mistakes
    if params.get("mast_chapters") and params.get("intervention_types"):
        if "L" in params["mast_chapters"] and any(
            t in ["State aid", "Financial grant", "Export subsidy"] 
            for t in params["intervention_types"]
        ):
            raise ValueError(
                "Redundant filters detected. You specified mast_chapters=['L'] "
                "(all subsidies) AND specific subsidy types in intervention_types. "
                "\n\nRECOMMENDATION: Remove intervention_types to get broader "
                "coverage, OR remove mast_chapters to get only specific types."
            )
    
    # Guide toward better queries
    if params.get("query") and len(params.get("query", "").split()) > 10:
        raise ValueError(
            "Query too complex. The 'query' parameter searches text fields and "
            "works best with 1-5 keywords.\n\n"
            "TRY: Use structured filters (implementing_jurisdictions, "
            "intervention_types) for factual criteria, and 'query' only for "
            "entity names or concepts."
        )
    
    # Prevent performance issues
    if (not params.get("implementing_jurisdictions") and 
        not params.get("affected_jurisdictions") and
        not params.get("date_announced_gte")):
        raise ValueError(
            "Query too broad. At least one of these is required:\n"
            "- implementing_jurisdictions (which countries)\n"
            "- affected_jurisdictions (impacted countries)\n"
            "- date_announced_gte (time window)\n\n"
            "This prevents timeouts from searching entire database."
        )
```

---

### Strategy 4: Examples in Schema Descriptions

Show patterns directly in field descriptions:

```python
class SearchInput(BaseModel):
    query: str | None = Field(
        default=None,
        description="""Entity/product names for text search (optional).
        
Examples:
- 'Tesla' - Find measures mentioning Tesla
- 'electric vehicle | EV' - Match either phrase
- '5G & Huawei' - Must mention both
- 'artificial intelligence | AI | machine learning' - Multiple alternatives

Keep queries short (1-5 words). Use structured filters for factual criteria.""",
        max_length=200
    )
    
    implementing_jurisdictions: list[str] = Field(
        default_factory=list,
        description="""Countries implementing the measure (ISO codes).

Examples:
- ['USA'] - US measures only
- ['USA', 'CHN'] - US or China measures
- ['EU'] - EU-level measures (supranational)
- ['DEU', 'FRA'] - Germany or France (national)

See 'gta://docs/jurisdiction-codes' for full list.""",
        max_items=20
    )
```

---

## Implementation Checklist

### Phase 1: Restructure Documentation
- [ ] Identify documentation currently in tool descriptions
- [ ] Split into: (1) brief tool summaries, (2) detailed resources
- [ ] Create resource URIs: `{service}://docs/{topic}`
- [ ] Implement resource handlers with `@mcp.resource()`
- [ ] Update tool descriptions to reference resources

### Phase 2: Add Guided Workflows
- [ ] Identify 5-10 most common query patterns
- [ ] Create prompt templates with `@mcp.prompt()`
- [ ] Include pre-configured filters and instructions
- [ ] Test prompts with real user scenarios
- [ ] Document available prompts

### Phase 3: Optimize Tool Design
- [ ] Create simple/advanced tool variants if beneficial
- [ ] Add smart defaults to reduce required parameters
- [ ] Implement enum-based query patterns (if applicable)
- [ ] Add validation with educational error messages
- [ ] Put examples directly in schema descriptions

### Phase 4: Verify Context Efficiency
- [ ] Measure tool description lengths (target: <200 words each)
- [ ] Verify resources only load on explicit request
- [ ] Test that prompts inject correct documentation
- [ ] Confirm LLM can discover and use resources
- [ ] Profile context usage in real scenarios

---

## Context Budget Analysis

**Before (everything in tool descriptions):**
```
Tool load: 15 tools × 800 words avg = 12,000 words = ~16,000 tokens
Every conversation: 16,000 tokens of documentation
User query space: Remaining context - 16k tokens
```

**After (three-layer approach):**
```
Tool load: 15 tools × 150 words avg = 2,250 words = ~3,000 tokens
Resource (on demand): Loaded only when needed = ~5,000 tokens
Prompt (user-invoked): Template + targeted resource = ~6,000 tokens

Standard conversation: 3,000 tokens (13k saved)
Complex query needing help: 8,000 tokens (8k saved)
Guided workflow: 9,000 tokens (7k saved)
```

**Savings: 54-81% reduction in documentation overhead**

---

## Technical Implementation Notes

### Python FastMCP Resources

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("service_mcp")

# Simple text resource
@mcp.resource("service://docs/guide")
async def get_guide() -> str:
    return "Documentation content here"

# Resource with metadata
@mcp.resource(
    "service://docs/reference",
    name="API Reference",
    description="Complete API documentation",
    mime_type="text/markdown"
)
async def get_reference() -> str:
    return "# API Reference\n\n..."

# Dynamic resource (with parameters)
@mcp.resource("service://docs/{topic}")
async def get_doc(topic: str) -> str:
    docs = {
        "filters": "Filter documentation...",
        "syntax": "Query syntax...",
    }
    return docs.get(topic, "Topic not found")
```

### Python FastMCP Prompts

```python
# Simple prompt
@mcp.prompt()
async def analyze_trend(keyword: str) -> list:
    """Analyze trends for a keyword."""
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"Analyze trends for: {keyword}"
            }
        }
    ]

# Prompt with embedded resources
@mcp.prompt()
async def complex_analysis() -> list:
    """Complex analysis with documentation."""
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": "Perform analysis..."
            }
        },
        {
            "role": "user",
            "content": {
                "type": "resource",
                "resource": {
                    "uri": "service://docs/guide",
                    "mimeType": "text/markdown"
                }
            }
        }
    ]
```

---

## Key Principles

1. **Lazy Loading**: Documentation loads only when needed
2. **Progressive Disclosure**: Simple → Advanced complexity path
3. **Examples Over Prose**: Show patterns in descriptions
4. **Validation as Education**: Errors guide correct usage
5. **Smart Defaults**: Reduce decision space
6. **Separation of Concerns**: Tools (what), Resources (how), Prompts (workflows)

---

## Resources

- **MCP Prompts Specification**: https://modelcontextprotocol.io/specification/2025-06-18/server/prompts
- **MCP Resources Specification**: https://modelcontextprotocol.io/specification/2025-06-18/server/resources
- **Python FastMCP Documentation**: https://github.com/modelcontextprotocol/python-sdk
