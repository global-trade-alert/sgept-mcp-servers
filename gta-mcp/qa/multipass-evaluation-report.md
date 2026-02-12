# Multi-Pass Workflow Evaluation Report

**Generated:** 2026-02-12 20:33:49
**API endpoint:** `https://api.globaltradealert.org/api/v2/gta/data/`
**Overview keys:** 8 fields
**Standard keys:** 18 fields

## Summary

| # | Prompt | Type | Pass 1 Results | Pass 1 Size | Pass 2 OK | Verdict |
|---|--------|------|----------------|-------------|-----------|---------|
| 1 | What tariffs has the US imposed on China since Jan 2025... | search | 71 | 34.4 KB | Yes | OK |
| 2 | Which countries have imposed tariffs affecting US expor... | search | 500 | 246.8 KB | Yes | OK |
| 3 | What export controls has China imposed on rare earth el... | search | 36 | 15.7 KB | Yes | OK |
| 4 | Which countries have restricted exports of lithium or c... | search | 0 | 0.0 KB | N/A (0 results) | No results |
| 5 | What measures currently affect semiconductor manufactur... | search | 500 | 249.7 KB | Yes | OK |
| 6 | What subsidies are governments providing for critical m... | search | 191 | 88.7 KB | Yes | OK |
| 7 | Which countries subsidise their domestic semiconductor ... | search | 500 | 249.7 KB | Yes | OK |
| 8 | Which G20 countries have increased state aid to EV manu... | search | 391 | 181.3 KB | Yes | OK |
| 9 | What harmful measures has the EU imposed on US exports ... | search | 412 | 309.3 KB | Yes | OK |
| 10 | What measures has Brazil implemented affecting US agric... | search | 500 | 227.8 KB | Yes | OK |
| 11 | Find all anti-dumping investigations targeting Chinese ... | search | 98 | 58.7 KB | Yes | OK |
| 12 | What safeguard measures are currently in force on solar... | search | 2 | 0.9 KB | Yes | OK |
| 13 | What local content requirements affect automotive produ... | search | 47 | 21.3 KB | Yes | OK |
| 14 | What import licensing requirements affect pharmaceutica... | search | 1 | 0.4 KB | Yes | OK |
| 15 | Has the use of export restrictions increased since 2020... | count | 20 groups | - | - | OK |
| 16 | How many harmful interventions were implemented globall... | count_pair | 2025: 6; 2024: 6 | - | - | OK |
| 17 | Which interventions target state-owned enterprises spec... | search | 158 | 70.7 KB | Yes | OK |
| 18 | What subnational measures has the US implemented since ... | search | 355 | 176.9 KB | Yes | OK |
| 19 | What FDI screening measures target Chinese investments ... | search | 5 | 3.5 KB | Yes | OK |
| 20 | What measures have G7 countries coordinated against Rus... | search | 500 | 390.0 KB | Yes | OK |

## Per-Prompt Details

### Prompt 1: What tariffs has the US imposed on China since Jan 2025?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 71 interventions
- Response size: 34.4 KB (35,205 bytes)
- Elapsed: 801 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - United States of America: Reclassification of certain vehicles for transport of goods and consequent increase in MFN Duty
  - United States of America: Reclassification of decorative storage baskets and consequent increase in MFN Duty
  - United States of America: Reclassification of underwater remotely-operated vehicles and consequent increase in MFN Duty
  - United States of America: Reclassification of certain spa covers and spa cover lifters and consequent decrease in MFN duty
  - United States of America: Reclassification of men’s outerwear jackets from China and consequent decrease in MFN duty

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [152110, 148999, 145040, 144298, 142485]
- IDs returned: [142485, 144298, 145040, 148999, 152110]
- All IDs present: Yes
- Num returned: 5
- Response size: 29.6 KB
- Elapsed: 240 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 142485):
  - Title: United States of America: Reclassification of a men’s vest and consequent modification in the MFN duties
  - Type: Import tariff
  - Evaluation: Red
  - Date announced: 2025-01-08
  - In force: 1

