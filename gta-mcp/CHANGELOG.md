# Changelog

All notable changes to the GTA MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

- **0.4.0** (2026-02-12): Public release — glossary resource, use case library, user-first README, expanded references
- **0.3.0** (2026-02-12): Expanded resources, MAST chapters, advanced filters, counts tool, analytical knowledge, PyPI publication
- **0.2.0** (2025-11-08): Text search for entity names
- **0.1.0** (2025-10-23): Initial release

## Versioning Guidelines
- **Major** (1.0.0): Breaking API changes
- **Minor** (0.x.0): New features, backwards compatible
- **Patch** (0.x.y): Bug fixes, backwards compatible
