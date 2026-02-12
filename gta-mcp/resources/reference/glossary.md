# GTA Glossary

Key terms and concepts for understanding Global Trade Alert data.

---

## Intervention

A single trade policy measure documented in the GTA database. Each intervention has a unique ID, an evaluation (Red/Amber/Green), implementing and affected jurisdictions, and dates. Example: "United States imposes 25% tariff on Chinese steel imports" is one intervention. When searching or counting trade measures, you are working with interventions.

---

## State Act

A government action or announcement that may contain one or more interventions. When a government announces a package of trade measures, GTA records it as one state act containing multiple interventions. Example: A presidential executive order imposing tariffs on multiple product categories from several countries creates one state act with several interventions (one per product-country combination with distinct evaluations).

---

## Red Evaluation

The GTA assessment that a trade measure is harmful or discriminatory. Red means the measure almost certainly discriminates against foreign commercial interests. Examples include new import tariffs, export bans, discriminatory subsidies, and definitive trade defence duties. Red is the most severe evaluation and indicates clear protectionism.

---

## Amber Evaluation

The GTA assessment that a trade measure is likely harmful but the outcome is uncertain. Amber covers measures where discrimination is probable but not yet confirmed. All trade defence investigations (anti-dumping, countervailing duty, safeguard) start as Amber until definitive duties are imposed, at which point they become Red. Amber also includes measures with unclear effects or incomplete information.

---

## Green Evaluation

The GTA assessment that a trade measure is liberalising — it improves foreign commercial interests. Examples include tariff reductions, removal of import quotas, new trade agreements, and investment liberalisation. Green measures make it easier or more attractive for foreign businesses to operate in the implementing jurisdiction.

---

## Harmful (Evaluation Filter)

A convenience grouping used in search filters that combines Red and Amber evaluations. When filtering by `gta_evaluation: [4]` or `gta_evaluation: ["Harmful"]`, you get both Red and Amber interventions. Individual intervention records never contain the value 4 — they are always 1 (Red), 2 (Amber), or 3 (Green). This filter is useful for "how much protectionism" queries.

---

## MAST Chapters

The Multilateral Agreement on Services and Trade classification system (chapters A through P) that groups trade measures into broad policy categories. Examples: Chapter D = Anti-dumping measures, Chapter E = Subsidies (including grants and state loans), Chapter L = Subsidies other than export subsidies. Use MAST chapters for broad queries like "all subsidies" or "all trade defence measures". The ID mapping is non-alphabetical: A=1, B=2, C=17, D=4, E=5, etc.

---

## HS Code (Harmonised System)

The international product classification system using 6-digit numeric codes. HS codes identify specific goods (not services). Example: 854110 = semiconductor diodes, 720711 = semi-finished steel products. When filtering interventions by `affected_products`, use HS codes as integers (e.g., `[854110, 720711]`). For services, use CPC sectors instead.

---

## CPC Sector (Central Product Classification)

A broader product classification system that covers both goods and services, using 3-digit codes. CPC sectors are less granular than HS codes but include services (financial services, telecommunications, transport, etc.) which HS codes do not cover. Use CPC sectors for services-related queries or broad sector-level analysis. Use HS codes for specific goods at the product level.

---

## Implementing Jurisdiction

The country, customs territory, or international body that enacted the trade measure. Example: if the European Commission imposes an anti-dumping duty, the implementing jurisdiction is "European Union". If a US state imposes a procurement restriction, the implementing jurisdiction is "United States" at the subnational level. GTA always records the final governmental implementer, not merely the announcing body.

---

## Affected Jurisdiction

The country or countries whose commercial interests are harmed (or helped) by the trade measure. GTA identifies affected jurisdictions through several methods: Targeted (explicitly named in the measure), Inferred (calculated from trade data where bilateral trade exceeds USD 1 million), Excluded (explicitly exempted from the measure), and Incidental (affected through firm-specific targeting). A single intervention can affect dozens of jurisdictions.

---

## Implementation Level

The level of government that enacted the measure. Options: Supranational (e.g., EU Commission), National (central government or central bank), Subnational (state, provincial, or municipal), SEZ (Special Economic Zone authority), IFI (International Financial Institution like World Bank), or NFI (National Financial Institution like an export-import bank). GTA always records the final governmental implementer, not the announcing body.

---

## Eligible Firms

Which types of businesses are targeted by the intervention. Categories: all (universal policy), SMEs (small and medium enterprises), firm-specific (named company, e.g., Huawei sanctions), state-controlled (state-owned enterprises), sector-specific (all firms in an industry), location-specific (firms in a particular region), or processing trade (firms engaged in import-for-re-export). This helps distinguish broad policies from targeted interventions.

---

## In Force

A measure that is currently legally active and binding. Measures that have been removed, expired, or revoked are no longer in force. Filter with `is_in_force: true` to see only currently active measures. Note that GTA records historical measures indefinitely, so always filter by force status when asking "what's active now".

---

## Publication Lag

The delay between when a trade measure is announced or implemented and when it appears in the GTA database. GTA entries are created by analysts after the fact, so a tariff implemented on 1 January may not appear until February or later. Recent data is always incomplete. For monitoring tasks, use overlapping scan windows to avoid missing entries that arrive late.

---

## Date Announced vs Date Implemented

Two key dates for every intervention. `date_announced` is when the measure was publicly disclosed. `date_implemented` is when it legally takes effect. The gap can be months or years (e.g., a tariff announced in April implemented in October). For "what's new" queries, use `date_announced`. For "what's active now" queries, use `date_implemented`. When only a year is known, GTA defaults conservatively: implementation defaults to 31 December, removal defaults to 1 January.

---

## Ticker

A feed of recently modified or newly added interventions in the GTA database. Use the ticker to monitor what's changed — new entries, updated descriptions, or revised evaluations. Accessed via the `gta_list_ticker_updates` tool. The ticker shows all database activity (new interventions, updates to existing records, evaluation changes), not just brand-new measures.

---

## Trade Defence

A category of measures where governments protect domestic industries from foreign competition. Three types: anti-dumping duties (against imports sold below cost), countervailing duties (against subsidised imports), and safeguard measures (against import surges). In GTA, trade defence investigations are coded Amber until definitive duties are imposed (then Red). "Removed" status on an investigation means it progressed to the next stage (provisional or definitive duties), not that it was revoked.

---
