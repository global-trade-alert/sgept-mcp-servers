# DPA MCP Server

Model Context Protocol server providing access to the Digital Policy Alert (DPA) database. This server exposes digital policy events, enabling LLMs to search and analyze government regulations affecting the digital economy worldwide.

## Features

- **Comprehensive Search**: Filter events by countries, economic activities, policy areas, event types, dates, and more
- **Detailed Retrieval**: Get complete information for specific events including descriptions and sources
- **Flexible Output**: Both human-readable markdown and machine-readable JSON formats
- **Smart Pagination**: Handle large datasets with offset-based pagination (up to 1000 results per query)
- **Rich Reference Data**: Access to complete taxonomies, handbooks, and lookup tables

## Installation

### Prerequisites
- Python 3.10 or higher
- `uv` package manager ([install here](https://github.com/astral-sh/uv))
- DPA API key from SGEPT (same as GTA API key)

### Setup

```bash
# Clone or navigate to the project directory
cd dpa-mcp

# Install dependencies with uv
uv sync

# Set your API key
export DPA_API_KEY='your-api-key-here'

# Test the installation
uv run dpa-mcp --help
```

## Configuration

### Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "dpa": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/dpa-mcp",
        "run",
        "dpa-mcp"
      ],
      "env": {
        "DPA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Other MCP Clients

For clients supporting stdio transport, run:

```bash
uv run dpa-mcp
```

## Available Tools

### 1. `dpa_search_events`
Search and filter digital policy events with comprehensive parameters.

**Key Parameters:**
- `implementing_jurisdictions`: ISO codes of implementing countries (e.g., `["USA", "CHN", "DEU"]`)
- `economic_activities`: Digital economic sectors (e.g., `["ML and AI development", "platform intermediary: user-generated content"]`)
- `policy_areas`: Policy domains (e.g., `["Data governance", "Content moderation", "Competition"]`)
- `event_types`: Type of regulatory action (e.g., `["law", "order", "decision"]`)
- `government_branch`: Branch responsible (`["legislature", "executive", "judiciary"]`)
- `dpa_implementation_level`: Scope (e.g., `["national", "supranational"]`)
- `event_period_start/end`: Filter by event date (`"YYYY-MM-DD"`)
- `limit`: Results per query (1-1000, default 50)
- `offset`: Pagination offset (default 0)
- `sorting`: Sort order (default `"-id"` for newest first)
- `response_format`: Output format (`"markdown"` or `"json"`)

**Example Queries:**
- "Find all EU AI regulations announced in 2024"
- "Search for data governance policies affecting cloud computing"
- "Get recent content moderation laws from the United States"

### 2. `dpa_get_event`
Retrieve complete details for a specific event by ID.

**Parameters:**
- `event_id`: The DPA event ID (integer, required)
- `response_format`: `"markdown"` or `"json"`

**Returns:** Full description, implementers, policy classification, economic activities, and timeline.

## Data Fields

All event results include:
- **Event ID**: Unique identifier
- **Title**: Short description of the policy measure
- **Description**: Detailed explanation
- **Date**: When the event occurred
- **Status**: Current status (adopted, in force, etc.)
- **Event Type**: Classification (law, order, decision, etc.)
- **Action Type**: Lifecycle stage (adoption, implementation, etc.)
- **Implementers**: Countries/jurisdictions implementing the policy
- **Policy Area**: Legal domain (data governance, competition, etc.)
- **Policy Instrument**: Specific regulatory tool used
- **Economic Activities**: Digital sectors affected
- **Implementation Level**: Scope of the policy
- **URLs**: Links to DPA website for more details

## Citation and References

All event results include proper citations and references to facilitate verification and further research.

### Inline Citations

Each event mentioned in results includes an inline citation:
- **Format**: `[ID [20442](https://digitalpolicyalert.org/event/20442)]`
- Appears next to the event title
- Clicking the ID opens the event page on digitalpolicyalert.org

Example:
```
## 1. Adopted Second Edition Model AI Governance Framework [ID [20442](https://digitalpolicyalert.org/event/20442)]
```

### Reference List

At the end of each response, a "Reference List (in reverse chronological order)" section lists all cited events:
- **Format**: `YYYY-MM-DD: Title [ID [event_id](link)].`
- Sorted by date (newest first, reverse chronological)
- Provides quick overview of all events discussed
- Event IDs are clickable links

**Example:**
```markdown
## Reference List (in reverse chronological order)

- 2024-07-04: EU AI Act Adopted [ID [25123](https://digitalpolicyalert.org/event/25123)].
- 2024-05-24: US Executive Order on AI Safety [ID [24892](https://digitalpolicyalert.org/event/24892)].
```

This citation format ensures all claims about digital policy events can be verified directly on the DPA website.

## Sorting and Finding Recent Data

**IMPORTANT:** The DPA MCP server **defaults to `sorting: "-id"`** (newest events first) to provide recent data by default.

### Default Sorting Behavior

✅ Searches without explicit sorting will return recent events first
✅ You'll see recent 2024-2025 data when searching without date filters
✅ The most recent policy developments appear at the top of results

### Customizing Sort Order

You can override the default sorting by specifying the `sorting` parameter:

```
sorting: "-id"   # Newest events first (default)
sorting: "id"    # Oldest events first
sorting: "-date" # By date descending
sorting: "date"  # By date ascending
```

### Best Practices for Finding Recent Data

1. **Use date filters for specific periods:**
   ```
   event_period_start: "2024-01-01"  # Events from 2024 onwards
   ```

2. **Rely on default sorting for recent data:**
   ```
   # No sorting parameter needed - defaults to newest first
   limit: 20
   ```

3. **Combine filters with sorting:**
   ```
   implementing_jurisdictions: ["USA"]
   event_period_start: "2024-10-01"
   sorting: "-id"
   ```

## Using Economic Activities

The `economic_activities` parameter supports flexible matching:

### Matching Options

1. **Exact Name Match**
   ```
   economic_activities: ["ML and AI development", "platform intermediary: user-generated content"]
   ```

2. **Case-Insensitive**
   ```
   economic_activities: ["ml and ai development", "CLOUD COMPUTING"]
   ```

3. **Partial Match** (when unique)
   ```
   economic_activities: ["AI development"]  # Matches "ML and AI development"
   ```

### Common Economic Activities

- **AI & ML**: "ML and AI development"
- **Platforms**: "platform intermediary: user-generated content", "platform intermediary: e-commerce"
- **Infrastructure**: "infrastructure provider: internet and telecom services", "infrastructure provider: cloud computing, storage and databases"
- **Digital Payments**: "digital payment provider (incl. cryptocurrencies)"
- **Software**: "software provider: app stores", "software provider: other software"
- **Semiconductors**: "semiconductors"
- **Cross-cutting**: "cross-cutting" (affects entire digital economy)

### Finding Economic Activities

Use the `dpa://reference/economic-activities-list` resource to see all available economic activities.

## Available Resources

The DPA MCP server exposes reference data as resources that Claude can read to improve response accuracy.

### Reference Tables (Static Resources)

#### `dpa://reference/jurisdictions`
Complete jurisdiction lookup table with DPA IDs, ISO codes, and names for all countries tracked by DPA.

**Use this to:**
- Look up jurisdiction IDs from ISO codes
- Find correct jurisdiction names
- Convert between ISO and DPA ID formats

#### `dpa://reference/economic-activities`
Complete table of digital economic activities tracked by DPA with descriptions.

**Use this to:**
- Understand different digital economic sectors
- Find correct activity names for filtering
- Learn about DPA's economic taxonomy

#### `dpa://reference/economic-activities-list`
Quick reference list of all available economic activity names with slugs.

**Use this to:**
- Discover what economic activities exist
- Get the correct name for filtering

#### `dpa://reference/policy-areas`
Complete list of policy areas (legal domains) tracked by DPA.

**Use this to:**
- Understand different areas of digital policy
- Find correct policy area names for filtering

#### `dpa://reference/event-types`
List of all event types with binding/non-binding classification.

**Use this to:**
- Understand different types of regulatory actions
- Distinguish between binding and non-binding measures

#### `dpa://reference/action-types`
List of all action types representing policy lifecycle stages.

**Use this to:**
- Understand the progression of regulatory changes
- Track policies through their lifecycle

#### `dpa://reference/intervention-types`
Complete list of policy instruments (intervention types) with descriptions.

**Use this to:**
- Understand different regulatory tools
- Learn about specific policy mechanisms

#### `dpa://guide/handbook`
Complete DPA Activity Tracking Handbook.

**Use this to:**
- Understand DPA methodology
- Learn about the taxonomy in depth
- Get context on how DPA tracks digital policy

### Dynamic Lookups (Template Resources)

#### `dpa://jurisdiction/{iso_code}`
Look up detailed information for a specific jurisdiction using its ISO 3-letter code.

**Examples:**
- `dpa://jurisdiction/USA` - United States details
- `dpa://jurisdiction/CHN` - China details
- `dpa://jurisdiction/DEU` - Germany details

**Returns:**
- DPA jurisdiction ID (for API queries)
- Full jurisdiction name
- Short name and adjective forms

#### `dpa://economic-activity/{activity_slug}`
Look up detailed information about a specific economic activity using its slug.

**Examples:**
- `dpa://economic-activity/ml-and-ai-development` - AI/ML details
- `dpa://economic-activity/platform-intermediary-user-generated-content` - Platform details
- `dpa://economic-activity/cloud-computing` - Cloud computing details

**Returns:**
- Activity ID
- Complete description
- Usage guidance

### When to Use Resources

**Use resources when you need to:**
- ✅ Convert ISO codes to DPA IDs for API queries
- ✅ Understand what an economic activity means
- ✅ Find examples of specific policy instruments
- ✅ Verify correct jurisdiction or activity names
- ✅ Learn about DPA taxonomy and methodology

**Don't use resources for:**
- ❌ Searching for actual events (use `dpa_search_events` tool instead)
- ❌ Getting real-time data (resources are static reference data)

## Response Formats

### Markdown
- **Human-readable** format optimized for presentation
- Clean formatting with headers, lists, and emphasis
- Truncates long descriptions for readability
- Limits large lists (e.g., first 5 economic activities)
- Includes clickable links to DPA website

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
- **Not found errors**: Specific event IDs
- **Rate limits**: Retry guidance

## Architecture

```
dpa-mcp/
├── pyproject.toml          # Project configuration and dependencies
├── README.md               # This file
├── REQUIREMENTS.md         # Implementation tracking
└── src/
    └── dpa_mcp/
        ├── __init__.py     # Package initialization
        ├── server.py       # MCP server and tool implementations
        ├── api.py          # DPA API client with authentication
        ├── models.py       # Pydantic input validation models
        ├── formatters.py   # Response formatting (markdown/JSON)
        └── resources_loader.py # Resource loading utilities
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
uv run dpa-mcp --help

# Check imports
uv run python -c "from dpa_mcp import server; print('OK')"
```

### Code Quality

- **Type hints** throughout
- **Pydantic v2** for input validation
- **Async/await** for all I/O operations
- **DRY principle**: No code duplication
- **Tool annotations**: Proper MCP metadata

## Troubleshooting

### "DPA_API_KEY not set"
Set the environment variable before running:
```bash
export DPA_API_KEY='your-key-here'
```

### "Authentication Error" or "403 Forbidden"
Check your API key is valid and has **DPA endpoint permissions** enabled. While DPA and GTA use the same SGEPT API system, your API key must be specifically authorized for DPA endpoints. Contact SGEPT to verify your key has DPA access.

### "Response truncated"
Use pagination (`offset` parameter) or add more specific filters to reduce result set size.

### Server not appearing in Claude Desktop
1. Verify the absolute path in `claude_desktop_config.json`
2. Ensure `DPA_API_KEY` is set in the `env` section
3. Completely quit and restart Claude Desktop (not just close the window)

## API Documentation

Full DPA API documentation: https://api.globaltradealert.org/api/doc/

## About Digital Policy Alert

The Digital Policy Alert (DPA) is the first public inventory of laws and regulations affecting the digital economy. Launched in April 2021, DPA tracks over 6,000 policy changes across G20 nations, EU member states, and selected Southeast Asian countries.

**Coverage:**
- **Geographical**: G20, EU, Switzerland, and expanding to Southeast Asia
- **Policy Scope**: Data governance, content moderation, competition, taxation, AI, and more
- **Temporal**: Daily tracking since January 2020
- **Lifecycle**: Full tracking from proposal to revocation
- **Verification**: All entries verified with official sources

Learn more at: https://digitalpolicyalert.org/

## License

This MCP server implementation is provided for use with the Digital Policy Alert database.
API access requires valid credentials from SGEPT.

## Support

For issues with:
- **This MCP server**: Contact Johannes Fritz at SGEPT
- **DPA API access**: Contact SGEPT for API credentials
- **MCP protocol**: See https://modelcontextprotocol.io/
