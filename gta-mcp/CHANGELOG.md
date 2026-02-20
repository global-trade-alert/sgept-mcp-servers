# Changelog

All notable changes to the GTA MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.9] - 2026-02-20

### Changed
- **Dataset links: one labeled link per tool call, no "full dataset" inference**: Removed the v0.4.8 logic that tried to infer a "full dataset" by stripping non-date filters. That approach was wrong — if the user asks about subsidies, the full dataset IS subsidies, not everything. Now each tool call produces one clearly labeled link for its exact filters (e.g., `📊 Dataset — MAST L | 2026-02-01 to 2026-02-28`). The LLM is instructed to include ALL unique links from all tool calls, letting it determine which is broadest based on context.

## [0.4.8] - 2026-02-20

### Fixed
- **Dataset links show filtered subset instead of full dataset**: Every tool response now includes a "Full dataset" link (date-only filters) alongside any filtered link. When the query has non-date filters (e.g., MAST chapter, country), both the full and filtered links are shown with clear labels so users can access both views.
- **LLM can't find search/get tools — only uses counts**: Added explicit `RELATED TOOLS` cross-reference sections to all tool docstrings so the model discovers `gta_search_interventions` and `gta_get_intervention` from any tool. Added workflow hint at the end of count responses: "Use `gta_search_interventions` to browse individual interventions, or `gta_get_intervention` to read full text."

## [0.4.7] - 2026-02-20

### Fixed
- **Dataset links still dropped by LLM**: Moved Activity Tracker and Data Centre links from the bottom to the **top** of tool responses (new `make_dataset_links_header`). Links at the bottom were consistently stripped during multi-tool synthesis. Top-positioned compact links (`📊 Explore this data: ...`) are much harder for the LLM to drop. Full links section remains at bottom as fallback. Strengthened CRITICAL docstring instructions to reference the top-of-response format and allow "at least one" set of links when multiple tools are called.

## [0.4.6] - 2026-02-20

### Fixed
- **Dataset links dropped by LLM**: Added `⚠️ CRITICAL` instructions to `gta_count_interventions` and `gta_search_interventions` tool docstrings requiring the LLM to preserve the "Explore Full Dataset" section (Activity Tracker + Data Centre links). Previously only Reference List had a CRITICAL instruction, so LLMs consistently dropped the dataset links when summarising results.

## [0.4.3] - 2026-02-14

### Fixed
- **Status label**: Interventions not yet in force were incorrectly labelled "Removed" in all formatters. Now uses three-state logic: "In force", "Removed" (has revocation date), "Not yet in force" (announced/pending)

## [0.4.2] - 2026-02-14

### Added
- **Comprehensive Analysis Prompt** (`comprehensive_analysis`): MCP prompt guiding mixed quantitative + qualitative analysis workflows

### Fixed
- **Tool routing**: Improved tool descriptions to prevent over-reliance on the count endpoint when users ask to see, read, or fetch interventions

## [0.4.0] - 2026-02-12

### Added
- **GTA Glossary Resource** (`gta://reference/glossary`): Definitions of 18 key GTA terms for non-expert users — evaluations, MAST chapters, HS codes, CPC sectors, implementation levels, and more
- **Use Case Library** (`USE_CASES.md`): 40+ copy-paste example prompts across 8 professional categories
- **User-First README**: Complete rewrite targeting non-developer trade professionals with "What is GTA?", example prompts, post-install verification, and error-indexed troubleshooting

### Changed
- **Expanded Resources**: data_model.md (3x larger with worked examples), common_mistakes.md (2x with concrete DO/DON'T examples), eligible_firms and implementation_levels tables with full descriptions
- **PyPI Metadata**: Added keywords (tariffs, subsidies, trade-barriers), classifiers (Science/Research), project URLs (documentation, changelog, bug tracker)

## [0.3.0] - 2026-02-12

### Added
- **Expanded Resource Support**: MAST chapter taxonomy, query syntax guide, CPC vs HS guide, exclusion filters guide, parameters reference, query examples library (35+ patterns)
- **MAST Chapter Support**: Broader taxonomic querying (letters A-P, IDs 1-20, special categories)
- **Advanced Filter Parameters**: CPC sector filtering, eligible firms, implementation levels, inclusion/exclusion logic via keep_* parameters
- **Counts Tool** (`gta_count_interventions`): Server-side aggregation with 24 count_by dimensions
- **Analytical Knowledge Resources** (v0.3.1): Data model guide, analytical caveats (15 critical rules), common mistakes checklist
- **Enhanced Tool Descriptions**: Overcounting warnings, evaluation semantics, publication lag guidance

### Changed
- Reduced schema documentation overhead by 72% (~2,200 tokens saved per conversation)
- Field descriptions streamlined to <60 words with resource references
- Package renamed to `sgept-gta-mcp` for PyPI distribution

## [0.2.0] - 2025-11-08

### Added
- **Text Search**: Search intervention descriptions and titles using keywords (company/entity names)

## [0.1.0] - 2025-10-23

### Added
- **MCP Server Implementation**: Full Model Context Protocol server for GTA database access
- **Four Main Tools**: search, get, ticker, impact chains
- **Search & Filtering**: ISO-to-UN code conversion, intervention type matching, date/product/evaluation filtering, pagination
- **Formatting**: Markdown and JSON output, inline citations, 25K character limit with smart truncation
- **Resources**: Jurisdictions table, intervention types, search guide, date fields guide
- **Error Handling**: Defensive parsing, clear error messages, timeout handling

---

## Version History

- **0.4.3** (2026-02-14): Fix false "Removed" status on pending interventions
- **0.4.2** (2026-02-14): Comprehensive analysis prompt, tool routing fix
- **0.4.0** (2026-02-12): Public release — glossary resource, use case library, user-first README, expanded references
- **0.3.0** (2026-02-12): Expanded resources, MAST chapters, advanced filters, counts tool, analytical knowledge, PyPI publication
- **0.2.0** (2025-11-08): Text search for entity names
- **0.1.0** (2025-10-23): Initial release

## Versioning Guidelines
- **Major** (1.0.0): Breaking API changes
- **Minor** (0.x.0): New features, backwards compatible
- **Patch** (0.x.y): Bug fixes, backwards compatible
