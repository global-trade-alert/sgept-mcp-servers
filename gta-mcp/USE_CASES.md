# GTA MCP Server — Use Cases

Example prompts you can copy-paste into Claude. Each prompt works out of the box with the GTA MCP server.

## How to use this guide

Pick a category that matches your work. Copy a prompt, paste it into Claude, and adapt it to your specific question. Claude will use the GTA database to find relevant trade policy interventions.

---

## 1. Tariff Escalation and Retaliation

**Persona:** You're tracking tariff wars, retaliatory measures, or Section 232/301 actions.

**Prompt:** "What tariffs has the United States imposed on China since January 2025?"

Uses `gta_search_interventions` with country and date filters. Returns a list of interventions with titles, dates, and GTA links.

**Prompt:** "Which countries have imposed tariffs affecting US exports in 2025?"

Uses `gta_search_interventions` with `affected_jurisdictions: ['USA']` and date filter. Note: GTA has no "retaliation" concept — results show all measures affecting the US, not just retaliatory ones. You will need to interpret which measures are responses to US actions.

**Prompt:** "What Section 232 measures has the US implemented since 2025?"

Uses text search (`query: "Section 232"`) combined with `implementing_jurisdictions: ['USA']`. Note: text search may not capture all relevant measures — some Section 232 tariffs may be recorded by product rather than legal provision. Combine with structured filters (intervention type: "Import tariff") for comprehensive coverage.

**Prompt:** "Show me all tariffs imposed by the EU on US goods in the last 12 months"

Filters interventions by implementing jurisdiction (EU), affected country (US), measure type (tariffs), and date range.

**Prompt:** "What tariffs has China imposed affecting US exports since 2018?"

Uses `gta_search_interventions` with `implementing_jurisdictions: ['CHN']`, `affected_jurisdictions: ['USA']`, and tariff type filter. To identify measures that may be retaliatory, review the intervention descriptions and dates — GTA records measures neutrally without characterising them as retaliation.

## 2. Critical Minerals and Supply Chain Risks

**Persona:** You're monitoring export controls, resource nationalism, or supply chain vulnerabilities.

**Prompt:** "What export controls has China imposed on rare earth elements?"

Uses `gta_search_interventions` with `implementing_jurisdictions: ['CHN']` and `mast_chapters: ['P']` (export-related measures). Note: MAST chapter P alone returns all Chinese export measures. To narrow to rare earth elements specifically, add `query: "rare earth"` or provide specific HS codes. Without product-level filtering, results will be over-inclusive.

**Prompt:** "Which countries have restricted exports of lithium or cobalt since 2022?"

Searches for export bans, quotas, or licensing requirements affecting critical battery materials.

**Prompt:** "What measures currently affect semiconductor manufacturing equipment trade?"

Filters interventions by sector (semiconductors) and measure type (export controls, trade defence, FDI screening).

**Prompt:** "Show me all export restrictions on graphite imposed globally since 2020"

Searches for interventions with "graphite" in the product description and "export" in the measure type.

**Prompt:** "What local content requirements affect battery production in Indonesia?"

Filters for Indonesian interventions targeting local content or domestic sourcing requirements in the battery sector.

## 3. Subsidies and State Aid

**Persona:** You're researching government support for domestic industries or competitive subsidy intelligence.

**Prompt:** "What subsidies are governments providing for critical mineral processing?"

Uses `gta_search_interventions` filtered for subsidy measures (state loans, financial grants, tax breaks) in the mining and processing sectors.

**Prompt:** "Which countries subsidise their domestic semiconductor industry?"

Searches for subsidy interventions in the semiconductor sector, grouped by implementing country.

**Prompt:** "Which G20 countries have increased state aid to EV manufacturers since 2022?"

Filters interventions by implementing jurisdiction (G20 members), sector (automotive), measure type (subsidies), and date.

**Prompt:** "What financial grants has the EU provided to green steel producers?"

Searches for EU subsidy interventions targeting the steel sector with "green" or "decarbonisation" in descriptions.

**Prompt:** "Show me all state loans provided by China to its semiconductor firms since 2020"

Filters for Chinese subsidy interventions in semiconductors, specifically state loans and credit guarantees.

## 4. Bilateral and Regional Trade Relations

**Persona:** You're preparing for trade negotiations or analysing bilateral trade barriers.

**Prompt:** "What harmful measures has the EU imposed on US exports since 2024?"

Uses `gta_search_interventions` with EU as implementing country, US as affected, and evaluation filter. Use `gta_evaluation: ['Harmful']` to include both Red (confirmed harmful) and Amber (likely harmful) measures — Amber includes pending trade defence investigations that may escalate.

**Prompt:** "What measures has Brazil implemented affecting US agricultural exports?"

Filters for Brazilian interventions targeting the US. To narrow to agricultural products specifically, add `affected_sectors` with agricultural CPC codes (e.g., 11-49 for primary agriculture) or relevant HS codes. Without sector filtering, results include all Brazilian measures affecting the US.

**Prompt:** "Compare trade barriers imposed by ASEAN members on EU services"

Searches for harmful interventions by ASEAN countries affecting the EU. To filter for services specifically, add `affected_sectors` with CPC sectors >= 500 (e.g., 711 for financial services, 841 for telecommunications). Without explicit sector filtering, results include all measure types.