**Multi-pass value:** Prompt returned 71 results vs old ceiling of 50. Overview pass reveals 42% more data.

---

### Prompt 2: Which countries have imposed tariffs affecting US exports in 2025?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 500 interventions
- Response size: 246.8 KB (252,752 bytes)
- Elapsed: 901 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - Mexico: Removal of several products from the "basic basket" products list temporarily exempted from import duties (December 2025)
  - Brazil: Modification of import tariff-rate quotas and import duties for 15 products (December 2025)
  - Iraq: Government implements new customs tariffs on hybrid vehicles and gold starting from 1 January 2026
  - EU: Changes to the list of agricultural and industrial products subject to a reduction of import duties (December 2025)
  - EU: Changes to the list of agricultural and industrial products subject to a reduction of import duties (December 2025)

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [151413, 150651, 148496, 145773, 144207]
- IDs returned: [144207, 145773, 148496, 150651, 151413]
- All IDs present: Yes
- Num returned: 5
- Response size: 10.0 KB
- Elapsed: 170 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 144207):
  - Title: Vietnam: Government reduces import tariff rates on certain products in response to geopolitical developments
  - Type: Import tariff
  - Evaluation: Green
  - Date announced: 2025-03-31
  - In force: 1

**Multi-pass value:** Prompt returned 500 results vs old ceiling of 50. Overview pass reveals 900% more data.

---

### Prompt 3: What export controls has China imposed on rare earth elements?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 36 interventions
- Response size: 15.7 KB (16,042 bytes)
- Elapsed: 287 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - China: Government grants export license to Ningbo Jintian Copper
  - China: Government grants rare earth export license to several Chinese companies
  - China: Temporary suspension of additional export controls for rare earth-related technologies and  foreign entities that export Chinese-origin rare-earth materials
  - China: Temporary suspension of additional export controls for rare earth-related technologies and  foreign entities that export Chinese-origin rare-earth materials
  - China: Chinese commitments under a trade and economic agreement with the US (October 2025)

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [151266, 149796, 20137, 20170, 20166]
- IDs returned: [20137, 20166, 20170, 149796, 151266]
- All IDs present: Yes
- Num returned: 5
- Response size: 16.7 KB
- Elapsed: 199 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 20137):
  - Title: China: Government approves the second batch of export quotas on rare earth metals for 2013
  - Type: Export quota
  - Evaluation: Red
  - Date announced: 2013-06-18
  - In force: 0

**Multi-pass value:** Only 36 results (within old 50-result ceiling). Overview mode still useful for compact triage at 15.7 KB.

---

### Prompt 4: Which countries have restricted exports of lithium or cobalt since 2022?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 0 interventions
- Response size: 0.0 KB (2 bytes)
- Elapsed: 463 ms
- Keys returned: []

**Pass 2:** Skipped (no results from Pass 1)

**Multi-pass value:** No results returned -- query may be too narrow.

---

### Prompt 5: What measures currently affect semiconductor manufacturing equipment trade?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 500 interventions
- Response size: 249.7 KB (255,701 bytes)
- Elapsed: 836 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - United States of America (Texas): USD 14.1 million grant to Coherent Corp under Texas Semiconductor Innovation Fund
  - China: Government reportedly allows several Chinese firms to import of Nvidia H200 AI chips
  - Republic of Korea: Eximbank announces KRW 22 trillion program to support AI industry
  - Republic of Korea: Eximbank announces KRW 22 trillion program to support AI industry
  - United Kingdom: British Business Bank commits GBP 50 million to IQ Capital Fund V for deeptech investments

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [152717, 142858, 138004, 129504, 107530]
- IDs returned: [107530, 129504, 138004, 142858, 152717]
- All IDs present: Yes
- Num returned: 5
- Response size: 21.0 KB
- Elapsed: 131 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 107530):
  - Title: United States of America: U.S. Administration enacts the CHIPS and Science Act of 2022
  - Type: State aid, unspecified
  - Evaluation: Red
  - Date announced: 2022-08-09
  - In force: 1

