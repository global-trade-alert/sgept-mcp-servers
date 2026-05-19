# Query Intent Mapping Guide

When translating natural language questions into GTA API calls, map analytical concepts to structured filters **before** falling back to the `query` parameter.

---

## Policy Type to MAST Chapter

| Natural language term | MAST chapter | API value | Notes |
|-----------------------|-------------|-----------|-------|
| subsidies, state aid, grants, financial support, incentives | L - Subsidies | `mast_chapters=['L']` | Broadest subsidy category |
| tariffs, customs duties, import duties | D - Contingent trade-protective measures | `intervention_types=['Import tariff']` | Or use specific type |
| export controls, export restrictions, export bans | P - Export-related measures | `mast_chapters=['P']` | Covers bans, licensing, taxes |
| import quotas, import licensing, quantitative restrictions | E - Non-automatic licensing, quotas | `mast_chapters=['E']` | |
| anti-dumping, countervailing duties, safeguards | D - Contingent trade-protective measures | `mast_chapters=['D']` | Trade defence instruments |
| investment restrictions, FDI screening, investment controls | I - Investment measures | `mast_chapters=['I']` | |
| local content requirements, localisation, domestic content | E - Non-automatic licensing, quotas | `intervention_types=['Local content requirement']` | Specific type under MAST E |
| procurement, government purchasing, buy national | M - Government procurement | `mast_chapters=['M']` | |
| technical barriers, standards, certification | B - Technical barriers to trade | `mast_chapters=['B']` | |
| sanitary, phytosanitary, food safety, SPS | A - Sanitary and phytosanitary | `mast_chapters=['A']` | |
| intellectual property, patents, IP protection | N - Intellectual property | `mast_chapters=['N']` | |
| price controls, reference prices, minimum prices | F - Price-control measures | `mast_chapters=['F']` | |
| competition policy, antitrust, merger control | H - Measures affecting competition | `mast_chapters=['H']` | |

---

## Evaluation Terms

| Natural language term | API filter | Notes |
|-----------------------|-----------|-------|
| harmful, restrictive, protectionist, barriers | `gta_evaluation=['Harmful']` | Expands to Red + Amber |
| liberalising, liberalizing, opening, facilitating | `gta_evaluation=['Green']` | |
| certainly harmful, clearly discriminatory | `gta_evaluation=['Red']` | Red only |
| likely harmful, probably discriminatory | `gta_evaluation=['Amber']` | Amber only |
| imposed (implies harmful in context) | `gta_evaluation=['Harmful']` | When used with trade barriers |

---

## Sector/Product Terms to HS Codes

For commodity-specific queries, use `gta_lookup_hs_codes` to find exact codes. Common mappings:

| Natural language term | HS chapters/codes | How to use |
|-----------------------|-------------------|------------|
| agriculture, agricultural, food, farming | Chapters 01-24 | `gta_lookup_hs_codes` search or `affected_products` with chapter codes |
| automotive, vehicles, cars | Chapter 87 | `gta_lookup_hs_codes` with "vehicle" |
| steel, iron and steel | Chapter 72-73 | `gta_lookup_hs_codes` with "steel" |
| semiconductors, chips, microprocessors | HS 8541, 8542 | `gta_lookup_hs_codes` with "semiconductor" |
| solar panels, photovoltaic | HS 854140 | `gta_lookup_hs_codes` with "photovoltaic" |
| pharmaceuticals, medicines, drugs | Chapter 30 | `gta_lookup_hs_codes` with "pharmaceutical" |
| textiles, clothing, apparel | Chapters 50-63 | `gta_lookup_hs_codes` with "textile" |
| critical minerals, rare earths | Various (multiple chapters) | `gta_lookup_hs_codes` with specific mineral name |
| lithium | HS 282520, 283691 | `gta_lookup_hs_codes` with "lithium" |
| cobalt | HS 810520 | `gta_lookup_hs_codes` with "cobalt" |
| nickel | Chapter 75 | `gta_lookup_hs_codes` with "nickel" |

**Important:** For commodities spanning multiple HS codes, always use `gta_lookup_hs_codes` to find the complete set rather than relying on free-text `query`.

---

## Service Sectors to CPC Codes

For services queries, use `gta_lookup_sectors` to find CPC codes. Common mappings:

| Natural language term | CPC codes | How to use |
|-----------------------|-----------|------------|
| financial services, banking | CPC 71x | `gta_lookup_sectors` with "financial" |
| telecommunications, telecom | CPC 841-842 | `gta_lookup_sectors` with "telecom" |
| digital services, data services | CPC 843 | `gta_lookup_sectors` with "data" |
| transport, shipping, logistics | CPC 65x | `gta_lookup_sectors` with "transport" |
| construction | CPC 54x | `gta_lookup_sectors` with "construction" |
| education | CPC 92x | `gta_lookup_sectors` with "education" |
| health, healthcare | CPC 93x | `gta_lookup_sectors` with "health" |

**Remember:** CPC sectors with ID >= 500 are services; ID < 500 are goods.

---

## Geographic Group Terms

| Natural language term | Filter | Reference |
|-----------------------|--------|-----------|
| G7 countries | `implementing_jurisdictions=['CAN','FRA','DEU','ITA','JPN','GBR','USA']` | gta://reference/jurisdiction-groups |
| G20 countries | See full list in jurisdiction-groups resource | gta://reference/jurisdiction-groups |
| EU, European Union (as bloc) | `implementing_jurisdictions=['EUN']` | UN code 1049 |
| EU member states | Full EU-27 ISO list | gta://reference/jurisdiction-groups |
| European (broad) | EU-27 + GBR + NOR + CHE + ISL | Consider context |
| BRICS | `implementing_jurisdictions=['BRA','RUS','IND','CHN','ZAF']` | Original 5 |
| ASEAN, Southeast Asia | Full ASEAN-10 ISO list | gta://reference/jurisdiction-groups |
| CPTPP members | Full CPTPP-12 ISO list | gta://reference/jurisdiction-groups |

---

## Temporal Terms

| Natural language term | Filter | Notes |
|-----------------------|--------|-------|
| since {year}, from {year} | `date_announced_gte='{year}-01-01'` | Use announcement date for "new" measures |
| in {year} | `date_announced_gte='{year}-01-01'`, `date_announced_lte='{year}-12-31'` | Bounded range |
| currently in force, active, still in effect | `is_in_force=true` | |
| recently, latest, new | `date_announced_gte` with recent date | |
| implemented in {year} | `date_implemented_gte`, `date_implemented_lte` | Use implementation dates |
| removed, expired, revoked | `is_in_force=false` | Or use date_removed filters |

---

## Multi-Concept Queries

Complex questions often combine multiple dimensions. Map each concept independently:

**Example:** "Which G20 countries have increased state aid to EV manufacturers since 2022?"
- "G20 countries" -> `implementing_jurisdictions` with G20 list (from jurisdiction-groups)
- "state aid" -> `mast_chapters=['L']`
- "EV manufacturers" -> `query='electric vehicle'` (or use `gta_lookup_hs_codes` for specific HS codes)
- "since 2022" -> `date_announced_gte='2022-01-01'`

**Example:** "What harmful measures has the EU imposed on US exports since 2024?"
- "harmful" -> `gta_evaluation=['Harmful']`
- "EU" -> `implementing_jurisdictions=['EUN']`
- "US exports" -> `affected_jurisdictions=['USA']`
- "since 2024" -> `date_announced_gte='2024-01-01'`

**Example:** "Which countries have restricted exports of lithium or cobalt since 2022?"
- "restricted exports" -> `mast_chapters=['P']`
- "lithium or cobalt" -> First use `gta_lookup_hs_codes` for each, then `affected_products=[282520, 283691, 810520, ...]`
- "since 2022" -> `date_announced_gte='2022-01-01'`

---

## Decision Flow

```
User question
    |
    +-- Contains policy type term? ---> Map to MAST chapter or intervention_type
    |
    +-- Contains evaluation term? ----> Map to gta_evaluation
    |
    +-- Contains commodity/product? --> Use gta_lookup_hs_codes for HS codes
    |
    +-- Contains service sector? -----> Use gta_lookup_sectors for CPC codes
    |
    +-- Contains country group? ------> Look up in gta://reference/jurisdiction-groups
    |
    +-- Contains specific country? ---> Map ISO code via gta://reference/jurisdictions
    |
    +-- Contains time reference? -----> Map to date filters
    |
    +-- Remaining entity names? ------> ONLY NOW use query parameter
```

**The `query` parameter is the tool of LAST resort**, not first resort. Every concept that maps to a structured filter should use that filter.
