# DPA API Gap Analysis & Capability Uplift

**Date:** 2026-03-05
**Author:** Claude (commissioned by Johannes Fritz)
**Status:** Reference document for DPA API development

## Executive Summary

The Digital Policy Alert (DPA) and Global Trade Alert (GTA) share the same `gtaapi` Django backend (`api.globaltradealert.org`). The GTA side has a mature public API (12+ endpoints, API key auth, aggregation, streaming export) and a feature-rich MCP server (7 tools, 18 resources, 3,500 lines). The DPA side has website-serving ViewSets but no public data API, and a minimal MCP server (2 tools, 13 resources, 1,400 lines).

This document maps every gap, identifies what DPA already has, highlights DPA-unique capabilities that must be preserved, and provides a phased implementation roadmap.

---

## Layer 1: Backend API (gtaapi Django)

### What GTA Backend Has (That DPA Lacks)

| GTA Capability | GTA Location | DPA Equivalent | Gap |
|---|---|---|---|
| **Public interventions endpoint** with API key auth, streaming export, data slicer filtering | `api/urls.py` -> `interventions_view` | None -- DPA events only served via website ViewSets | **CRITICAL** |
| **Data counts / aggregation endpoint** | `api/urls.py` -> `data_counts` | None | **CRITICAL** |
| **Reference table endpoints** (jurisdiction, intervention_type, implementation_level, etc.) | `api/urls.py` -> 12 helper views | None -- DPA serves these inline to website | **HIGH** |
| **Helper tables combined endpoint** | `api/urls.py` -> `helper_tables_view` | None | **MEDIUM** |
| **API key authentication + tier system** | `users/api/authentication.py` -> `APIKeyAuthentication` | Partially exists (`APIUserPermission` model has `is_restricted_dpa`, `dpa_delay` fields) | **HIGH** -- model exists, endpoints don't use it |
| **Trade data / macro indicators** | `api/urls.py` -> `trade_data`, `trade_counts`, `trade_coverage` | N/A -- DPA has no trade data equivalent | **NOT APPLICABLE** |
| **ClickHouse backend for analytics** | `api/urls.py` -> `*_ch` endpoints | N/A | **FUTURE** -- only needed at scale |
| **Ticker / change monitoring endpoint** | `gta/` ticker views | N/A -- DPA events are single-dated records; querying recent events by date or date_modified provides equivalent "what's new" capability without a separate ticker mechanism | **NOT APPLICABLE** |
| **Impact chain analysis** | `gta/` impact chain views | None | **MEDIUM** -- could map to policy propagation |
| **Full-text search with operators** | GTA data slicer `query` param | DPA `SearchViewSet` exists but limited | **MEDIUM** |
| **Sync status monitoring** | `api/urls.py` -> `SyncStatusView` | None | **LOW** |

### What DPA Backend Already Has

| DPA Capability | Location | Notes |
|---|---|---|
| Intervention CRUD + 25+ detail actions | `dpa/api/views.py` -> `InterventionViewSet` | Website-oriented, not public API |
| Event listing + detail | `dpa/api/views.py` -> `EventViewSet` | Used by MCP server today |
| Text search | `dpa/api/views.py` -> `SearchViewSet` | Basic |
| Filtering via `FilterViewSetMixin` | `dpa/api/mixins/views.py` | jurisdiction, policy_area, economic_activity, event_type, etc. |
| Subscriptions (event + issue) | `dpa/api/views.py` | Newsletter/alert functionality |
| Issue tracking | `dpa/api/views.py` -> `IssueViewSet` | Cross-cutting policy threads |
| Jurisdiction, PolicyArea, EconomicActivity endpoints | `dpa/api/versions/v1.py` | Reference data via ViewSets |
| DPA-specific permission model | `core/models/dpa.py` -> `APIUserPermission` | `is_restricted_dpa`, `dpa_delay` fields exist |
| Newsletter system | `dpa/tasks.py` | Daily, weekly, instant |
| Streaming export | `InterventionViewSet` inherits `StreamingExportViewSetMixin` | Already there |

### Key Insight

DPA has ~70% of the backend infrastructure (models, ViewSets, mixins, serializers). The gap is a **public API facade** -- new URL routes with API key auth, query parameter mapping, and aggregation views. Much of Phase 1 is wiring, not greenfield.

---

## Layer 2: MCP Server (Public Interface)

### Tool Comparison