**Multi-pass value:** Prompt returned 500 results vs old ceiling of 50. Overview pass reveals 900% more data.

---

### Prompt 6: What subsidies are governments providing for critical mineral processing?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 191 interventions
- Response size: 88.7 KB (90,781 bytes)
- Elapsed: 408 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - United States of America: EXIM approves loan to establish a Strategic Critical Minerals Reserve
  - Australia: National Reconstruction Fund Corporation (NRFC) invests AUD 75 million to Alpha HPA
  - United Kingdom: National Wealth Fund releases its five-year strategic plan
  - Canada: Canada Growth Fund Provides USD 25 million in funding to Cyclic Materials
  - United States of America: "SECURE Minerals Act of 2026 " introduced in Congress

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [152570, 142715, 136228, 116666, 88906]
- IDs returned: [88906, 116666, 136228, 142715, 152570]
- All IDs present: Yes
- Num returned: 5
- Response size: 13.8 KB
- Elapsed: 165 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 88906):
  - Title: Germany: Introduction of state loan and financial grant scheme to support critical minerals sector
  - Type: Financial grant
  - Evaluation: Red
  - Date announced: 2012-10-03
  - In force: 0

**Multi-pass value:** Prompt returned 191 results vs old ceiling of 50. Overview pass reveals 282% more data.

---

### Prompt 7: Which countries subsidise their domestic semiconductor industry?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 500 interventions
- Response size: 249.7 KB (255,701 bytes)
- Elapsed: 880 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - United States of America (Texas): USD 14.1 million grant to Coherent Corp under Texas Semiconductor Innovation Fund
  - China: Government reportedly allows several Chinese firms to import of Nvidia H200 AI chips
  - Republic of Korea: Eximbank announces KRW 22 trillion program to support AI industry
  - Republic of Korea: Eximbank announces KRW 22 trillion program to support AI industry
  - United Kingdom: British Business Bank commits GBP 50 million to IQ Capital Fund V for deeptech investments

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [152717, 142858, 138004, 129504, 107530]
- IDs returned: [107530, 129504, 138004, 142858, 152717]
- All IDs present: Yes
- Num returned: 5
- Response size: 21.0 KB
- Elapsed: 133 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 107530):
  - Title: United States of America: U.S. Administration enacts the CHIPS and Science Act of 2022
  - Type: State aid, unspecified
  - Evaluation: Red
  - Date announced: 2022-08-09
  - In force: 1

**Multi-pass value:** Prompt returned 500 results vs old ceiling of 50. Overview pass reveals 900% more data.

---

### Prompt 8: Which G20 countries have increased state aid to EV manufacturers since 2022?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 391 interventions
- Response size: 181.3 KB (185,680 bytes)
- Elapsed: 632 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - Canada: New measures to support the automobile industry
  - Canada: New measures to support the automobile industry
  - Russia: Industry Development Fund discloses a RUB 8.2 billion loan to Avtotor
  - Australia: National Reconstruction Fund Corporation (NRFC) invests AUD 30.7 million to Applied Electric Vehicles
  - United Kingdom: National Wealth Fund releases its five-year strategic plan

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [152705, 139988, 130042, 116184, 101010]
- IDs returned: [101010, 116184, 130042, 139988, 152705]
- All IDs present: Yes
- Num returned: 5
- Response size: 9.5 KB
- Elapsed: 130 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 101010):
  - Title: Hungary: Introduction of EUR 24 million measure to support Volta Energy Solutions
  - Type: Financial grant
  - Evaluation: Red
  - Date announced: 2022-01-07
  - In force: 1

