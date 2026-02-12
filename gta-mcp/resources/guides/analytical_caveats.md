# GTA Analytical Caveats

The 15 most critical caveats for interpreting GTA data correctly.

## 1. Evaluation Filter-Only Values

Values 4 (Harmful) and 5 (Liberalizing) are convenience groupings for filtering: Harmful = Red + Amber, Liberalizing = Green. Individual records always contain values 1-3 only.

## 2. Amber Is NOT Neutral

Amber means "likely discrimination but uncertain outcome." For analytical purposes, Amber is classified as harmful. All trade defence investigations (anti-dumping, countervailing, safeguard) are coded Amber until definitive duties are imposed (then Red).

## 3. India Code Anomaly

India uses GTA jurisdiction code 699, NOT the standard UN M49 code 356. The MCP server handles this via ISO code conversion (IND → 699), but agents using raw UN codes must be aware.

## 4. MAST Chapter IDs Are Non-Alphabetical

The mapping is not A=1, B=2, C=3. Actual mapping: A=1, B=2, C=17, D=4, E=5, F=6, G=8, H=18, I=9, J=19, K=20, L=10, M=11, N=13, P=14. Plus special categories: Capital controls=3, FDI=7, Migration=12, Tariffs=15, Unclear=16.

## 5. 68 Intervention Types (Not 74-79)

Historical documents cite higher counts due to deprecated/merged types. The live API has 68 contiguous values. Always use the mappings endpoint or `gta://reference/intervention-types-list` for the current list.

## 6. What's NOT in the Database

- Bilateral/multilateral agreements (only unilateral deviations from them)
- Measures before November 2008
- Financial measures below USD 10M (USD 100M for SME-targeted)
- WTO TBT-notified and SPS-notified measures
- UN Security Council sanctions and CITES measures
- Proposals, drafts, speeches (only credible/enacted actions)

## 7. One Intervention → Many Products/Sectors

A single intervention can affect hundreds of HS codes and multiple CPC sectors. When using `gta_count_interventions` with `count_by: ["sector"]`, the result is intervention-sector combinations, not unique interventions. One intervention blocking 50 steel products appears 50 times in a product-level count.

## 8. Date Semantics

- `date_announced` = when publicly disclosed (use for "what's new" monitoring)
- `date_implemented` = when legally takes effect (use for "what's active now")
- Gap can be months or years. Always specify which date you mean.
- Year-only dates default conservatively: inception → Dec 31, removal → Jan 1.

## 9. Publication Lag

Entries are created by analysts after the fact. A tariff implemented 1 January may not appear in the database until February. Recent data is always incomplete. Use overlapping scan windows for monitoring.

## 10. EU Jurisdiction Complexity

- EU Regulations → implementing jurisdiction = "European Union"
- EU Directives → each member state transposes separately
- EU State Aid decisions → implementing jurisdiction = the member state, NOT the EU

## 11. IFI/NFI Jurisdiction Assignment

When an international financial institution (World Bank, EIB, etc.) provides a loan/grant, implementing jurisdiction = beneficiary country, NOT the IFI headquarters.

## 12. Prior Level Artefact

A `prior_level` of 0 in tariff data often indicates a data entry default (artefact), not a genuine zero tariff. Exercise caution when analysing absolute tariff changes.

## 13. Trade Defence Lifecycle

Investigation initiation = Amber. Preliminary duties = Amber. Definitive duties = Red. Investigation terminated = measure removed. "Removed" status on an investigation means it progressed to the next stage, not that it was revoked.

## 14. Direction Determines Evaluation

A tariff at 10% is neither Red nor Green inherently. Evaluation depends on comparison with prior level: up from 5% = Red, down from 15% = Green. This is why the `prior_level` and `new_level` fields in full-access responses are analytically critical.

## 15. Affected Jurisdiction Types

Affected jurisdictions include: Inferred (auto-calculated from trade data, > USD 1M threshold), Targeted (explicitly named), Excluded (explicitly exempted), and Incidental (firm-specific context). Inferred jurisdictions are periodically recalculated and may change.