**Prompt:** "What import restrictions does India impose on Swiss pharmaceutical products?"

Filters for Indian interventions affecting Switzerland in the pharmaceutical sector.

**Prompt:** "Show me all measures China has implemented affecting Australian mineral exports since 2020"

Searches for Chinese interventions targeting Australia in the mining sector, filtered by implementation date.

## 5. Trade Defence (Anti-Dumping, Safeguards, Anti-Subsidy)

**Persona:** You're building a trade remedy case or researching defence measures.

**Prompt:** "Find all anti-dumping investigations targeting Chinese steel since 2020"

Uses `gta_search_interventions` filtered for anti-dumping measures affecting China in the steel sector.

**Prompt:** "What safeguard measures are currently in force on solar panels?"

Uses `gta_search_interventions` with `is_in_force: true` to filter for active measures only. Without this filter, expired measures will also appear. Note: "Removed" status on a trade defence investigation means it progressed to definitive duties (a separate entry), not that it was dropped.

**Prompt:** "Which countries have initiated anti-dumping cases against EU steel exports in 2025?"

Filters interventions by measure type (anti-dumping), affected country (EU countries), and sector (steel).

**Prompt:** "Show me all countervailing duty investigations on subsidised Chinese products since 2023"

Searches for countervailing duty measures affecting China, implemented since 2023.

**Prompt:** "What safeguard measures has India imposed on imports in the last two years?"

Filters for Indian interventions classified as safeguards, with date range covering 2024-2026.

## 6. Regulatory and Non-Tariff Barriers

**Persona:** You're tracking non-tariff barriers like licensing requirements, local content rules, or public procurement restrictions.

**Prompt:** "What local content requirements affect automotive production in Southeast Asia?"

Uses `gta_search_interventions` with `intervention_types: ['Local content requirement']` and major Southeast Asian auto-producing countries (Indonesia, Thailand, Vietnam, Malaysia, Philippines). Results include all local content requirements in these countries, not just automotive. For automotive-specific results, add `query: "automotive"` or `affected_sectors` with vehicle CPC codes.

**Prompt:** "What import licensing requirements affect pharmaceutical products in India?"

Searches for Indian interventions involving import licences or quotas in the pharmaceutical sector.

**Prompt:** "What public procurement restrictions favour domestic bidders in the US?"

Filters for US interventions involving procurement rules, including Buy American provisions.

## 7. Monitoring and Aggregation

**Persona:** You need trend data, counts, or year-over-year comparisons.

**Prompt:** "Has the use of export restrictions increased since 2020?"

Uses `gta_count_interventions` to count export restrictions year-by-year from 2020 to present, enabling trend analysis.

**Prompt:** "How many harmful interventions were implemented globally in 2025 versus 2024?"

Uses `gta_count_interventions` with `gta_evaluation: ['Harmful']` (Red + Amber) for both years. Note: recent data is always incomplete due to 2-4 week publication lag — treat the most recent month's counts as preliminary. When counting by `date_implemented`, a potentially large group of interventions with "No implementation date" will appear — these are real measures that lack a known implementation date. For more complete counts, consider counting by `date_announced` instead.

**Prompt:** "What is the trend in subsidy measures implemented by the US since 2020?"

Counts US subsidy interventions by year to show whether state aid is increasing or decreasing.

**Prompt:** "How many interventions currently affect the semiconductor sector globally?"

Uses `gta_count_interventions` filtered by sector. Important: when counting by sector, one intervention affecting multiple sectors is counted once per sector — the result shows intervention-sector combinations, not unique interventions. Add `is_in_force: true` to count only currently active measures.

**Prompt:** "Compare the number of trade defence cases initiated by the EU and US in 2024"

Counts anti-dumping, safeguard, and countervailing measures for both jurisdictions in the specified year.

## 8. Advanced and Cross-Cutting Queries

**Persona:** You need complex multi-filter queries, firm-level targeting, or subnational data.

**Prompt:** "Which interventions target state-owned enterprises specifically?"

Uses `gta_search_interventions` with `eligible_firms: ['state-controlled']` to find measures specifically targeting state-owned enterprises. This is more reliable than text search, as GTA classifies eligible firm types for each intervention.

**Prompt:** "What subnational measures has the US implemented since 2023?"

Uses `gta_search_interventions` with `implementing_jurisdictions: ['USA']`, `implementation_levels: ['subnational']`, and date filter. This filters for measures implemented at sub-federal levels (state, municipal, etc.).

**Prompt:** "Show me all measures affecting both semiconductors and rare earth elements"

Filters interventions that impact multiple sectors simultaneously, useful for supply chain analysis.

**Prompt:** "What FDI screening measures target Chinese investments in European technology sectors?"

Searches for EU-member interventions involving investment restrictions, affecting China, in technology sectors.

**Prompt:** "Find all interventions that mention 'national security' justifications since 2022"

Uses text search in descriptions to find interventions citing security rationales, regardless of sector.

**Prompt:** "What measures have G7 countries coordinated against Russia since February 2022?"

Filters interventions by implementing jurisdiction (G7), affected country (Russia), and date, to identify coordinated actions.