**Multi-pass value:** Prompt returned 391 results vs old ceiling of 50. Overview pass reveals 682% more data.

---

### Prompt 9: What harmful measures has the EU imposed on US exports since 2024?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 412 interventions
- Response size: 309.3 KB (316,729 bytes)
- Elapsed: 801 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - EU: Action plan on drone and counter-drone security to support the development of homegrown technologies
  - Italy: EUR 390 million rescue loan to Acciaierie d'Italia
  - Germany: EUR 3 billion state aid scheme for cleantech manufacturing capacity
  - Germany: EUR 3 billion state aid scheme for cleantech manufacturing capacity
  - Germany: EUR 3 billion state aid scheme for cleantech manufacturing capacity

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [152737, 150785, 115979, 138596, 131859]
- IDs returned: [115979, 131859, 138596, 150785, 152737]
- All IDs present: Yes
- Num returned: 5
- Response size: 14.7 KB
- Elapsed: 131 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 115979):
  - Title: Germany: EUR 920 million grant to support Infineon Technologies AG's construction project of a semiconductor and integrated circuit factory
  - Type: Financial grant
  - Evaluation: Red
  - Date announced: 2025-02-20
  - In force: 1

**Multi-pass value:** Prompt returned 412 results vs old ceiling of 50. Overview pass reveals 724% more data.

---

### Prompt 10: What measures has Brazil implemented affecting US agricultural exports?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 500 interventions
- Response size: 227.8 KB (233,222 bytes)
- Elapsed: 637 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - Brazil: Modifications of the import tariff of 1'249 products under the LEBIT/BK list (February 2026)
  - Brazil: Modifications of the import tariff of 1'249 products under the LEBIT/BK list (February 2026)
  - Brazil: BNDES and WEG sign loan to renovate and build a factory for battery energy storage systems in Itajaí
  - Brazil: Modification of in-quota volume for electric motors (February 2026)
  - Brazil: Changes to import duties and import tariff-rate quotas for multiple products (January 2026)

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [152527, 146600, 140661, 136190, 121951]
- IDs returned: [121951, 136190, 140661, 146600, 152527]
- All IDs present: Yes
- Num returned: 5
- Response size: 15.2 KB
- Elapsed: 135 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 121951):
  - Title: Brazil: Removal of several products from the capital goods and IT and telecommunications Ex-Tarifário lists (August 2023)
  - Type: Import tariff
  - Evaluation: Red
  - Date announced: 2023-08-16
  - In force: 1

**Multi-pass value:** Prompt returned 500 results vs old ceiling of 50. Overview pass reveals 900% more data.

---

### Prompt 11: Find all anti-dumping investigations targeting Chinese steel since 2020

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 98 interventions
- Response size: 58.7 KB (60,089 bytes)
- Elapsed: 334 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - SACU: Initiation of anti-dumping investigation on imports of flat-rolled products of iron or non-alloy steel, of a width of 600 mm or more, clad, plated or coated, painted, varnished or coated with plastics from China
  - EU: Initiation of anti-dumping investigation on imports of certain wires of silicomanganese steel from China
  - Republic of Korea: Initiation of antidumping investigation on imports of zinc and zinc-alloy surface-treated cold-rolled products from China
  - Australia: Initiation of antidumping investigation on imports of certain welded steel mesh sheets from China and Malaysia
  - Australia: Initiation of antidumping investigation on imports of certain flat rolled steel products from China and the Republic of Korea

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [151457, 141380, 132223, 85753, 80502]
- IDs returned: [80502, 85753, 132223, 141380, 151457]
- All IDs present: Yes
- Num returned: 5
- Response size: 6.4 KB
- Elapsed: 137 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 80502):
  - Title: Brazil: Definitive antidumping duty on imports of CNG cylinders from China
  - Type: Anti-dumping
  - Evaluation: Red
  - Date announced: 2020-01-31
  - In force: 1