| Capability | GTA MCP | DPA MCP | Gap |
|---|---|---|---|
| **Search tool** | `gta_search_interventions` -- 39 filter params, detail levels, exclusion filters, full-text query | `dpa_search_events` -- 11 filter params, basic | **CRITICAL** |
| **Get single item** | `gta_get_intervention` | `dpa_get_event` | **PARITY** |
| **Ticker / updates** | `gta_list_ticker_updates` | N/A -- DPA events are atomic single-date records; recent event queries serve this purpose | **N/A** |
| **Aggregation / counts** | `gta_count_interventions` -- 24 count dimensions | None | **CRITICAL** |
| **Impact analysis** | `gta_get_impact_chains` -- product/sector granularity | None | **MEDIUM** |
| **Product code lookup** | `gta_lookup_hs_codes` | N/A -- DPA uses economic activities not HS codes | **N/A** |
| **Sector lookup** | `gta_lookup_sectors` | N/A -- DPA uses economic activities | **N/A** |

### Feature Comparison (within search tool)

| Feature | GTA MCP | DPA MCP | Gap |
|---|---|---|---|
| Detail level control | overview/standard/full | Single level only | **HIGH** |
| Response field control | `show_keys` parameter | None | **MEDIUM** |
| Exclusion filters | 9 `keep_*` params to invert filters | None | **HIGH** |
| Full-text query | `query` param with `\|`, `&`, `#` operators | None | **HIGH** |
| Affected jurisdiction filter | Yes (implementing vs affected) | Only implementing | **HIGH** |
| Date range granularity | 3 date types (announced, implemented, modified) | 1 date range (event_period) | **HIGH** |
| Sorting options | Multiple sort fields | `-id`, `id`, `-date`, `date` only | **MEDIUM** |

### Resource Comparison

| Aspect | GTA MCP | DPA MCP | Gap |
|---|---|---|---|
| Total resources | 18 (incl. 8 guides) | 13 (1 guide) | **HIGH** |
| Guide resources | searching, date-fields, parameters, query-examples, query-syntax, exclusion-filters, data-model, common-mistakes, query-intent-mapping | handbook only | **HIGH** |
| Code size | ~3,500 lines across 8 files | ~1,400 lines across 5 files | -- |

---

## Layer 3: DPA-Specific Capabilities (Not in GTA)

These capabilities are unique to DPA and must be preserved and surfaced in the public API. They are NOT gaps to fill from GTA -- they are DPA strengths.

| Capability | Rationale | Current Status |
|---|---|---|
| **Issue/thread tracking** | DPA tracks cross-cutting policy issues (e.g., "EU AI Act") linking multiple interventions. GTA has no equivalent. | In DPA backend (`IssueViewSet`), not in MCP |
| **Government branch filtering** | DPA classifies by legislature/executive/judiciary. GTA doesn't. | In DPA MCP already |
| **Binding vs non-binding classification** | DPA distinguishes binding from non-binding events. Critical for policy analysis. | In backend, not in MCP filters |
| **Policy lifecycle tracking** | DPA has 23 action types showing regulatory progression (announcement -> adoption -> implementation). More granular than GTA. | In backend, partially in MCP |
| **Economic activity taxonomy** | DPA's 22 digital sectors are a unique taxonomy. | Well-served in MCP already |

---

## Implementation Roadmap

### Phase 1: Public Data API Endpoints (Backend)

**Goal:** Create DPA equivalents of the GTA public API layer.
**Scope:** New file `dpa/api/public_views.py` + URL registration in `dpa/api/versions/v1.py`.
**Dependency:** None -- can start immediately.

| Endpoint | Priority | Notes |
|---|---|---|
| `GET /api/v1/dpa/events/` | CRITICAL | Public events endpoint with API key auth, complex filtering, streaming export. Reuses existing `EventViewSet` logic. |
| `GET /api/v1/dpa/data-counts/` | CRITICAL | Aggregation endpoint. Count by: jurisdiction, policy_area, economic_activity, event_type, year, month, implementation_level, action_type, government_branch, binding_status. |
| ~~`GET /api/v1/dpa/ticker/`~~ | N/A | Not needed -- DPA events are single-dated; sorting by `date_modified` on the events endpoint covers "what changed" queries. |
| `GET /api/v1/dpa/helper-tables/` | MEDIUM | Combined reference data (jurisdictions, policy areas, economic activities, event types, action types, intervention types, implementation levels, government branches). |
| `GET /api/v1/dpa/jurisdiction/` | HIGH | Individual reference endpoint |
| `GET /api/v1/dpa/policy-area/` | HIGH | Individual reference endpoint |
| `GET /api/v1/dpa/economic-activity/` | HIGH | Individual reference endpoint |
| `GET /api/v1/dpa/event-type/` | HIGH | Individual reference endpoint |
| `GET /api/v1/dpa/action-type/` | HIGH | Individual reference endpoint |
| `GET /api/v1/dpa/intervention-type/` | HIGH | Individual reference endpoint |
| `GET /api/v1/dpa/implementation-level/` | HIGH | Individual reference endpoint |

### Phase 2: DPA MCP Server Uplift

