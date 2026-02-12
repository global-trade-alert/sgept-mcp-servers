# GTA MCP Server

Query 78,000+ trade policy interventions through Claude — tariffs, subsidies, export bans, and more from 200+ countries.

## What is Global Trade Alert?

Global Trade Alert (GTA) is a transparency initiative by the St Gallen Endowment for Prosperity through Trade (SGEPT) that tracks government trade policy changes worldwide since November 2008. Unlike trade databases that rely on government self-reporting, GTA independently documents and verifies policy interventions using primary sources — official gazettes, ministry announcements, legislative records, and press releases.

GTA covers all types of trade measures: not just tariffs, but subsidies, export restrictions, FDI barriers, public procurement rules, localisation requirements and more. Each intervention is classified by color: Red (harmful/discriminatory), Amber (likely harmful but uncertain), or Green (liberalising). The database contains over 78,000 documented interventions across 200+ jurisdictions.

This breadth distinguishes GTA from the WTO's trade monitoring system, which captures only measures that governments voluntarily report. GTA reveals the full landscape of state intervention in markets — including measures governments prefer not to highlight.

## What can you ask?

**Tariffs and trade barriers:**
- "What tariffs has the United States imposed on China since January 2025?"
- "Which countries have imposed tariffs affecting US exports in 2025?"

**Critical minerals and supply chains:**
- "What export controls has China imposed on rare earth elements?"
- "Has the use of export restrictions increased since 2020?"

**Subsidies and state aid:**
- "Which countries subsidise their domestic semiconductor industry?"
- "Which G20 countries have increased state aid to EV manufacturers since 2022?"

**Trade negotiations:**
- "What harmful measures has the EU imposed on US exports since 2024?"
- "What measures has Brazil implemented affecting US agricultural exports?"

**Trade defence:**
- "Find all anti-dumping investigations targeting Chinese steel since 2020"

**Monitoring:**
- "How many harmful interventions were implemented globally in 2025 versus 2024?"

## Quick Start

### Prerequisites

You need **uv** (a Python package manager) installed on your system. If you don't have it:

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installing, restart your terminal. Verify it works by running `uvx --version` — you should see a version number.

### Getting an API key

You need a GTA API key from SGEPT. Request access at https://globaltradealert.org/api-access — you'll receive your demo key direcly; request support for full access credentials.

### For Claude Desktop (recommended)

Add to your Claude Desktop config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

If this file doesn't exist yet, create it with the content below. If it already exists and contains other MCP servers, add the `"gta"` entry inside the existing `"mcpServers"` object.

```json
{
  "mcpServers": {
    "gta": {
      "command": "uvx",
      "args": ["sgept-gta-mcp"],
      "env": {
        "GTA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Then **completely quit and restart Claude Desktop** (not just close the window — fully quit from the menu bar/system tray).

### For Claude Code

```bash
claude mcp add --transport stdio gta -e GTA_API_KEY=your-key -- uvx sgept-gta-mcp
```

### For any MCP client

```bash
pip install sgept-gta-mcp
GTA_API_KEY=your-key gta-mcp
```

## Is it working?

After restarting Claude Desktop, try this prompt:

> Show me 3 recent trade interventions implemented by the United States.

**If it works:** You'll see a formatted list of US trade measures with titles, dates, and links to the GTA website.

**If you see "tool not found":** The server isn't connected. Check that:
1. Your `claude_desktop_config.json` is valid JSON (no trailing commas, all quotes matched)
2. You completely quit and restarted Claude Desktop
3. Your API key is correctly set in the `env` section

**If you see "Authentication Error":** Your API key is invalid or expired. Verify it at https://globaltradealert.org/api-access.

## Use Cases

See [USE_CASES.md](USE_CASES.md) for 40+ example prompts organized by professional use case — from competitive subsidy intelligence to trade negotiation prep.

## Available Tools

### 1. `gta_search_interventions`

Search and filter trade interventions by country, type, date, sector, and evaluation.

**Key parameters:**
- `implementing_jurisdictions`: Countries implementing measures (e.g., ["USA", "CHN", "DEU"])
- `intervention_types`: Filter by measure type (e.g., ["Import tariff", "Export subsidy", "Export ban"])
- `date_announced_gte` / `date_announced_lte`: Filter by announcement date range
- `evaluation`: Red (harmful), Amber (likely harmful), or Green (liberalising)
- `limit`: Maximum results to return (default 100)

**Example:** "What tariffs has India imposed on steel imports since 2024?"

### 2. `gta_get_intervention`

Get full details for a specific intervention by ID (identification number from search results).

**Key parameters:**
- `intervention_id`: The unique GTA intervention ID

**Example:** "Show me the full details for intervention 123456"

### 3. `gta_list_ticker_updates`

Monitor recent changes to existing interventions — removals, extensions, modifications.

**Key parameters:**
- `published_gte` / `published_lte`: Filter by when the update was published
- `implementing_jurisdictions`: Filter by country
- `limit`: Maximum results to return

**Example:** "What changes to existing trade measures were published in the last 30 days?"

### 4. `gta_get_impact_chains`

Analyze implementing-product-affected jurisdiction relationships — which countries impose measures on which products affecting which other countries.

**Key parameters:**
- `implementing_jurisdictions`: Countries implementing measures
- `affected_jurisdictions`: Countries affected by measures
- `mast_chapters`: Product categories (MAST classification system)

**Example:** "Show me how US measures on semiconductors affect China and Taiwan"

### 5. `gta_count_interventions`

Get aggregated counts across 24 dimensions including year, country, type, sector, and evaluation.

**Key parameters:**
- `group_by`: Dimension to count by (e.g., "year", "implementing_jurisdiction", "intervention_type")
- Filters: Same as `gta_search_interventions`

**Example:** "How many harmful trade interventions did G20 countries implement each year from 2020 to 2025?"

### 6. `gta_lookup_hs_codes`

Search HS (Harmonized System) product codes by keyword, chapter number, or code prefix. Use this before `gta_search_interventions` when asking about specific commodities or products.

**Key parameters:**
- `search_term`: Product keyword (e.g., "lithium"), chapter number (e.g., "28"), or code prefix (e.g., "8541")
- `max_results`: Maximum codes to return (default 50)

**Example:** "Look up HS codes for steel" returns codes like 7206-7229 which you can then pass to `gta_search_interventions` as `affected_products`.

### 7. `gta_lookup_sectors`

Search CPC (Central Product Classification) sector codes by keyword or code prefix. Use this before `gta_search_interventions` when asking about services or broad economic sectors.

**Key parameters:**
- `search_term`: Sector keyword (e.g., "financial", "transport") or code prefix (e.g., "71")
- `max_results`: Maximum sectors to return (default 50)

**Example:** "Look up sectors related to financial services" returns CPC codes like 711, 715, 717 which you can pass as `affected_sectors`.

## Available Resources

Resources provide reference data and documentation through the MCP resource system (accessible via prompts like "Show me the GTA glossary").

| Resource | URI | Purpose |
|----------|-----|---------|
| Jurisdictions | `gta://reference/jurisdictions` | Country codes, names, ISO/UN mapping |
| Jurisdiction Groups | `gta://reference/jurisdiction-groups` | G7, G20, EU-27, BRICS, ASEAN, CPTPP, RCEP member codes |
| Intervention Types | `gta://reference/intervention-types` | Definitions, examples, MAST mapping |
| MAST Chapters | `gta://reference/mast-chapters` | Product classification system |
| Sectors | `gta://reference/sectors` | Economic sector taxonomy |
| Glossary | `gta://reference/glossary` | Key GTA terms explained for non-experts |
| Data Model | `gta://guide/data-model` | How interventions, products, and jurisdictions relate |
| Date Fields | `gta://guide/date-fields` | Announced vs implemented dates |
| CPC vs HS | `gta://guide/cpc-vs-hs` | When to use sector codes vs product codes |
| Analytical Caveats | `gta://guide/analytical-caveats` | Data limitations and interpretation guidance |
| Query Intent Mapping | `gta://guide/query-intent-mapping` | Natural language terms to structured GTA filters |
| Query Patterns | `gta://guide/query-patterns` | Common analysis workflows |