**Multi-pass value:** Prompt returned 98 results vs old ceiling of 50. Overview pass reveals 96% more data.

---

### Prompt 12: What safeguard measures are currently in force on solar panels?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 2 interventions
- Response size: 0.9 KB (919 bytes)
- Elapsed: 146 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - United States of America: Safeguard measure on imports large residential washing machines
  - United States of America: Safeguard measure on imports of crystalline silicon photovoltaic cells

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [58242, 90120]
- IDs returned: [58242, 90120]
- All IDs present: Yes
- Num returned: 2
- Response size: 4.9 KB
- Elapsed: 150 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 58242):
  - Title: United States of America: Safeguard measure on imports large residential washing machines
  - Type: Safeguard
  - Evaluation: Red
  - Date announced: 2017-06-13
  - In force: 1

**Multi-pass value:** Only 2 results (within old 50-result ceiling). Overview mode still useful for compact triage at 0.9 KB.

---

### Prompt 13: What local content requirements affect automotive production in Southeast Asia?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 47 interventions
- Response size: 21.3 KB (21,814 bytes)
- Elapsed: 240 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - Thailand: Government introduced a less restrictive requirement of a 2 to 1 domestic corn absorption rate for wheat import permit
  - Indonesia: Government established several restrictions on shipping and port companies
  - Indonesia: Government provided fiscal incentives for the importation of and changed the local content requirements for the manufacturing of electric vehicles
  - Indonesia: Government provided fiscal incentives for the importation of and changed the local content requirements for the manufacturing of electric vehicles
  - Indonesia: Government provided fiscal incentives for the importation of and changed the local content requirements for the manufacturing of electric vehicles

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [142050, 142454, 117623, 106535, 62791]
- IDs returned: [62791, 106535, 117623, 142050, 142454]
- All IDs present: Yes
- Num returned: 5
- Response size: 8.0 KB
- Elapsed: 153 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 62791):
  - Title: Indonesia: Localisation restrictions in the telecommunications sector
  - Type: Local content requirement
  - Evaluation: Red
  - Date announced: 2009-01-19
  - In force: 1

**Multi-pass value:** Only 47 results (within old 50-result ceiling). Overview mode still useful for compact triage at 21.3 KB.

---

### Prompt 14: What import licensing requirements affect pharmaceutical products in India?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 1 interventions
- Response size: 0.4 KB (449 bytes)
- Elapsed: 138 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - India: Import of certain organic chemicals and waste pharmaceuticals liberalised

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [64871]
- IDs returned: [64871]
- All IDs present: Yes
- Num returned: 1
- Response size: 2.0 KB
- Elapsed: 128 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 64871):
  - Title: India: Import of certain organic chemicals and waste pharmaceuticals liberalised
  - Type: Import licensing requirement
  - Evaluation: Green
  - Date announced: 2018-10-03
  - In force: 1

**Multi-pass value:** Only 1 results (within old 50-result ceiling). Overview mode still useful for compact triage at 0.4 KB.

---

### Prompt 15: Has the use of export restrictions increased since 2020?

**Count query (no multi-pass needed)**
- Status: 200
- Groups: 20
- Total count: 20
- Elapsed: 1329 ms
- Data (first 10 rows):
  - {'value': 1100, 'date_announced_year': '2022'}
  - {'value': 945, 'date_announced_year': '2020'}
  - {'value': 928, 'date_announced_year': '2012'}
  - {'value': 896, 'date_announced_year': '2023'}
  - {'value': 887, 'date_announced_year': '2021'}
  - {'value': 858, 'date_announced_year': '2013'}
  - {'value': 855, 'date_announced_year': '2015'}
  - {'value': 810, 'date_announced_year': '2011'}
  - {'value': 803, 'date_announced_year': '2025'}
  - {'value': 769, 'date_announced_year': '2010'}

---