**Goal:** Bring `dpa-mcp` to feature parity with `gta-mcp`.
**Dependency:** Phase 1 endpoints must exist for new tools to call.

#### New Tools

| Tool | Priority | Description |
|---|---|---|
| `dpa_count_events` | CRITICAL | Aggregation with 15+ count dimensions |
| ~~`dpa_list_ticker_updates`~~ | N/A | Not needed -- DPA events are atomic single-date records; sorting/filtering by modification date on `dpa_search_events` covers this |
| `dpa_get_intervention` | HIGH | Get full intervention (parent of events) |
| `dpa_search_interventions` | HIGH | Search at intervention level (not just events) |
| `dpa_get_issue` | MEDIUM | Get cross-cutting policy issue details |

#### Enhanced `dpa_search_events`

| Enhancement | Priority |
|---|---|
| `affected_jurisdictions` filter | HIGH |
| `action_types` filter | HIGH |
| `intervention_types` filter (policy instruments) | HIGH |
| `binding_status` filter (binding/non-binding) | HIGH |
| `query` full-text search param with operators | HIGH |
| `detail_level` (overview/standard/full) | HIGH |
| `show_keys` response field control | MEDIUM |
| Exclusion filters (`keep_jurisdiction`, `keep_policy_area`, etc.) | HIGH |
| `date_announced_gte/lte`, `date_implemented_gte/lte`, `date_modified_gte/lte` | HIGH |
| `is_in_force` filter | MEDIUM |

#### New Resources (Guides)

| Resource URI | Priority |
|---|---|
| `dpa://guide/searching` | HIGH |
| `dpa://guide/date-fields` | HIGH |
| `dpa://guide/parameters` | HIGH |
| `dpa://guide/query-examples` | HIGH |
| `dpa://guide/query-syntax` | HIGH |
| `dpa://guide/exclusion-filters` | HIGH |
| `dpa://guide/data-model` | HIGH |
| `dpa://guide/common-mistakes` | HIGH |

### Phase 3: Authentication & Access Control

**Goal:** Wire API key auth into DPA public endpoints.
**Dependency:** Phase 1 endpoints must exist.

| Task | Priority | Notes |
|---|---|---|
| Wire `APIKeyAuthentication` into DPA public endpoints | HIGH | Reuse existing GTA auth class |
| Implement tier-based access using `is_restricted_dpa` and `dpa_delay` fields | HIGH | Model fields already exist in `APIUserPermission` |
| Add rate limiting consistent with GTA | MEDIUM | Follow GTA patterns |

---

## Critical Files Reference

### DPA Backend (Current)

| File | Purpose |
|---|---|
| `gtaapi/dpa/api/views.py` | Existing DPA ViewSets (website-serving) |
| `gtaapi/dpa/api/versions/v1.py` | DPA URL router |
| `gtaapi/dpa/api/serializers.py` | DPA serializers |
| `gtaapi/dpa/api/mixins/views.py` | DPA filter mixin (`FilterViewSetMixin`) |
| `gtaapi/core/models/dpa.py` | DPA database models |

### GTA Backend (Reference Pattern)

| File | Purpose |
|---|---|
| `gtaapi/api/urls.py` | GTA public API URLs -- pattern to follow |
| `gtaapi/api/views.py` | GTA public API views -- reference implementation |
| `gtaapi/users/api/authentication.py` | API key auth (`APIKeyAuthentication`) |

### DPA MCP Server (Current)

| File | Purpose |
|---|---|
| `sgept-mcp-servers/dpa-mcp/src/dpa_mcp/` | All 5 .py files -- current DPA MCP server |

### GTA MCP Server (Reference)

| File | Purpose |
|---|---|
| `sgept-mcp-servers/gta-mcp/src/gta_mcp/` | All 8 files -- target capability reference |

---

## Gap Summary by Priority

| Priority | Count | Items |
|---|---|---|
| **CRITICAL** | 4 | Public events endpoint, data counts endpoint, MCP search enhancement, MCP count tool |
| **HIGH** | 13 | Reference endpoints (7), auth wiring, MCP new tools (2), MCP exclusion filters, MCP date granularity, MCP guides |
| **MEDIUM** | 6 | Helper tables combined, impact chains, MCP field control, MCP sorting, MCP issue tool, rate limiting |
| **LOW** | 1 | Sync status monitoring |
| **NOT APPLICABLE** | 5 | Trade data, ClickHouse, HS code/sector lookup, ticker (backend), ticker (MCP) |

**Estimated effort:** Phase 1 (backend) is primarily wiring existing infrastructure into new URL routes -- moderate effort. Phase 2 (MCP) requires new tool implementations and guide authoring -- significant effort. Phase 3 (auth) is configuration-level work leveraging existing GTA patterns -- low effort.