## Understanding GTA Data

**Evaluation colors:** Red = harmful/discriminatory, Amber = likely harmful but uncertain, Green = liberalising. See `gta://reference/glossary` for detailed definitions.

**Date fields:** `date_announced` (when disclosed) vs `date_implemented` (when takes effect). Implementation dates may be months or years after announcement. See `gta://guide/date-fields`.

**Publication lag:** Recent data is always incomplete due to a 2-4 week verification process. Counts from the last month should be considered preliminary. See `gta://guide/analytical-caveats`.

**Counting:** One intervention can affect many products and countries. Counting by product or affected jurisdiction inflates numbers — count by intervention for accurate totals. See `gta://guide/data-model`.

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| "uvx: command not found" | uv is not installed | Install uv first — see [Prerequisites](#prerequisites) above |
| "GTA_API_KEY not set" | Environment variable missing | Set it in Claude Desktop config `env` section, or `export GTA_API_KEY=...` for CLI |
| "Authentication Error" | Invalid or expired key | Verify at globaltradealert.org/api-access, check for typos |
| "Response truncated" | Too many results for context window | Use `limit` parameter (e.g., 10) or add more specific filters |
| Server not appearing in Claude | Config issue | Check JSON syntax, verify path, quit+restart Claude fully |
| No results returned | Filters too narrow or wrong date field | Try `date_announced_gte` instead of `date_implemented_gte`, broaden jurisdiction filter |
| Timeout errors | Query too broad | Add country or date filters to narrow results |
| Invalid jurisdiction code | Wrong format | Use ISO 3-letter codes (USA, CHN, DEU), not 2-letter or numeric |
| Rate limit (429) | Too many queries | Wait 30 seconds and retry |

## For Developers

### Architecture

```
Claude Desktop
    ↓
MCP Protocol (stdio)
    ↓
GTA MCP Server (FastMCP)
    ↓
GTA API v2.0 (REST)
    ↓
PostgreSQL Database
```

### Development Install

```bash
git clone https://github.com/sgept/sgept-mcp-servers.git
cd sgept-mcp-servers/gta-mcp
pip install -e ".[dev]"
export GTA_API_KEY=your-key
mcp dev gta_mcp/server.py
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=gta_mcp --cov-report=term-missing

# Specific test file
pytest tests/test_tools.py
```

### Code Quality

- Python 3.12+
- Type hints on all functions
- FastMCP for MCP protocol handling
- httpx for async API requests
- pytest for testing
- Black for formatting
- Ruff for linting

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Version and License

**Current version:** 0.4.0 (February 2026)

**License:** MIT

**Support:**
- API access: Contact SGEPT at support@sgept.org
- Server bugs: File issues on GitHub at https://github.com/sgept/sgept-mcp-servers
- Full changelog: [CHANGELOG.md](CHANGELOG.md)

**About SGEPT:** Learn more at https://sgept.org