### Prompt 16: How many harmful interventions were implemented globally in 2025 versus 2024?

**Count pair (no multi-pass needed)**
- **2025:**
  - Status: 200
  - Total count: 6
  - Elapsed: 2397 ms
    - {'value': 3903, 'date_implemented_year': '2025'}
    - {'value': 2760, 'date_implemented_year': 'No implementation date'}
    - {'value': 4, 'date_implemented_year': '2026'}
    - {'value': 1, 'date_implemented_year': '2013'}
    - {'value': 1, 'date_implemented_year': '2024'}
- **2024:**
  - Status: 200
  - Total count: 6
  - Elapsed: 2419 ms
    - {'value': 4439, 'date_implemented_year': '2024'}
    - {'value': 2760, 'date_implemented_year': 'No implementation date'}
    - {'value': 7, 'date_implemented_year': '2025'}
    - {'value': 4, 'date_implemented_year': '2026'}
    - {'value': 1, 'date_implemented_year': '2013'}

---

### Prompt 17: Which interventions target state-owned enterprises specifically?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 158 interventions
- Response size: 70.7 KB (72,381 bytes)
- Elapsed: 389 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - India: Customs duty amendments announced as part of 2026-2027 budget
  - Thailand: BOI provided investment incentives for certain hospital businesses
  - Italy: EIB provides financing for 'CDP Italian Regions De-Linked Rs II'
  - India: Equity participation by north-eastern states in hydroelectric projects
  - India: Scheme approved for the promotion of coal or lignite gasification projects

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [152435, 70740, 57354, 56245, 61394]
- IDs returned: [56245, 57354, 61394, 70740, 152435]
- All IDs present: Yes
- Num returned: 5
- Response size: 8.3 KB
- Elapsed: 128 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 56245):
  - Title: Republic of Moldova: VAT-exempted imports of certain medical equipment
  - Type: Internal taxation of imports
  - Evaluation: Green
  - Date announced: 2014-07-10
  - In force: 1

**Multi-pass value:** Prompt returned 158 results vs old ceiling of 50. Overview pass reveals 216% more data.

---

### Prompt 18: What subnational measures has the US implemented since 2023?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 355 interventions
- Response size: 176.9 KB (181,118 bytes)
- Elapsed: 457 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - United States of America (Texas): USD 14.1 million grant to Coherent Corp under Texas Semiconductor Innovation Fund
  - United States of America (Texas): USD 15.2 million grant to Tekscend Photomask Round Rock Inc under Texas Semiconductor Innovation Fund
  - United States (State of Indiana): USD 10 million in EDGE tax credit to Roche Diagnostics Operations Inc
  - United States (State of Indiana): USD 10 million in redevelopment tax credit to Roche Diagnostics Operations Inc
  - United States of America (State of California): Film production tax credit worth USD 14.1 million for Apple Studios LLC

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [152717, 149212, 140225, 133431, 129116]
- IDs returned: [129116, 133431, 140225, 149212, 152717]
- All IDs present: Yes
- Num returned: 5
- Response size: 9.3 KB
- Elapsed: 161 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 129116):
  - Title: United States (Wisconsin): Prohibition on the use of certain foreign digital products and technologies in the state IT systems
  - Type: Public procurement, nes
  - Evaluation: Red
  - Date announced: 2023-01-08
  - In force: 1

**Multi-pass value:** Prompt returned 355 results vs old ceiling of 50. Overview pass reveals 610% more data.

---

