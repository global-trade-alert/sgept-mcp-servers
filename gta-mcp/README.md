# GTA MCP Server

Model Context Protocol server providing access to the Global Trade Alert (GTA) database. This server exposes trade policy interventions, enabling LLMs to search and analyze government trade measures worldwide.

## Version

**Current Version:** 0.3.0 (November 9, 2025)

⚠️ **Experimental Release** - This server is under active development. Feedback and feature requests welcome.

See [Version History & Changelog](#version-history--changelog) below for details.

## Overview

**Purpose:** This MCP server translates natural language queries into precise API requests for the Global Trade Alert database, enabling flexible interrogation of 75,000+ trade policy interventions worldwide. It handles the complex task of identifying and retrieving relevant intervention records with their complete GTA information.

**How It Works:**
1. The server converts your natural language request into optimized API calls with appropriate filters
2. It retrieves relevant intervention IDs and their complete information from GTA (including full descriptions and sources if your API key permits)
3. The LLM receives this raw data for analysis and interpretation

**Important:** The MCP server's role ends at data retrieval. How the LLM interprets, summarizes, and analyzes the returned interventions depends entirely on your prompts (client-side instructions).

**Best Practice for Detailed Queries:** For questions requiring careful analysis, explicitly instruct your LLM to examine the returned intervention set thoroughly and methodically. Think of it as giving instructions to a lawyerly specific about what aspects to analyze, what to compare, and what conclusions to draw.

**Status:** Ongoing development to continuously improve query precision and result optimization. Send feedback or requests to Johannes Fritz.

## Installation

### Prerequisites
- Python 3.10 or higher
- `uv` package manager ([install here](https://github.com/astral-sh/uv))
- GTA API key from SGEPT

### Setup

```bash
# Clone or navigate to the project directory
cd gta_mcp

# Install dependencies with uv
uv sync

# Set your API key
export GTA_API_KEY='your-api-key-here'

# Test the installation
uv run gta-mcp --help
```

## Configuration

### Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "gta": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/gta_mcp",
        "run",
        "gta-mcp"
      ],
      "env": {
        "GTA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Other MCP Clients

For clients supporting stdio transport, run:

```bash
uv run gta-mcp
```

## Available Tools

### 1. `gta_search_interventions`
Search and filter trade interventions with comprehensive parameters.

**Key Parameters:**
- `implementing_jurisdictions`: ISO codes of implementing countries (e.g., `["USA", "CHN"]`)
- `affected_jurisdictions`: ISO codes of affected countries
- `affected_products`: HS product codes (6-digit integers, e.g., `[292149]`)
- `intervention_types`: Filter by type using names (e.g., `["Import tariff", "Export ban"]`) or IDs. Supports exact matches, case-insensitive matching, and partial matches. Use `gta://reference/intervention-types-list` resource to see all available types.
- `gta_evaluation`: Filter by assessment (`["Red", "Amber", "Green"]`)
- `date_announced_gte/lte`: Filter by announcement date (`"YYYY-MM-DD"`)
- `date_implemented_gte/lte`: Filter by implementation date
- `is_in_force`: Current status (`true` or `false`)
- `limit`: Results per query (1-1000, default 50)
- `offset`: Pagination offset (default 0)
- `sorting`: Sort order (default `"-date_announced"` for newest first)
- `response_format`: Output format (`"markdown"` or `"json"`)

**Example Queries:**
- "Find all US import tariffs on Chinese products announced in 2024"
- "Search for harmful EU subsidies affecting semiconductor products"
- "Get recent export restrictions implemented by any country"

### 2. `gta_get_intervention`
Retrieve complete details for a specific intervention by ID.

**Parameters:**
- `intervention_id`: The GTA intervention ID (integer, required)
- `response_format`: `"markdown"` or `"json"`

**Returns:** Full description, all sources, complete lists of affected jurisdictions and products, implementation timeline.

### 3. `gta_list_ticker_updates`
Monitor recent text updates to existing interventions.

**Parameters:**
- `implementing_jurisdictions`: Filter by country ISO codes
- `intervention_types`: Filter by intervention type
- `date_modified_gte`: Updates since this date (`"YYYY-MM-DD"`)
- `limit`: Results per query (1-1000, default 50)
- `offset`: Pagination offset
- `response_format`: `"markdown"` or `"json"`

**Use Cases:**
- Track changes to existing measures
- Monitor policy evolution over time
- Identify recent amendments or updates

### 4. `gta_get_impact_chains`
Extract granular implementing-product/sector-affected jurisdiction relationships.

**Parameters:**
- `granularity`: `"product"` for HS codes or `"sector"` for broader categories (required)
- `implementing_jurisdictions`: Filter by implementing countries
- `affected_jurisdictions`: Filter by affected countries
- `limit`: Results per query (1-1000, default 50)
- `offset`: Pagination offset
- `response_format`: `"markdown"` or `"json"`

**Use Cases:**
- Bilateral trade flow analysis
- Product-level impact assessment
- Sector-specific intervention mapping

## Data Fields

All intervention results include:
- **Intervention ID**: Unique identifier
- **Title**: Short description of the measure
- **Description**: Detailed explanation (full access only)
- **Sources**: Official documentation links
- **Implementing Jurisdictions**: Countries/groups implementing the measure
- **Affected Jurisdictions**: Countries impacted
- **Affected Products**: HS product codes with tariff levels (full access)
- **Intervention Type**: Classification (tariff, subsidy, etc.)
- **GTA Evaluation**: Red (harmful), Amber (mixed), Green (liberalizing)
- **Dates**: Announced, published, implemented, removed
- **Status**: Whether currently in force
- **URLs**: Links to GTA website for more details

## Citation and References

All intervention results include proper citations and references to facilitate verification and further research.

### Inline Citations

Each intervention mentioned in results includes an inline citation:
- **Format**: `[ID [123456](https://globaltradealert.org/intervention/123456)]`
- Appears next to the intervention title
- Clicking the ID opens the intervention page on globaltradealert.org

Example:
```
## 1. China: Launch of CNY 344 billion fund [ID [122819](https://globaltradealert.org/intervention/122819)]
```

### Reference List

At the end of each response, a "Reference List (in reverse chronological order)" section lists all cited interventions:
- **Format**: `YYYY-MM-DD: Title [ID [intervention_id](link)].`
- Sorted by announcement date (newest first, reverse chronological)
- Provides quick overview of all interventions discussed
- Intervention IDs are clickable links

**Example:**
```markdown
## Reference List (in reverse chronological order)

- 2024-07-04: EU: Temporary customs duty suspension extended [ID [138295](https://globaltradealert.org/intervention/138295)].
- 2024-05-24: China: Launch of CNY 344 billion fund [ID [122819](https://globaltradealert.org/intervention/122819)].
```

This citation format ensures all claims about trade interventions can be verified directly on the GTA website.

## Sorting and Finding Recent Data

**IMPORTANT:** The GTA API returns results **sorted by intervention ID (oldest first) by default**. To find recent interventions:

### Default Sorting Behavior (Changed in v1.1)

As of version 1.1, the MCP server **defaults to `sorting: "-date_announced"`** (newest first) to provide a better user experience. This means:

✅ Searches without explicit sorting will return recent interventions first
✅ You'll see October 2025 data when searching without date filters
✅ The most recent policy developments appear at the top of results

### Customizing Sort Order

You can override the default sorting by specifying the `sorting` parameter:

```
sorting: "-date_announced"  # Newest announcements first (default)
sorting: "date_announced"   # Oldest announcements first
sorting: "-intervention_id" # Highest ID first
```

Valid sort fields: `date_announced`, `date_published`, `date_implemented`, `date_removed`, `intervention_id`

### Best Practices for Finding Recent Data

1. **Use date filters for specific periods:**
   ```
   date_announced_gte: "2025-01-01"  # Data from 2025 onwards
   ```

2. **Rely on default sorting for recent data:**
   ```
   # No sorting parameter needed - defaults to newest first
   limit: 20
   ```

3. **Combine filters with sorting:**
   ```
   implementing_jurisdictions: ["USA"]
   date_announced_gte: "2025-10-01"
   sorting: "-date_announced"
   ```

See `gta://guide/searching` resource for comprehensive search guidance.

## Using Intervention Types

The `intervention_types` parameter supports flexible matching to make searches more intuitive:

### Matching Options

1. **Exact Name Match**
   ```
   intervention_types: ["Export ban", "Import tariff"]
   ```

2. **Case-Insensitive**
   ```
   intervention_types: ["export ban", "IMPORT TARIFF"]
   ```

3. **Partial Match** (when unique)
   ```
   intervention_types: ["Export licensing"]  # Matches "Export licensing requirement"
   ```

4. **Integer IDs** (advanced)
   ```
   intervention_types: [19, 47]  # Export ban, Import tariff
   ```

### Common Intervention Types

- **Export controls**: "Export ban", "Export licensing requirement", "Export quota"
- **Import barriers**: "Import ban", "Import tariff", "Import quota", "Import licensing requirement"
- **Subsidies**: "State loan", "Financial grant", "Production subsidy", "Export subsidy"
- **FDI restrictions**: "FDI: Entry and ownership rule", "FDI: Treatment and operations, nes"
- **Local requirements**: "Local content requirement", "Local operations requirement"
- **Trade remedies**: "Anti-dumping", "Safeguard", "Anti-subsidy"
- **Standards**: "Sanitary and phytosanitary measure", "Technical barrier to trade"

### Finding Intervention Types

Use the `gta://reference/intervention-types-list` resource to see all 79 available intervention types with their IDs.

### Ambiguous Matches

If your search term matches multiple types (e.g., "export restriction" matches both "Port restriction" and "Distribution restriction"), you'll receive an error with suggestions. Be more specific in your query.

## Available Resources

The GTA MCP server exposes reference data as resources that Claude can read to improve response accuracy and reduce hallucination. Resources are automatically available once the server is connected.

### Reference Tables (Static Resources)

#### `gta://reference/jurisdictions`
Complete jurisdiction lookup table with UN codes, ISO codes, and names for all countries and jurisdictions tracked by GTA.

**Use this to:**
- Look up UN country codes from ISO codes
- Find correct jurisdiction names
- Convert between ISO and UN code formats

#### `gta://reference/intervention-types`
Comprehensive descriptions of all GTA intervention types including:
- Detailed definitions and explanations
- Real-world examples with links to GTA database
- MAST (Multilateral Agreement on Services and Trade) classifications
- Guidance on when to use each type

**Use this to:**
- Understand what different intervention types mean
- Learn how to classify trade measures
- Find examples of each intervention type

#### `gta://reference/intervention-types-list`
Quick reference list of all available intervention type names with their slugs.

**Use this to:**
- Discover what intervention types exist
- Get the correct slug for looking up specific types

### Search Guidance Resources

#### `gta://guide/searching`
Comprehensive guide to searching the GTA database effectively.

**Covers:**
- Default sorting behavior and how to override it
- Finding recent interventions (the #1 issue users face)
- Common search patterns with examples
- Troubleshooting "no recent data found" issues
- Best practices for date filters and sorting

**⚠️ READ THIS if you're having trouble finding recent data!**

#### `gta://guide/date-fields`
Detailed explanation of GTA date fields and when to use each one.

**Explains:**
- `date_announced` - When policy was announced (use for recent searches)
- `date_implemented` - When policy took effect (often missing for recent data)
- `date_removed` - When policy was withdrawn
- `date_modified` - When database entry was updated
- Which date field to use for different questions
- Common mistakes and how to avoid them

**⚠️ READ THIS to understand why `date_announced` ≠ `date_implemented`**

### Dynamic Lookups (Template Resources)

#### `gta://jurisdiction/{iso_code}`
Look up detailed information for a specific jurisdiction using its ISO 3-letter code.

**Examples:**
- `gta://jurisdiction/USA` - United States details
- `gta://jurisdiction/CHN` - China details
- `gta://jurisdiction/DEU` - Germany details

**Returns:**
- UN country code (for API queries)
- Full jurisdiction name
- Short name and adjective forms

#### `gta://intervention-type/{type_slug}`
Look up detailed information about a specific intervention type using its slug.

**Examples:**
- `gta://intervention-type/export-ban` - Export ban details
- `gta://intervention-type/import-tariff` - Import tariff details
- `gta://intervention-type/state-loan` - State loan details

**Returns:**
- Complete description and definition
- Real-world examples from GTA database
- MAST classification
- Usage guidance

### When to Use Resources

**Use resources when you need to:**
- ✅ Convert ISO codes to UN codes for API queries
- ✅ Understand what an intervention type means
- ✅ Find examples of specific intervention types
- ✅ Verify correct jurisdiction or intervention type names
- ✅ Learn about MAST classifications

**Don't use resources for:**
- ❌ Searching for actual interventions (use `gta_search_interventions` tool instead)
- ❌ Getting real-time data (resources are static reference data)

## Response Formats

### Markdown
- **Human-readable** format optimized for presentation
- Clean formatting with headers, lists, and emphasis
- Truncates long descriptions for readability
- Limits large lists (e.g., first 10 countries)
- Includes clickable links to GTA website

### JSON
- **Machine-readable** structured data
- Complete API response with all fields
- Suitable for programmatic processing
- Preserves all metadata and nested structures

## Character Limits

Responses are limited to **25,000 characters** to prevent overwhelming LLM context windows. When limits are exceeded:
- Results are automatically truncated
- Clear truncation messages provided
- Guidance given on using pagination or filters
- Pagination metadata helps retrieve remaining results

## Error Handling

Clear, actionable error messages for:
- **Authentication failures**: Invalid or missing API key
- **Invalid parameters**: Constraint violations with guidance
- **API timeouts**: Suggestions to reduce result sets
- **Not found errors**: Specific intervention IDs
- **Rate limits**: Retry guidance

## Architecture

```
gta_mcp/
├── pyproject.toml          # Project configuration and dependencies
├── README.md               # This file
└── src/
    └── gta_mcp/
        ├── __init__.py     # Package initialization
        ├── server.py       # MCP server and tool implementations
        ├── api.py          # GTA API client with authentication
        ├── models.py       # Pydantic input validation models
        └── formatters.py   # Response formatting (markdown/JSON)
```

### Key Design Principles

1. **Code Reusability**: Shared formatters, API client, and utilities
2. **Input Validation**: Comprehensive Pydantic models with constraints
3. **Error Resilience**: Graceful handling with educational messages
4. **LLM Optimization**: 
   - Human-readable identifiers (country names vs IDs)
   - Concise markdown for readability
   - Pagination guidance in responses
   - Context-efficient truncation strategies

## Development

### Running Tests

```bash
# Verify server starts
uv run gta-mcp --help

# Check imports
uv run python -c "from gta_mcp import server; print('OK')"
```

### Code Quality

- **Type hints** throughout
- **Pydantic v2** for input validation
- **Async/await** for all I/O operations
- **DRY principle**: No code duplication
- **Tool annotations**: Proper MCP metadata

## Troubleshooting

### "GTA_API_KEY not set"
Set the environment variable before running:
```bash
export GTA_API_KEY='your-key-here'
```

### "Authentication Error"
Check your API key is valid and has appropriate permissions.

### "Response truncated"
Use pagination (`offset` parameter) or add more specific filters to reduce result set size.

### Server not appearing in Claude Desktop
1. Verify the absolute path in `claude_desktop_config.json`
2. Ensure `GTA_API_KEY` is set in the `env` section
3. Completely quit and restart Claude Desktop (not just close the window)

## API Documentation

Full GTA API documentation: https://api.globaltradealert.org/api/doc/

## License

This MCP server implementation is provided for use with the Global Trade Alert database.
API access requires valid credentials from SGEPT.

## Version History & Changelog

### Version 0.3.0 (November 9, 2025)

**Added: MAST Chapter Support**

Allows the server to query at a broader taxonomic level when users express general intent. When you mention "anti-dumping," the system can retrieve the entire trade defense toolkit (including safeguards, countervailing duties).

---

### Version 0.2.0 (November 8, 2025)

**Added: Text Search**

MCP can now search intervention descriptions and titles using keywords. Used for queries including company and entity names.

---

### Version 0.1.0 (Initial Release)

**Core Features:**
- Comprehensive intervention search with field-based filtering
- Citation and reference management
- Intervention type flexible matching
- Reference resources for jurisdictions and intervention types
- Search guidance documentation

---

**Note:** Pre-1.0 versions indicate experimental status. We welcome feedback and feature requests to improve the server.

## Support

For issues with:
- **This MCP server**: Contact Johannes Fritz at SGEPT
- **GTA API access**: Contact SGEPT for API credentials: https://globaltradealert.org/api-access 
- **MCP protocol**: See https://modelcontextprotocol.io/
