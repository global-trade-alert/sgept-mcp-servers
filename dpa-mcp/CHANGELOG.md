# Changelog

All notable changes to the DPA MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-24

### Added

#### Core Features
- **MCP Server** with 2 tools and 14 resources for Digital Policy Alert database access
- **Tool: `dpa_search_events`** - Search and filter digital policy events with comprehensive parameters
  - Filter by jurisdictions (ISO codes), economic activities, policy areas, event types
  - Date range filtering, pagination, and custom sorting
  - Support for both markdown and JSON output formats
- **Tool: `dpa_get_event`** - Retrieve detailed information for specific events by ID

#### Resources
- **12 Static Resources** for reference data:
  - Jurisdictions table with ISO codes and DPA IDs
  - Economic activities list with descriptions
  - Economic activities quick reference
  - Policy areas list
  - Event types list
  - Action types list
  - Intervention types (policy instruments)
  - DPA Activity Tracking Handbook
  - And more...
- **2 Dynamic Resources** for lookups:
  - `dpa://jurisdiction/{iso_code}` - Jurisdiction details by ISO code
  - `dpa://economic-activity/{slug}` - Economic activity details by slug

#### API Integration
- Async HTTP client for DPA API (`/api/v1/dpa/events/`)
- Authentication with API key
- Comprehensive data mappings:
  - ISO codes → DPA jurisdiction IDs
  - Economic activity names → IDs (with fuzzy matching)
  - Policy area names → IDs
  - Event type names → IDs
  - Action type names → IDs
- Robust error handling with educational messages

#### Data Processing
- Pydantic v2 input validation for all tool parameters
- Smart response formatting:
  - Markdown format for human-readable output
  - JSON format for machine processing
  - 25,000 character limit with intelligent truncation
  - Inline citations with clickable DPA links
  - Reference lists sorted reverse chronologically
- Pagination support (up to 1000 results per query)

#### Documentation
- **README.md** - Complete user documentation
- **INDEX.md** - Package overview and navigation guide
- **QUICKSTART.md** - 5-minute installation guide
- **USAGE_EXAMPLES.md** - 17 real-world query examples
- **IMPLEMENTATION_SUMMARY.md** - Technical architecture details
- **LICENSE** - MIT License
- **CHANGELOG.md** - This file

#### Code Quality
- Type hints throughout all modules
- Async/await for all I/O operations
- Comprehensive docstrings
- No code duplication (DRY principle)
- MCP best practices:
  - Tool annotations (readOnly, idempotent, openWorld)
  - Clear error messages
  - Example queries in documentation

### Technical Details

- **Python Version**: >=3.10
- **Dependencies**:
  - `mcp>=1.0.0` - Model Context Protocol SDK
  - `httpx>=0.27.0` - Async HTTP client
  - `pydantic>=2.0.0` - Data validation
- **Architecture**: Modular design with 5 core Python modules
  - `server.py` (~350 lines) - MCP server and tools
  - `api.py` (~380 lines) - DPA API client
  - `models.py` (~100 lines) - Input validation
  - `formatters.py` (~270 lines) - Response formatting
  - `resources_loader.py` (~320 lines) - Resource management

### Notes

- Initial production-ready release
- Modeled after the proven GTA MCP server architecture
- Requires valid DPA API key with appropriate permissions
- Claude Desktop integration supported

[0.1.0]: https://github.com/yourusername/dpa-mcp/releases/tag/v0.1.0