### Prompt 19: What FDI screening measures target Chinese investments in European technology sectors?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 5 interventions
- Response size: 3.5 KB (3,536 bytes)
- Elapsed: 298 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - EU: Commission publishes its new approach to economic security
  - United States of America: Presidential order that Beijing Shiji Information Technology Co., Ltd. divest StayNTouch, Inc
  - United States of America: Executive Order on Securing the Information and Communications Technology and Services Supply Chain
  - India: Trade and investment implications of the 2015-16 budget
  - Germany: Review of foreign investments on national security and public policy grounds

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [151187, 78695, 71882, 12599, 11938]
- IDs returned: [11938, 12599, 71882, 78695, 151187]
- All IDs present: Yes
- Num returned: 5
- Response size: 26.8 KB
- Elapsed: 226 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 11938):
  - Title: Germany: Review of foreign investments on national security and public policy grounds
  - Type: FDI: Entry and ownership rule
  - Evaluation: Red
  - Date announced: 2009-04-18
  - In force: 1

**Multi-pass value:** Only 5 results (within old 50-result ceiling). Overview mode still useful for compact triage at 3.5 KB.

---

### Prompt 20: What measures have G7 countries coordinated against Russia since February 2022?

**Pass 1 -- Overview (auto-detected for broad search)**
- Results: 500 interventions
- Response size: 390.0 KB (399,326 bytes)
- Elapsed: 814 ms
- Keys returned: ['date_announced', 'gta_evaluation', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'state_act_title']
- Sample titles:
  - Italy: EUR 390 million rescue loan to Acciaierie d'Italia
  - Germany: EUR 3 billion state aid scheme for cleantech manufacturing capacity
  - Germany: EUR 3 billion state aid scheme for cleantech manufacturing capacity
  - Germany: EUR 3 billion state aid scheme for cleantech manufacturing capacity
  - Germany: EUR 3 billion state aid scheme for cleantech manufacturing capacity

**Pass 2 -- Standard Detail (auto-detected for specific IDs)**
- IDs requested: [152697, 148527, 143369, 138013, 131542]
- IDs returned: [131542, 138013, 143369, 148527, 152697]
- All IDs present: Yes
- Num returned: 5
- Response size: 18.2 KB
- Elapsed: 136 ms
- Keys returned: ['affected_jurisdictions', 'affected_sectors', 'date_announced', 'date_implemented', 'date_removed', 'eligible_firm', 'gta_evaluation', 'implementation_level', 'implementing_jurisdictions', 'intervention_id', 'intervention_type', 'intervention_url', 'is_in_force', 'is_official_source', 'mast_chapter', 'state_act_id', 'state_act_title', 'state_act_url']
- Sample record (ID 131542):
  - Title: EU: New sanctions package targeting Russia includes diamond import ban and other trade and economic measures
  - Type: Import ban
  - Evaluation: Red
  - Date announced: 2023-12-18
  - In force: 1

**Multi-pass value:** Prompt returned 500 results vs old ceiling of 50. Overview pass reveals 900% more data.

---

## Key Findings

### Result Volume
- **12** of 18 search prompts exceeded the old 50-result ceiling
- **6** search prompts returned 50 or fewer results
- **Max results:** 500 (from a single overview query)
- **Min results (non-zero):** 1
- **Average results:** 237

### Response Sizes (Overview Pass)
- **Average:** 129.2 KB
- **Max:** 390.0 KB
- **Min:** 0.0 KB
- **Fits in LLM context (<100KB):** 10 of 18

### Pass 2 (Detail) Success Rate
- **17** of 17 detail passes returned all requested IDs

### Count Queries
- **2** count prompts tested
  - Prompt 15: OK
  - Prompt 16 (2025): OK
  - Prompt 16 (2024): OK

### Prompts Where Overview Provides Limited Benefit (<= 50 results)
- Prompt 3: 36 results -- What export controls has China imposed on rare earth element
- Prompt 12: 2 results -- What safeguard measures are currently in force on solar pane
- Prompt 13: 47 results -- What local content requirements affect automotive production
- Prompt 14: 1 results -- What import licensing requirements affect pharmaceutical pro
- Prompt 19: 5 results -- What FDI screening measures target Chinese investments in Eu

### Prompts With Zero Results
- Prompt 4: Which countries have restricted exports of lithium or cobalt
