# Changelog

All notable changes to the GTA MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-23

### Added

#### Core Features
- **MCP Server Implementation**: Full Model Context Protocol server for GTA database access
- **Four Main Tools**:
  - `gta_search_interventions`: Comprehensive search with 15+ filter parameters
  - `gta_get_intervention`: Detailed intervention retrieval by ID
  - `gta_list_ticker_updates`: Monitor recent changes to existing interventions
  - `gta_get_impact_chains`: Granular bilateral trade relationship analysis

#### Search & Filtering
- ISO country code to UN code conversion (200+ jurisdictions)
- Intervention type name-to-ID conversion (79 types)
- Flexible intervention type matching (exact, case-insensitive, partial)
- Date range filtering (announcement, implementation, removal dates)
- Product filtering (HS 6-digit codes)
- GTA evaluation filtering (Red/Amber/Green)
- In-force status filtering
- Smart pagination (up to 1000 results per query)
- Configurable sorting (default: newest first)

#### Formatting & Output
- Markdown format (human-readable, optimized for LLMs)
- JSON format (machine-readable, structured)
- Inline citations with clickable GTA links
- Reference lists in reverse chronological order
- Automatic HTML tag stripping from descriptions
- Character limit handling (25,000 chars) with smart truncation

#### Resources & Documentation
- 7 MCP resources for reference data:
  - Jurisdictions table (UN codes, ISO codes, names)
  - Intervention types descriptions (with examples)
  - Intervention types list (quick reference)
  - Jurisdiction lookup by ISO code
  - Intervention type details by slug
  - Search guide (best practices)
  - Date fields guide (understanding GTA dates)

#### Robustness & Error Handling
- Defensive type checking for all text fields
- Safe extraction from list/dict/string formats
- Graceful handling of missing data
- Clear, actionable error messages
- API timeout handling
- Authentication error detection

### Technical Details

#### Architecture
- Clean separation of concerns:
  - `api.py`: API client and request handling
  - `models.py`: Pydantic input validation
  - `formatters.py`: Response formatting utilities
  - `server.py`: MCP tool implementations
  - `resources_loader.py`: Resource file loading
- Async/await for all I/O operations
- Type hints throughout codebase
- Comprehensive docstrings

#### Dependencies
- `mcp>=1.0.0`: Model Context Protocol SDK
- `httpx>=0.27.0`: Async HTTP client
- `pydantic>=2.0.0`: Data validation

#### Configuration
- Environment variable for API key: `GTA_API_KEY`
- Compatible with Claude Desktop and other MCP clients
- uv package manager for dependency management

### Documentation

- Comprehensive README with:
  - Installation instructions
  - Configuration examples
  - Tool documentation
  - Search best practices
  - Citation format examples
  - Resource descriptions
- Quick start guide
- Usage examples
- Implementation summary
- Contributing guidelines

### Known Limitations

- Character limit of 25,000 chars per response (with smart truncation)
- API requires valid GTA API key from SGEPT
- Some GTA fields may be lists of objects (handled with defensive parsing)
- Ticker API returns lists directly (wrapped by server)

---

## [Unreleased]

### Planned Features
- Unit test suite
- Integration tests with mock API
- Additional intervention type aliases
- Batch intervention retrieval
- Export to CSV/Excel formats
- Caching layer for frequent queries

---

## Version History

- **0.1.0** (2025-10-23): Initial release with full MCP server implementation

## Notes

### Versioning Guidelines
- **Major** (1.0.0): Breaking API changes
- **Minor** (0.1.0): New features, backwards compatible
- **Patch** (0.1.1): Bug fixes, backwards compatible

### Upgrade Instructions

When upgrading, always:
1. Check this CHANGELOG for breaking changes
2. Update your `GTA_API_KEY` if authentication changes
3. Restart Claude Desktop to reload the MCP server
4. Review updated documentation in README.md
