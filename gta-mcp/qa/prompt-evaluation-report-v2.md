# GTA MCP Server -- Prompt Evaluation Report (v2)

**Generated:** 2026-02-12 19:29:25
**API Base:** `https://api.globaltradealert.org`
**Total Prompts Tested:** 24

## Summary

| Verdict | Count |
|---------|-------|
| PASS | 24 |
| WARN | 0 |
| FAIL | 0 |

## Results Overview

| # | Prompt | Status | Results | Time (s) | Verdict |
|---|--------|--------|---------|----------|---------|
| 1 | What tariffs has the US imposed on China since Jan 2025... | 200 | 50 | 7.37 | **PASS** |
| 2 | Which countries have imposed tariffs affecting US expor... | 200 | 50 | 2.38 | **PASS** |
| 3 | What export controls has China imposed on rare earth el... | 200 | 36 | 1.48 | **PASS** |
| 4 | Which countries have restricted exports of lithium or c... | 200 | 50 | 4.12 | **PASS** |
| 5 | What measures currently affect semiconductor manufactur... | 200 | 50 | 3.93 | **PASS** |
| 6 | What subsidies are governments providing for critical m... | 200 | 50 | 2.61 | **PASS** |
| 7 | Which countries subsidise their domestic semiconductor ... | 200 | 50 | 0.81 | **PASS** |
| 8 | Which G20 countries have increased state aid to EV manu... | 200 | 50 | 1.75 | **PASS** |
| 9 | What harmful measures has the EU imposed on US exports ... | 200 | 50 | 3.67 | **PASS** |
| 10 | What measures has Brazil implemented affecting US agric... | 200 | 50 | 3.2 | **PASS** |
| 11 | Find all anti-dumping investigations targeting Chinese ... | 200 | 50 | 1.28 | **PASS** |
| 12 | What safeguard measures are currently in force on solar... | 200 | 2 | 1.08 | **PASS** |
| 13 | What local content requirements affect automotive produ... | 200 | 47 | 1.52 | **PASS** |
| 14 | What import licensing requirements affect pharmaceutica... | 200 | 1 | 0.61 | **PASS** |
| 15 | Has the use of export restrictions increased since 2020... | 200 | 20 | 1.32 | **PASS** |
| 16a | How many harmful interventions were implemented globall... | 200 | 6 | 2.64 | **PASS** |
| 16b | How many harmful interventions were implemented globall... | 200 | 6 | 2.66 | **PASS** |
| 17 | Which interventions target state-owned enterprises spec... | 200 | 50 | 3.23 | **PASS** |
| 18 | What subnational measures has the US implemented since ... | 200 | 50 | 1.01 | **PASS** |
| 19 | What FDI screening measures target Chinese investments ... | 200 | 5 | 1.26 | **PASS** |
| 20 | What measures have G7 countries coordinated against Rus... | 200 | 50 | 4.09 | **PASS** |
| 21 | Overview mode -- semiconductor measures (test detail_le... | 200 | 500 | 7.29 | **PASS** |
| 22 | Recently modified interventions (test -last_updated sor... | 200 | 20 | 3.36 | **PASS** |
| 23 | Standard detail for specific IDs: [152717, 152307, 1513... | 200 | 5 | 0.72 | **PASS** |

---

## Per-Prompt Details

### Prompt 1: What tariffs has the US imposed on China since Jan 2025?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 50
- **Response Time:** 7.37s
- **Verdict:** **PASS**

**Notes:**
- Returned 50 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 152110,
    "state_act_id": 96122,
    "state_act_title": "United States of America: Reclassification of certain vehicles for transport of goods and consequent increase in MFN Duty",
    "intervention_description": [
      {
        "status": "new",
        "order_nr": 1,
        "modified": "2026-01-22 07:16",
        "text": "<p>On 21 January 2026, the U.S. Customs and Border Protection (CBP) issued a ruling relating to the tariff classification of certain vehicles for transport of goods (\u201cmicro truks\u201d). With the ruling, CBP reclassified \u201cmicro truks\u201d as vehicles for the transport of goods under HTSUS 8704.31.01 rather than as works trucks under HTSUS 8709.19.00. Consequently, the import tariff for certain vehicles for transport of goods (\u201cmicro truks\u201d) increased from duty-free to 25%. <br>This ruling will become effective on 22 March 2026.</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/152110?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/96122?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-01-22 14:04",
        "text": "U.S. Customs and Border Protection (21 January 2026). Revocation of Two Ruling Letters and Revocation of Treatment Relating to the Tariff Classification of Certain Vehicles for Transport of Goods. CUSTOMS BULLETIN AND DECISIONS, VOL. 60, NO. 3.: https://www.cbp.gov/sites/default/files/2026-01/Vol%2060_No_3_Complete_0.pdf"
      }
    ],
    "is_official_source": false,
    "gta_evaluation": "Red",
    "implementing_jurisdictions": [
      {
        "id": 840,
        "name": "United States of America",
        "iso": "USA"
      }
    ],
    "implementing_jurisdiction_groups": [],
    "affected_jurisdictions": [
      {
        "id": 124,
        "name": "Canada",
        "iso": "CAN"
      },
      {
        "id": 156,
        "name": "China",
        "iso": "CHN"
      },
      {
        "id": 392,
        "name": "Japan",
        "iso": "JPN"
      },
      {
        "id": 484,
        "name": "Mexico",
        "iso": "MEX"
      },
      {
        "id": 724,
        "name": "Spain",
        "iso": "ESP"
      }
    ],
    "inferred_jurisdictions": "Inferred",
    "implementation_level": "National",
    "eligible_firm": "all",
    "intervention_type": "Import tariff",
    "mast_chapter": "Tariff measures",
    "mast_subchapter": "Tariff measures",
    "affected_sectors": [
      {
        "sector_id": 491,
        "name": "Motor vehicles, trai..."
      }
    ],
    "affected_products": [
      {
        "product_id": 870431,
        "name": "Vehicles; with only ...",
        "prior_level": "0",
        "new_level": "25",
        "unit": "percent",
        "date_implemented": "2026-03-22",
        "date_removed": null
      }
    ],
    "date_announced": "2026-
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "implementer": [
      840
    ],
    "affected": [
      156
    ],
    "intervention_types": [
      47
    ],
    "announcement_period": [
      "2025-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 2: Which countries have imposed tariffs affecting US exports in 2025?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 50
- **Response Time:** 2.38s
- **Verdict:** **PASS**

**Notes:**
- Returned 50 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 151413,
    "state_act_id": 95701,
    "state_act_title": "Mexico: Removal of several products from the \"basic basket\" products list temporarily exempted from import duties (December 2025)",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-01-08 09:03",
        "text": "<p>On 31 December 2025, the government of Mexico published a Decree increasing the import tariffs on 33 products classified under 31 six-digit tariff subheadings. The Decree removes these new products from the \"basic basket\" products list first established in May 2022 and its modifications (see related state acts). The measure will enter into force one day following its publication, namely on 1 January 2026.</p><p>Among the affected products are beef and pork (live animals and meat), milk and dairy products, paddy rice, dried beans and other legumes, vegetable oils (soybean, sunflower, safflower and cottonseed), tilapia, and sausages and similar meat products. According to the latest edition of the Law on General Import and Export Taxes (7 June 2022 and its modifications), the newly applicable MFN duties will range between 5% and 45%.</p><p>In addition, the Decree also extends the \"basic basket\" tariff exemptions until December 2026 (see related state acts).</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/151413?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/95701?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-01-05 12:08",
        "text": "Official Gazette [Diario Oficial de la Federaci\u00f3n] (31 December 2025). DECRETO por el que se modifica el diverso por el que se exenta el pago de arancel de importaci\u00f3n y se otorgan facilidades administrativas a diversas mercanc\u00edas de la canasta b\u00e1sica y de consumo b\u00e1sico de las familias. (Retrieved on 5 January 2025):\n\nhttps://dof.gob.mx/nota_detalle.php?codigo=5777651&fecha=31/12/2025#gsc.tab=0"
      }
    ],
    "is_official_source": false,
    "gta_evaluation": "Red",
    "implementing_jurisdictions": [
      {
        "id": 484,
        "name": "Mexico",
        "iso": "MEX"
      }
    ],
    "implementing_jurisdiction_groups": [
      {
        "name": "European Union"
      }
    ],
    "affected_jurisdictions": [
      {
        "id": 32,
        "name": "Argentina",
        "iso": "ARG"
      },
      {
        "id": 36,
        "name": "Australia",
        "iso": "AUS"
      },
      {
        "id": 76,
        "name": "Brazil",
        "iso": "BRA"
      },
      {
        "id": 124,
        "name": "Canada",
        "iso": "CAN"
      },
      {
        "id": 156,
        "name": "China",
        "iso": "CHN"
      }
    ],
    "_affected_jurisdictions_total": 11,
    "inferred_jurisdictions": "In
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "affected": [
      840
    ],
    "intervention_types": [
      47
    ],
    "announcement_period": [
      "2025-01-01",
      "2025-12-31"
    ]
  }
}
```
</details>

### Prompt 3: What export controls has China imposed on rare earth elements?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 36
- **Response Time:** 1.48s
- **Verdict:** **PASS**

**Notes:**
- Returned 36 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 151266,
    "state_act_id": 95623,
    "state_act_title": "China: Government grants export license to Ningbo Jintian Copper",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2025-12-15 16:26",
        "text": "<p>On 10 December 2025, the Chinese company\u00a0Ningbo Jintian Copper announced that it\u00a0had been granted an export license for the export of rare earth permanent magnet products. The statement was made on the Shanghai Stock Exchange Interactive Platform.</p><p>According to the company's statement, its \"rare earth permanent magnet products are widely used in various high-end fields such as new energy vehicles, wind power generation, high-efficiency energy-saving motors, robots, consumer electronics, and medical devices.\" The company \"primarily engages in non-ferrous metal processing, with main products including copper products and rare earth permanent magnet materials.\" (unofficial translation)</p><p>Several other Chinese companies were also reportedly to have secured \"general\" export licenses to export rare-earth-related items days ago (see related state act).</p><p>Notably, the news was reported following the US-China trade and economic agreement announced in late October 2025. The White House's Fact Sheet on the deal noted that China would \"issue general licenses\" for the benefit of US end users. This was not confirmed by the Chinese government at the time of writing.</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/151266?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/95623?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2025-12-10 21:28",
        "text": "SSE e-interaction [\u4e0a\u8bc1e\u4e92\u52a8] (10 December 2025). Company response to investors' questions (Retrieved on 10 December 2025):\nhttps://sns.sseinfo.com/company.do?uid=163607\n<p> \nReuters (10 December 2025). Another Chinese rare earth producer gets streamlined licence for magnet exports (Retrieved on 10 December 2025):\nhttps://www.reuters.com/world/asia-pacific/another-chinese-rare-earth-producer-obtains-streamlined-licence-magnet-exports-2025-12-10/"
      }
    ],
    "is_official_source": false,
    "gta_evaluation": "Green",
    "implementing_jurisdictions": [
      {
        "id": 156,
        "name": "China",
        "iso": "CHN"
      }
    ],
    "implementing_jurisdiction_groups": [],
    "affected_jurisdictions": [
      {
        "id": 32,
        "name": "Argentina",
        "iso": "ARG"
      },
      {
        "id": 36,
        "name": "Australia",
        "iso": "AUS"
      },
      {
        "id": 40,
        "name": "Austria",
        "iso": "AUT"
      },
      {
        "id": 50,
        "name": "Bangladesh",
        "iso": "BGD"
      },
      {
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "implementer": [
      156
    ],
    "mast_chapters": [
      14
    ],
    "query": "rare earth",
    "announcement_period": [
      "1900-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 4: Which countries have restricted exports of lithium or cobalt since 2022?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 50
- **Response Time:** 4.12s
- **Verdict:** **PASS**

**Notes:**
- Returned 50 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 151902,
    "state_act_id": 95991,
    "state_act_title": "China: Cancellation and reduction of export tax rebates for photovoltaic products and batteries",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-01-23 10:17",
        "text": "<p>On 8 January 2026, the Chinese Ministry of Finance and the State Administration of Taxation adopted Announcement 2026/2, announcing the reduction of value-added tax rebates for battery-related products, such as lithium-ion batteries, from 9% to 6%. This includes 22 HS codes at the 8-digit or 10-digit level in Chapter 85. The reduction takes effect from 1 April 2026 and will remain in effect until 31 December 2026.</p><p>Within the same document, the government announced additional measures to cancel the export tax rebate for photovoltaic products and batteries (see related interventions).</p><p>In November 2024, the government removed various products from the list of goods eligible for export rebates (see related state act).</p>"
      },
      {
        "status": "new",
        "order_nr": 2,
        "modified": "2026-01-23 10:17",
        "text": "<p>On 20 January 2026, the government spokesman replied to Bloomberg's question regarding this measure and noted, \"This adjustment to the export tax rebate policy will help promote the efficient use of resources, reduce environmental pollution and carbon emissions, and drive a comprehensive green transformation of economic and social development. At the same time, it will also help guide the rational adjustment of industrial structure, promote industrial transformation and upgrading, comprehensively address 'involutionary' competition, and promote high-quality economic development.\" (unofficial translation)</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/151902?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/95991?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-01-23 10:11",
        "text": "Ministry of Finance [\u8d22\u653f\u90e8] State Administration of Taxation [\u56fd\u5bb6\u7a0e\u52a1\u603b\u5c40] (8 January 2026). \u8d22\u653f\u90e8 \u7a0e\u52a1\u603b\u5c40\u5173\u4e8e\u8c03\u6574\u5149\u4f0f\u7b49\u4ea7\u54c1\u51fa\u53e3\u9000\u7a0e\u653f\u7b56\u7684\u516c\u544a. \u8d22\u653f\u90e8 \u7a0e\u52a1\u603b\u5c40\u516c\u544a2026\u5e74\u7b2c2\u53f7 (10 January 2026):\nhttps://szs.mof.gov.cn/zhengcefabu/202601/t20260109_3981637.htm\nMinistry of Finance [\u8d22\u653f\u90e8] State Administration of Taxation [\u56fd\u5bb6\u7a0e\u52a1\u603b\u5c40] (8 January 2026). \u8d22\u653f\u90e8 \u7a0e\u52a1\u603b\u5c40\u5173\u4e8e\u8c03\u6574\u5149\u4f0f\u7b49\u4ea7\u54c1\u51fa\u53e3\u9000\u7a0e\u653f\u7b56\u7684\u516c\u544a. \u8d22\u653f\u90e8 \u7a0e\u52a1\u603b\u5c40\u516c\u544
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "mast_chapters": [
      14
    ],
    "query": "lithium | cobalt",
    "announcement_period": [
      "2022-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 5: What measures currently affect semiconductor manufacturing equipment trade?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 50
- **Response Time:** 3.93s
- **Verdict:** **PASS**

**Notes:**
- Returned 50 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 152717,
    "state_act_id": 96397,
    "state_act_title": "United States of America (Texas): USD 14.1 million grant to Coherent Corp under Texas Semiconductor Innovation Fund",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-10 17:08",
        "text": "<p>On 6 February 2026, the government of the state of Texas announced a USD 14.1 million grant to Coherent Corp through the Texas Semiconductor Innovation Fund. The funding supports the production of Indium Phosphide (InP) wafers at the company's facility in Sherman, Texas.</p><p>According to the press release, the project involves a total capital investment of more than USD 154 million to produce technology used for data communications, telecommunications, artificial intelligence interconnects, and satellite communications.</p><p>In this context, Texas's Governor Greg Abbott said: \u201cTexas is the new frontier for technological innovation. This $154 million investment by Coherent to establish the world\u2019s first 6-inch InP wafer fabrication plant in Sherman is testament to Texas\u2019 leadership in semiconductor manufacturing and the technologies of tomorrow. With our skilled and growing workforce and the best business climate in the nation, Texas is where the future is building.\u201d</p><p><strong>Texas Semiconductor Innovation Fund (TSIF)</strong></p><p>The grant program was launched in 2023 under the Texas CHIPS Act (see related state act). The scheme aims to support Texas\u2019s leadership in semiconductor research, design, and manufacturing.</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/152717?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/96397?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "new",
        "order_nr": 1,
        "modified": "2026-02-10 17:02",
        "text": "Office of the Texas Governor (6 February 2026). Governor Abbott Announces Texas Semiconductor Innovation Fund Grant to Coherent. Press release (10 February 2026): https://gov.texas.gov/news/post/governor-abbott-announces-texas-semiconductor-innovation-fund-grant-to-coherent"
      }
    ],
    "is_official_source": false,
    "gta_evaluation": "Red",
    "implementing_jurisdictions": [
      {
        "id": 840,
        "name": "United States of America",
        "iso": "USA"
      }
    ],
    "implementing_jurisdiction_groups": [],
    "affected_jurisdictions": [
      {
        "id": 56,
        "name": "Belgium",
        "iso": "BEL"
      },
      {
        "id": 124,
        "name": "Canada",
        "iso": "CAN"
      },
      {
        "id": 156,
        "name": "China",
        "iso": "CHN"
      },
      {
        "id": 203,
        "name": "Czechia",
        "iso": "CZE"
      },
      {
        "id": 208,
        "name": "Denmark",
        "iso": "DNK"

```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "query": "semiconductor",
    "in_force_on_date": "2026-02-12",
    "keep_in_force_on_date": true,
    "announcement_period": [
      "1900-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 6: What subsidies are governments providing for critical mineral processing?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 50
- **Response Time:** 2.61s
- **Verdict:** **PASS**

**Notes:**
- Returned 50 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 152570,
    "state_act_id": 96344,
    "state_act_title": "United States of America: EXIM approves loan to establish a Strategic Critical Minerals Reserve",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-06 11:55",
        "text": "<p>On 2 February 2026, the US government, through the Export-Import Bank of the United States, approved a Direct Loan of up to USD 10 billion to support Project Vault in the United States. The financing aims to establish a Strategic Critical Minerals Reserve to secure access to essential raw materials for domestic manufacturers. The intervention targets US-based manufacturing supply chains and seeks to support production, processing, and storage of critical minerals across multiple states.</p><p>The approved loan will provide long-term financing to Project Vault, an independently governed public-private partnership involving original equipment manufacturers and private capital providers. According to the announcement, participating manufacturers reportedly include Clarios, GE Vernova, Western Digital, and Boeing, while suppliers include Hartree Partners, Mercuria Americas, and Traxys. The reserve is expected to store critical raw materials in facilities distributed across the United States to mitigate supply disruptions.</p><p>In this context, EXIM Chairman John Jovanovic said: \u201cProject Vault is designed to support domestic manufacturers from supply shocks, support U.S. production and processing of critical raw materials, and strength America\u2019s critical minerals sector. Thanks to President Trump\u2019s leadership, the U.S. Strategic Critical Minerals Reserve will help manufacturers in the United States compete, grow, and lead globally while creating jobs domestically, strengthening our economy, and advancing the national interest.\u201d</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/152570?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/96344?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-06 11:43",
        "text": "Export-Import Bank of the United States (2 February 2026). EXIM Approves Project Vault Loan to Launch America's Strategic Critical Minerals Reserve and Support Manufacturing Jobs. Press Release: https://www.exim.gov/news/project-vault"
      }
    ],
    "is_official_source": false,
    "gta_evaluation": "Red",
    "implementing_jurisdictions": [
      {
        "id": 840,
        "name": "United States of America",
        "iso": "USA"
      }
    ],
    "implementing_jurisdiction_groups": [],
    "affected_jurisdictions": [
      {
        "id": 76,
        "name": "Brazil",
        "iso": "BRA"
      },
      {
        "id": 124,
        "name": "Canada",
        "iso": "CAN"
      },
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "mast_chapters": [
      10
    ],
    "query": "critical mineral",
    "announcement_period": [
      "1900-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 7: Which countries subsidise their domestic semiconductor industry?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 50
- **Response Time:** 0.81s
- **Verdict:** **PASS**

**Notes:**
- Returned 50 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 152717,
    "state_act_id": 96397,
    "state_act_title": "United States of America (Texas): USD 14.1 million grant to Coherent Corp under Texas Semiconductor Innovation Fund",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-10 17:08",
        "text": "<p>On 6 February 2026, the government of the state of Texas announced a USD 14.1 million grant to Coherent Corp through the Texas Semiconductor Innovation Fund. The funding supports the production of Indium Phosphide (InP) wafers at the company's facility in Sherman, Texas.</p><p>According to the press release, the project involves a total capital investment of more than USD 154 million to produce technology used for data communications, telecommunications, artificial intelligence interconnects, and satellite communications.</p><p>In this context, Texas's Governor Greg Abbott said: \u201cTexas is the new frontier for technological innovation. This $154 million investment by Coherent to establish the world\u2019s first 6-inch InP wafer fabrication plant in Sherman is testament to Texas\u2019 leadership in semiconductor manufacturing and the technologies of tomorrow. With our skilled and growing workforce and the best business climate in the nation, Texas is where the future is building.\u201d</p><p><strong>Texas Semiconductor Innovation Fund (TSIF)</strong></p><p>The grant program was launched in 2023 under the Texas CHIPS Act (see related state act). The scheme aims to support Texas\u2019s leadership in semiconductor research, design, and manufacturing.</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/152717?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/96397?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "new",
        "order_nr": 1,
        "modified": "2026-02-10 17:02",
        "text": "Office of the Texas Governor (6 February 2026). Governor Abbott Announces Texas Semiconductor Innovation Fund Grant to Coherent. Press release (10 February 2026): https://gov.texas.gov/news/post/governor-abbott-announces-texas-semiconductor-innovation-fund-grant-to-coherent"
      }
    ],
    "is_official_source": false,
    "gta_evaluation": "Red",
    "implementing_jurisdictions": [
      {
        "id": 840,
        "name": "United States of America",
        "iso": "USA"
      }
    ],
    "implementing_jurisdiction_groups": [],
    "affected_jurisdictions": [
      {
        "id": 56,
        "name": "Belgium",
        "iso": "BEL"
      },
      {
        "id": 124,
        "name": "Canada",
        "iso": "CAN"
      },
      {
        "id": 156,
        "name": "China",
        "iso": "CHN"
      },
      {
        "id": 203,
        "name": "Czechia",
        "iso": "CZE"
      },
      {
        "id": 208,
        "name": "Denmark",
        "iso": "DNK"

```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "query": "semiconductor",
    "in_force_on_date": "2026-02-12",
    "keep_in_force_on_date": true,
    "announcement_period": [
      "1900-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 8: Which G20 countries have increased state aid to EV manufacturers since 2022?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 50
- **Response Time:** 1.75s
- **Verdict:** **PASS**

**Notes:**
- Returned 50 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 152705,
    "state_act_id": 96391,
    "state_act_title": "Canada: New measures to support the automobile industry",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-11 12:51",
        "text": "<p>On 5 February 2026, the Canadian government announced it would allocate of CAD 3 (USD 2.22) billion from the Strategic Response Fund to support the local automotive industry. The government did not specify the form the support would take.</p><p>According to the press release, the measures aim to assist the sector in adapting and diversifying into new international markets. This funding is part of a broader industrial strategy to reduce reliance on one trade partner and increase economic resilience. The government also confirmed the maintenance of counter-tariffs on automotive imports from the United States to ensure a level playing field for domestic manufacturers.</p><p>The Strategic Response Fund (SRF) replaces the Strategic Innovation Fund (SIF), building on its mandate, and is a federal program that supports Canada's industrial transformation by investing in sectors vulnerable to trade disruptions, including automotive, steel, and aluminium.</p><p>In the same announcement, the government committed up to CAD 100 (USD 73.88) million from the Regional Tariff Response Initiative to support the automotive industry. This scheme did not pass the GTA reporting criteria, as only small and medium-sized enterprises are eligible for funding.</p><p>In this context, Mark Carney, Prime Minister of Canada, said: \u201cCanada\u2019s new government is fundamentally transforming our economy \u2013 from one reliant on a single trade partner, to one that is stronger, more independent, and more resilient to global shocks. We are making strategic decisions and generational investments to build a strong Canadian auto sector, where Canadian workers build the cars of the future\".</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/152705?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/96391?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "new",
        "order_nr": 1,
        "modified": "2026-02-10 14:40",
        "text": "Prime Minister of Canada (5 February 2026). Prime Minister Carney Launches News Strategy to Transform Canada's Auto Industry. Press release (retrieved on 10 February 2026): https://www.pm.gc.ca/en/news/news-releases/2026/02/05/prime-minister-carney-launches-new-strategy-transform-canadas-auto"
      }
    ],
    "is_official_source": false,
    "gta_evaluation": "Amber",
    "implementing_jurisdictions": [
      {
        "id": 124,
        "name": "Canada",
        "iso": "CAN"
      }
    ],
    "implementing_jurisdiction_groups": [],
    "affected_jurisdictions": [
      {
        "id": 8,
        "name": "Alban
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "mast_chapters": [
      10
    ],
    "query": "electric vehicle",
    "announcement_period": [
      "2022-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 9: What harmful measures has the EU imposed on US exports since 2024?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 50
- **Response Time:** 3.67s
- **Verdict:** **PASS**

**Notes:**
- Returned 50 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 152737,
    "state_act_id": 96405,
    "state_act_title": "EU: Action plan on drone and counter-drone security to support the development of homegrown technologies",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-11 14:32",
        "text": "<p>On 11 February 2026, the European Commission published an Action Plan on Drone and Counter-Drone Security to support the prevention, detection, and response to malicious drone activities. Among other actions the communication signals the EU's intention to support the development of homegrown technologies through state aid.</p><p>More concretely, the Action Plan emphasises accelerating the expansion and industrial scaling of EU-based drone and counter-drone companies, as well as increasing manufacturing capacity, by:</p>\n<ul><li>identifying strategic investment priorities that favour innovative, scalable solutions developed by emerging actors operating across both civilian and defence sectors;</li><li>coordinating and activating sufficient public and private financing at both national and EU levels, spanning civilian and military domains;</li><li>drawing on cohesion policy resources and encouraging complementary national funding to prevent duplication, streamline financial flows, and concentrate support on clearly defined strategic priorities.</li></ul>\n<p>Most of the funding for the goals of the Action Plan will come from already existing programmes, such as the European Defence Fund (EDF), the European Defence Industry Programme (EDIP), the SAFE instrument (Security Action for Europe), the European Innovation Council (EIC), the EU Disruptive Innovation Scheme (EUDIS), the Border Management and Visa Instrument (BMVI). In the medium term, the defence, resilience and security window of the forthcoming European Competitiveness Fund (ECF) will also support the goals of this Action Plan.</p><p>In this context, Commissioner for Defence and Space, Andrius Kubilius, noted, \"With the launch of this Action Plan, we are turning the concept of a \u2018Drone Wall\u2019 from a political vision into an industrial reality. To achieve true defence readiness, Europe must be able to protect its borders and critical sites with a sophisticated, multi-layered shield that can detect and neutralise any threat in real-time. Commission is developing a range of tools to the industry and Member States to develop and acquire drone and anti-drone defence capabilities in Europe. This includes the Eastern Flank Watch initiative and European Drone Defence Initiative. By bridging the gap between innovative civilian technology and military requirements, we are ensuring that our defence industry can produce these essential systems at the scale and speed required to keep Europe secure and technologically sovereign.'</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/152737?key=eba65271-5400-4782-96c3-1
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "implementer": [
      1049
    ],
    "affected": [
      840
    ],
    "gta_evaluation": [
      1,
      2
    ],
    "announcement_period": [
      "2024-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 10: What measures has Brazil implemented affecting US agricultural exports?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 50
- **Response Time:** 3.2s
- **Verdict:** **PASS**

**Notes:**
- Returned 50 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 152527,
    "state_act_id": 96337,
    "state_act_title": "Brazil: Modifications of the import tariff of 1'249 products under the LEBIT/BK list (February 2026)",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-06 12:37",
        "text": "<p>On 5 February 2026, the Executive Committee of the Brazilian Foreign Trade Chamber (Gecex) published Resolution No. 852, which increased the import tariff for 893 products under 566 six-digit subheadings. The resolution will come into effect on 6 February 2026.</p><p>Specifically, previously these products were subject to a range of import duties between 0% to 12.6%. The new import tariffs range between 4% to 25%. The Resolution also modified the removal date of the import tariff rate quota of NCM 8517.71.20 to 18 August 2026 (see related state act).</p><p>The Resolution adds these products to Annexe VI of GECEX Resolution No. 272 of November 2021. This Annexe corresponds to the List of Exceptions for Computer and Telecommunications Goods and Capital Goods (LEBIT/BK list).</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/152527?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/96337?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-06 12:36",
        "text": "Executive Committee of the Foreign Trade Chamber [Comit\u00ea-Executivo de Gest\u00e3o da C\u00e2mara de Com\u00e9rcio Exterior] (5 February 2026). Resolu\u00e7\u00e3o Gecex n\u00ba 852, de 4 de fevereiro de 2026. Di\u00e1rio Oficial da Uni\u00e3o (Retrieval date: 5 February 2026): https://in.gov.br/en/web/dou/-/resolucao-gecex-n-852-de-4-de-fevereiro-de-2026-685397607\n\nGovernment of Brazil, Ministry of Economy [Governo do Brasil, Minist\u00e9rio da Economia]. Tarifas Vigentes/Lista de Bens sem Similar Nacional (Lessin), Anexo I - Tarifa Externa Comum - TEC - Sistema Harmonizado (SH-2022): https://www.gov.br/mdic/pt-br/assuntos/camex/se-camex/strat/tarifas/vigentes\n\nMERCOSUR Decisi\u00f3n CMC No. 08/2021. Available at: https://normas.mercosur.int/simfiles/normativas/87468_DEC_008-2021_ES_BIT-BK.pdf"
      }
    ],
    "is_official_source": false,
    "gta_evaluation": "Red",
    "implementing_jurisdictions": [
      {
        "id": 76,
        "name": "Brazil",
        "iso": "BRA"
      }
    ],
    "implementing_jurisdiction_groups": [],
    "affected_jurisdictions": [
      {
        "id": 32,
        "name": "Argentina",
        "iso": "ARG"
      },
      {
        "id": 36,
        "name": "Australia",
        "iso": "AUS"
      },
      {
        "id": 40,
        "name": "Austria",
        "iso": "AUT"
      },
      {
        "id": 50,
        "name": "Bangladesh",
        "iso": "BGD"
      },
      {
        "id": 56,
        "name": "Bel
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "implementer": [
      76
    ],
    "affected": [
      840
    ],
    "announcement_period": [
      "1900-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 11: Find all anti-dumping investigations targeting Chinese steel since 2020

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 50
- **Response Time:** 1.28s
- **Verdict:** **PASS**

**Notes:**
- Returned 50 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 151457,
    "state_act_id": 95733,
    "state_act_title": "SACU: Initiation of anti-dumping investigation on imports of flat-rolled products of iron or non-alloy steel, of a width of 600 mm or more, clad, plated or coated, painted, varnished or coated with plastics from China",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2025-12-19 14:54",
        "text": "<p>On 17 December 2025, the International Trade Administration Commission of South Africa initiated an anti-dumping investigation on imports of flat-rolled products of iron or non-alloy steel, of a width of 600 mm or more, clad, plated or coated, painted, varnished or coated with plastics from China. The products subject to investigation are classified under HS codes 7210.70.20, 7210.70.30, 7210.70.40, and 7210.70.90. This investigation follows the application lodged by ArcelorMittal South Africa Ltd and Safal Steel (Pty) Ltd on behalf of the SACU industry. The notice does not specify when a final determination or subsequent decision will be issued.</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/151457?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/95733?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2025-12-19 14:58",
        "text": "International Trade Administration Commission (17 December 2025). NOTICE 3694 OF 2025. Government Gazette (retrieved on 19 December 2025): https://www.gov.za/sites/default/files/gcis_document/202512/53872gen3694.pdf"
      }
    ],
    "is_official_source": false,
    "gta_evaluation": "Amber",
    "implementing_jurisdictions": [
      {
        "id": 72,
        "name": "Botswana",
        "iso": "BWA"
      },
      {
        "id": 748,
        "name": "Eswatini",
        "iso": "SWZ"
      },
      {
        "id": 426,
        "name": "Lesotho",
        "iso": "LSO"
      },
      {
        "id": 516,
        "name": "Namibia",
        "iso": "NAM"
      },
      {
        "id": 710,
        "name": "South Africa",
        "iso": "ZAF"
      }
    ],
    "implementing_jurisdiction_groups": [
      {
        "name": "SACU"
      }
    ],
    "affected_jurisdictions": [
      {
        "id": 156,
        "name": "China",
        "iso": "CHN"
      }
    ],
    "inferred_jurisdictions": "Targeted",
    "implementation_level": "Supranational",
    "eligible_firm": "all",
    "intervention_type": "Anti-dumping",
    "mast_chapter": "D: Contingent trade-protective measures",
    "mast_subchapter": "D1 Antidumping",
    "affected_sectors": [
      {
        "sector_id": 412,
        "name": "Products of iron or ..."
      }
    ],
    "affected_products": [
      {
        "product_id": 721070,
        "name": "Iron or non-alloy st...",
        "prior_level": null,
   
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "affected": [
      156
    ],
    "intervention_types": [
      51
    ],
    "query": "steel",
    "announcement_period": [
      "2020-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 12: What safeguard measures are currently in force on solar panels?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 2
- **Response Time:** 1.08s
- **Verdict:** **PASS**

**Notes:**
- Returned 2 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 58242,
    "state_act_id": 28096,
    "state_act_title": "United States of America: Safeguard measure on imports large residential washing machines",
    "intervention_description": [
      {
        "status": "static",
        "order_nr": 1,
        "modified": "2025-12-15 15:54",
        "text": "<p style=\"text-align: justify;\">On January 22, 2018, U.S. Trade Representative Robert Lighthizer announced that President Trump has approved recommendations to impose safeguard tariffs on imported residential washing machines (as well as solar cells and modules), based on the investigations, findings, and recommendations of the U.S. International Trade Commission (USITC). The restrictions will be imposed for three years on the following schedule:</p>\r\n<p style=\"text-align: justify;\">Tariff-Rate Quotas on Washers <br />Year 1:<br />20% on the first 1.2 million units of imported finished washers; 50% on all subsequent imports of finished washers; 50% tariff on covered parts after the first 50,000 units&nbsp;</p>\r\n<p style=\"text-align: justify;\">Year 2:<br />18% on the first 1.2 million units of imported finished washers; 45% on all subsequent imports of finished washers; 45% tariff on covered parts after the first 70,000 units&nbsp;</p>\r\n<p style=\"text-align: justify;\">Year 3:<br />16% on the first 1.2 million units of imported finished washers; 40% on all subsequent imports of finished washers; 40% tariff on covered parts after the first 90,000 units&nbsp;</p>\r\n<p style=\"text-align: justify;\">The restrictions came into effect on February 7, 2018.</p>\r\n<p style=\"text-align: justify;\">Together with the solar cells and modules case, this&nbsp;is the first time that the United States has resorted to the global safeguard since invoking that \"escape clause\" in a 2001 steel case. The restrictions imposed then, like nearly&nbsp;all other uses of the safeguard by all countries since the World Trade Organization came into existence in 1995, was found in a WTO dispute-settlement panel to have violated the terms of the WTO Agreement on Safeguards. It is widely expected that this latest&nbsp;case will lead to a similar challenge. If that challenge is successful (as is widely expected), the United States will need to decide if it will comply with its WTO obligations by bringing these restrictions to an end. Taking into accouint the usual pace of such cases, this finding might reasonably be expected while the restrictions are in their second year.</p>\r\n<p style=\"text-align: justify;\">This case began on 13 June 2017 when the USITC initiated a safeguard investigation of large residential washers. This investigation came in response to a petition filed by the Whirlpool Corporation. The commission determined that this investigation is &ldquo;extraordinarily complicated,&rdquo; and would make its injury determination by October 5, 2017.</p>\r\n<p style=\"text-align: justify;\">On 21 November 2017, the commission anno
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "intervention_types": [
      52
    ],
    "query": "solar",
    "in_force_on_date": "2026-02-12",
    "keep_in_force_on_date": true,
    "announcement_period": [
      "1900-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 13: What local content requirements affect automotive production in Southeast Asia?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 47
- **Response Time:** 1.52s
- **Verdict:** **PASS**

**Notes:**
- Returned 47 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 142050,
    "state_act_id": 89975,
    "state_act_title": "Thailand: Government introduced a less restrictive requirement of a 2 to 1 domestic corn absorption rate for wheat import permit",
    "intervention_description": [
      {
        "status": "static",
        "order_nr": 1,
        "modified": "2025-12-15 16:11",
        "text": "<p>On 16 December 2024,\u00a0the\u00a0Ministry of Commerce of Thailand temporarily imposed a less restrictive requirement of\u00a0a 2 to 1 domestic corn absorption rate\u00a0for importers to secure\u00a0a feed wheat import permit.\u00a0</p>\r\n<p>Previously, to secure\u00a0a feed wheat import permit, the importer should demonstrate a 3 to 1 domestic corn absorption rate (i.e., to import a ton of feed wheat, a mill should use three metric tons of domestic corn); see related act.</p>\r\n<p>The regulation will enter into force temporarily from\u00a01 January 2025\u00a0to 31 December 2025.</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/142050?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/89975?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "static",
        "order_nr": 1,
        "modified": "2025-11-20 16:09",
        "text": "Ministry of Commerce of Thailand (16 December 2024). Regulations on the request for permission and permission to import wheat into the Kingdom for the year 2025 (in Thai) (retrieved on 10 January 2025): https://www.dft.go.th/th-th/Detail-Law/ArticleId/28734/28734"
      }
    ],
    "is_official_source": true,
    "gta_evaluation": "Green",
    "implementing_jurisdictions": [
      {
        "id": 764,
        "name": "Thailand",
        "iso": "THA"
      }
    ],
    "implementing_jurisdiction_groups": [],
    "affected_jurisdictions": [
      {
        "id": 104,
        "name": "Myanmar",
        "iso": "MMR"
      },
      {
        "id": 116,
        "name": "Cambodia",
        "iso": "KHM"
      },
      {
        "id": 418,
        "name": "Lao",
        "iso": "LAO"
      },
      {
        "id": 699,
        "name": "India",
        "iso": "IND"
      },
      {
        "id": 710,
        "name": "South Africa",
        "iso": "ZAF"
      }
    ],
    "_affected_jurisdictions_total": 6,
    "inferred_jurisdictions": "Inferred",
    "implementation_level": "National",
    "eligible_firm": "all",
    "intervention_type": "Local content requirement",
    "mast_chapter": "I: Trade-related investment measures",
    "mast_subchapter": "I1 Local content measures",
    "affected_sectors": [
      {
        "sector_id": 11,
        "name": "Cereals..."
      }
    ],
    "affected_products": [
      {
        "product_id": 100510,
        "name": "Cereals; maize (corn...",
        "prior_level": "",
        "new_level": "",
        "unit": null,
        "date_implemented": "2025-01-01",
        "date_removed": "2025-
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "implementer": [
      360,
      764,
      704,
      458,
      608
    ],
    "intervention_types": [
      28
    ],
    "announcement_period": [
      "1900-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 14: What import licensing requirements affect pharmaceutical products in India?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 1
- **Response Time:** 0.61s
- **Verdict:** **PASS**

**Notes:**
- Returned 1 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 64871,
    "state_act_id": 33586,
    "state_act_title": "India: Import of certain organic chemicals and waste pharmaceuticals liberalised",
    "intervention_description": [
      {
        "status": "static",
        "order_nr": 1,
        "modified": "2025-12-15 15:57",
        "text": "<p>On 3 October 2018, the Indian Ministry of Commerce and Industry through Notification No. 39/2015-2020 liberalized the import of certain organic chemicals and waste pharmaceutical products. The list of organic chemicals includes&nbsp;derivatives of hydrocarbons, acyclic alcohols, acids, amine-function compounds, oxygen-function amino-compounds, Carboxyamide-function compounds, Nitrile-function compounds, Organo-sulphur compounds, Other organo-inorganic compounds, Heterocyclic compounds, Nucleic acids &amp;&nbsp;their salts, Provitamins, vitamins, and Alkaloids.</p>\r\n<p>The imports of these products were earlier&nbsp;\"restricted\" i.e. they required a license and were restricted to be used by the importer only. These restrictions have now been removed and the import policy has been changed from \"Restricted\" to \"Free\". However, a No Objection Certificate&nbsp;will be required from the Narcotics Commissioner in Gwalior before the import of such products.</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/64871?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/33586?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "static",
        "order_nr": 1,
        "modified": "2025-11-20 16:03",
        "text": "Notification No. 39/2015-2020\r\nhttp://dgft.gov.in/sites/default/files/Notification%20No.39%20dt-3.10.18%28E%29.pdf"
      }
    ],
    "is_official_source": true,
    "gta_evaluation": "Green",
    "implementing_jurisdictions": [
      {
        "id": 699,
        "name": "India",
        "iso": "IND"
      }
    ],
    "implementing_jurisdiction_groups": [],
    "affected_jurisdictions": [
      {
        "id": 36,
        "name": "Australia",
        "iso": "AUS"
      },
      {
        "id": 56,
        "name": "Belgium",
        "iso": "BEL"
      },
      {
        "id": 156,
        "name": "China",
        "iso": "CHN"
      },
      {
        "id": 191,
        "name": "Croatia",
        "iso": "HRV"
      },
      {
        "id": 203,
        "name": "Czechia",
        "iso": "CZE"
      }
    ],
    "_affected_jurisdictions_total": 21,
    "inferred_jurisdictions": "Inferred",
    "implementation_level": "National",
    "eligible_firm": "all",
    "intervention_type": "Import licensing requirement",
    "mast_chapter": "E: Non-automatic licensing, quotas etc.",
    "mast_subchapter": "E1 Non-automatic import-licensing procedures other than authorizations for SPS or TBT reasons",
    "affected_sectors": [
      {
        "sector_id": 341,
        "name": "Basic organic chemic..."

```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "implementer": [
      699
    ],
    "intervention_types": [
      36
    ],
    "query": "pharmaceutical",
    "announcement_period": [
      "1900-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 15: Has the use of export restrictions increased since 2020?

- **Endpoint:** `counts`
- **HTTP Status:** 200
- **Result Count:** 20
- **Response Time:** 1.32s
- **Verdict:** **PASS**

**Notes:**
- Returned 20 result(s)

**Sample Results:**
```json
[
  {
    "value": 1100,
    "date_announced_year": "2022"
  },
  {
    "value": 945,
    "date_announced_year": "2020"
  },
  {
    "value": 928,
    "date_announced_year": "2012"
  }
]
```

<details>
<summary>Request Body</summary>

```json
{
  "request_data": {
    "mast_chapters": [
      14
    ],
    "count_by": [
      "date_announced_year"
    ],
    "count_variable": "intervention_id"
  }
}
```
</details>

### Prompt 16a: How many harmful interventions were implemented globally in 2025?

- **Endpoint:** `counts`
- **HTTP Status:** 200
- **Result Count:** 6
- **Response Time:** 2.64s
- **Verdict:** **PASS**

**Notes:**
- Returned 6 result(s)

**Sample Results:**
```json
[
  {
    "value": 3903,
    "date_implemented_year": "2025"
  },
  {
    "value": 2760,
    "date_implemented_year": "No implementation date"
  },
  {
    "value": 4,
    "date_implemented_year": "2026"
  }
]
```

<details>
<summary>Request Body</summary>

```json
{
  "request_data": {
    "gta_evaluation": [
      1,
      2
    ],
    "implementation_period": [
      "2025-01-01",
      "2025-12-31"
    ],
    "count_by": [
      "date_implemented_year"
    ],
    "count_variable": "intervention_id"
  }
}
```
</details>

### Prompt 16b: How many harmful interventions were implemented globally in 2024?

- **Endpoint:** `counts`
- **HTTP Status:** 200
- **Result Count:** 6
- **Response Time:** 2.66s
- **Verdict:** **PASS**

**Notes:**
- Returned 6 result(s)

**Sample Results:**
```json
[
  {
    "value": 4439,
    "date_implemented_year": "2024"
  },
  {
    "value": 2760,
    "date_implemented_year": "No implementation date"
  },
  {
    "value": 7,
    "date_implemented_year": "2025"
  }
]
```

<details>
<summary>Request Body</summary>

```json
{
  "request_data": {
    "gta_evaluation": [
      1,
      2
    ],
    "implementation_period": [
      "2024-01-01",
      "2024-12-31"
    ],
    "count_by": [
      "date_implemented_year"
    ],
    "count_variable": "intervention_id"
  }
}
```
</details>

### Prompt 17: Which interventions target state-owned enterprises specifically?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 50
- **Response Time:** 3.23s
- **Verdict:** **PASS**

**Notes:**
- Returned 50 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 152435,
    "state_act_id": 96262,
    "state_act_title": "India: Customs duty amendments announced as part of 2026-2027 budget",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-04 06:20",
        "text": "<p>On 1 February 2026, the Indian Ministry of Finance, via Notification No. 2/2026-Customs, exempted the customs duty on the imports of raw materials (any HS chapter) for the manufacture of parts of aircraft for maintenance, repair, or overhauling. The exemption is only available to public sector units under the Ministry of Defence and is effective from 2 February 2026 until 31 March 2028.</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/152435?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/96262?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-04 07:10",
        "text": "Ministry of Finance (1 February 2026) Notification No. 2/2026-Customs \nhttps://taxinformation.cbic.gov.in/view-pdf/1010564/ENG/Notifications\n\nBudget Speech\nhttps://www.indiabudget.gov.in/doc/Budget_Speech.pdf"
      }
    ],
    "is_official_source": false,
    "gta_evaluation": "Green",
    "implementing_jurisdictions": [
      {
        "id": 699,
        "name": "India",
        "iso": "IND"
      }
    ],
    "implementing_jurisdiction_groups": [],
    "affected_jurisdictions": [
      {
        "id": 40,
        "name": "Austria",
        "iso": "AUT"
      },
      {
        "id": 56,
        "name": "Belgium",
        "iso": "BEL"
      },
      {
        "id": 124,
        "name": "Canada",
        "iso": "CAN"
      },
      {
        "id": 156,
        "name": "China",
        "iso": "CHN"
      },
      {
        "id": 251,
        "name": "France",
        "iso": "FRA"
      }
    ],
    "_affected_jurisdictions_total": 20,
    "inferred_jurisdictions": "Inferred",
    "implementation_level": "National",
    "eligible_firm": "state-controlled",
    "intervention_type": "Import tariff",
    "mast_chapter": "Tariff measures",
    "mast_subchapter": "Tariff measures",
    "affected_sectors": [
      {
        "sector_id": 496,
        "name": "Aircraft and spacecr..."
      }
    ],
    "affected_products": [
      {
        "product_id": 880710,
        "name": "Aircraft and spacecr...",
        "prior_level": "2.5",
        "new_level": "0",
        "unit": "percent",
        "date_implemented": "2026-02-02",
        "date_removed": "2028-03-31"
      },
      {
        "product_id": 880720,
        "name": "Aircraft and spacecr...",
        "prior_level": "2.5",
        "new_level": "0",
        "unit": "percent",
        "date_implemented": "2026-02-02",
        "date_removed": "2028-03-31"
      },
      {
        "product_id": 880730,
        "name": "
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "eligible_firms": [
      4
    ],
    "announcement_period": [
      "1900-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 18: What subnational measures has the US implemented since 2023?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 50
- **Response Time:** 1.01s
- **Verdict:** **PASS**

**Notes:**
- Returned 50 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 152717,
    "state_act_id": 96397,
    "state_act_title": "United States of America (Texas): USD 14.1 million grant to Coherent Corp under Texas Semiconductor Innovation Fund",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-10 17:08",
        "text": "<p>On 6 February 2026, the government of the state of Texas announced a USD 14.1 million grant to Coherent Corp through the Texas Semiconductor Innovation Fund. The funding supports the production of Indium Phosphide (InP) wafers at the company's facility in Sherman, Texas.</p><p>According to the press release, the project involves a total capital investment of more than USD 154 million to produce technology used for data communications, telecommunications, artificial intelligence interconnects, and satellite communications.</p><p>In this context, Texas's Governor Greg Abbott said: \u201cTexas is the new frontier for technological innovation. This $154 million investment by Coherent to establish the world\u2019s first 6-inch InP wafer fabrication plant in Sherman is testament to Texas\u2019 leadership in semiconductor manufacturing and the technologies of tomorrow. With our skilled and growing workforce and the best business climate in the nation, Texas is where the future is building.\u201d</p><p><strong>Texas Semiconductor Innovation Fund (TSIF)</strong></p><p>The grant program was launched in 2023 under the Texas CHIPS Act (see related state act). The scheme aims to support Texas\u2019s leadership in semiconductor research, design, and manufacturing.</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/152717?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/96397?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "new",
        "order_nr": 1,
        "modified": "2026-02-10 17:02",
        "text": "Office of the Texas Governor (6 February 2026). Governor Abbott Announces Texas Semiconductor Innovation Fund Grant to Coherent. Press release (10 February 2026): https://gov.texas.gov/news/post/governor-abbott-announces-texas-semiconductor-innovation-fund-grant-to-coherent"
      }
    ],
    "is_official_source": false,
    "gta_evaluation": "Red",
    "implementing_jurisdictions": [
      {
        "id": 840,
        "name": "United States of America",
        "iso": "USA"
      }
    ],
    "implementing_jurisdiction_groups": [],
    "affected_jurisdictions": [
      {
        "id": 56,
        "name": "Belgium",
        "iso": "BEL"
      },
      {
        "id": 124,
        "name": "Canada",
        "iso": "CAN"
      },
      {
        "id": 156,
        "name": "China",
        "iso": "CHN"
      },
      {
        "id": 203,
        "name": "Czechia",
        "iso": "CZE"
      },
      {
        "id": 208,
        "name": "Denmark",
        "iso": "DNK"

```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "implementer": [
      840
    ],
    "implementation_level": [
      3
    ],
    "announcement_period": [
      "2023-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 19: What FDI screening measures target Chinese investments in European technology sectors?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 5
- **Response Time:** 1.26s
- **Verdict:** **PASS**

**Notes:**
- Returned 5 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 151187,
    "state_act_id": 95561,
    "state_act_title": "EU: Commission publishes its new approach to economic security",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2025-12-08 12:25",
        "text": "<p>On 3 December 2025, the European Union published a Joint Communication outlining an approach to safeguarding the bloc\u2019s economic security. The communication identifies six high-risk areas and proposes measures to balance openness with the need to avoid deepening or creating new dependencies. Among others, the Commission calls for measures strengthening the FDI review mechanisms in the EU.</p><p>Specifically, the Commission calls for \"putting in place on a pilot basis an EU-level start-up monitoring mechanism aimed at identifying startups in critical technology areas that are vulnerable to the risk of hostile foreign acquisitions, redirecting them to EU investment alternatives and other forms of support (e.g., advisory, capacity-building, matchmaking with investors).\" The Commission will also \u201cwork with supervisory authorities to monitor portfolio investments (\u2026) in areas identified as high-risk.\u201d</p><p>In addition, the Commission calls for the development of \u201cguidelines drawing on the experience of implementing the current FDI Screening Regulation to ensure national screening authorities approach screening consistently, including in strategic sectors.\u201d These guidelines \u201cwould also set out how to take account of the potential cumulative risk of multiple investments,\u201d and would be complemented by guidance on the \u201cinterplay between any EU level requirements and the application of national screening mechanisms in the financial sector.\u201d For other measures specified in the Joint Communication, see related interventions.</p><p>In this context, St\u00e9phane S\u00e9journ\u00e9, Executive Vice-President for Prosperity and Industrial Strategy, noted: \"In a more volatile and unpredictable world, Europe must update its strategic reflexes and prepare for every possible scenario. Our ability to safeguard the resilience of our economy cannot depend on any single geopolitical configuration. With the launch of the ResourceEU programme, this new doctrine is not just a vision for the future \u2014 it is already operational. We are equipping the Union with the tools it needs to remain strong, adaptable, and sovereign in the face of global uncertainty.\"</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/151187?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/95561?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2025-12-04 16:16",
        "text": "European Commission, European Parliament and Council of the European Union
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "affected": [
      156
    ],
    "intervention_types": [
      25
    ],
    "query": "technology",
    "announcement_period": [
      "1900-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 20: What measures have G7 countries coordinated against Russia since February 2022?

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 50
- **Response Time:** 4.09s
- **Verdict:** **PASS**

**Notes:**
- Returned 50 result(s)

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 152697,
    "state_act_id": 96384,
    "state_act_title": "Italy: EUR 390 million rescue loan to Acciaierie d'Italia",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-11 12:34",
        "text": "<p>On 9 February 2026, the European Commission approved a EUR 390 million (USD 463.5 million) rescue loan from Italy. The measure will support Acciaierie d'Italia (AdI) to meet its liquidity needs and cover standard operating costs such as wages and supplier payments. AdI is an Italian integrated steel producer with eight different production and servicing sites.</p><p>Specifically, the funding addresses the company's projected liquidity shortfall and ensures the continuity of its operations during an ongoing insolvency process that began in 2024 (see related state acts). This support is intended to bridge the financial gap until the business is transferred to a new operator following a tender process. The loan is granted at market rates for a duration of six months, after which Italy must submit a restructuring or liquidation plan or demonstrate that the loan has been repaid.</p><p>The Commission approved the rescue loan after assessing it under Article 107(3)(c) of the Treaty on the Functioning of the European Union (TFEU).</p><p>As of February 2026, the European Commission has not published its decision.</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/152697?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/96384?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-10 22:19",
        "text": "European Commission (9 February 2026). Commission approves \u20ac390 million Italian rescue loan to Acciaierie d'Italia under EU State aid rules (Retrieved on 10 February 2026): https://ec.europa.eu/commission/presscorner/detail/en/ip_26_328"
      }
    ],
    "is_official_source": false,
    "gta_evaluation": "Red",
    "implementing_jurisdictions": [
      {
        "id": 381,
        "name": "Italy",
        "iso": "ITA"
      }
    ],
    "implementing_jurisdiction_groups": [],
    "affected_jurisdictions": [
      {
        "id": 12,
        "name": "Algeria",
        "iso": "DZA"
      },
      {
        "id": 56,
        "name": "Belgium",
        "iso": "BEL"
      },
      {
        "id": 156,
        "name": "China",
        "iso": "CHN"
      },
      {
        "id": 191,
        "name": "Croatia",
        "iso": "HRV"
      },
      {
        "id": 251,
        "name": "France",
        "iso": "FRA"
      }
    ],
    "_affected_jurisdictions_total": 45,
    "inferred_jurisdictions": "Inferred",
    "implementation_level": "National",
    "eligible_firm": "firm-specific",
    "intervention_type": "State loan",
    "mast_chapter": "L: Subsidies (excl. 
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 50,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "implementer": [
      840,
      826,
      251,
      276,
      381,
      392,
      124
    ],
    "affected": [
      643
    ],
    "announcement_period": [
      "2022-02-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 21: Overview mode -- semiconductor measures (test detail_level=overview via show_keys)

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 500
- **Response Time:** 7.29s
- **Verdict:** **PASS**

**Notes:**
- Returned 500 result(s)
- SHOW_KEYS: Response contains exactly the requested fields
- LIMIT=500: Returned 500 results (more than default 50)

**Response Keys:** `date_announced, gta_evaluation, implementing_jurisdictions, intervention_id, intervention_type, intervention_url, is_in_force, state_act_title`

**Sample Results:**
```json
[
  {
    "intervention_id": 152717,
    "state_act_title": "United States of America (Texas): USD 14.1 million grant to Coherent Corp under Texas Semiconductor Innovation Fund",
    "intervention_url": "https://globaltradealert.org/intervention/152717?key=eba65271-5400-4782-96c3-182099ef163d",
    "gta_evaluation": "Red",
    "implementing_jurisdictions": [
      {
        "id": 840,
        "name": "United States of America",
        "iso": "USA"
      }
    ],
    "intervention_type": "Financial grant",
    "date_announced": "2026-02-06",
    "is_in_force": 1
  },
  {
    "intervention_id": 152307,
    "state_act_title": "China: Government reportedly allows several Chinese firms to import of Nvidia H200 AI chips",
    "intervention_url": "https://globaltradealert.org/intervention/152307?key=eba65271-5400-4782-96c3-182099ef163d",
    "gta_evaluation": "Green",
    "implementing_jurisdictions": [
      {
        "id": 156,
        "name": "China",
        "iso": "CHN"
      }
    ],
    "intervention_type": "Import-related non-tariff measure, nes",
    "date_announced": "2026-01-28",
    "is_in_force": 1
  },
  {
    "intervention_id": 151336,
    "state_act_title": "Republic of Korea: Eximbank announces KRW 22 trillion program to support AI industry",
    "intervention_url": "https://globaltradealert.org/intervention/151336?key=eba65271-5400-4782-96c3-182099ef163d",
    "gta_evaluation": "Red",
    "implementing_jurisdictions": [
      {
        "id": 410,
        "name": "Republic of Korea",
        "iso": "KOR"
      }
    ],
    "intervention_type": "State loan",
    "date_announced": "2026-01-22",
    "is_in_force": 1
  }
]
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 500,
  "offset": 0,
  "sorting": "-date_announced",
  "request_data": {
    "query": "semiconductor",
    "in_force_on_date": "2026-02-12",
    "keep_in_force_on_date": true,
    "announcement_period": [
      "1900-01-01",
      "2099-12-31"
    ]
  },
  "show_keys": [
    "intervention_id",
    "state_act_title",
    "intervention_type",
    "gta_evaluation",
    "date_announced",
    "is_in_force",
    "implementing_jurisdictions",
    "intervention_url"
  ]
}
```
</details>

### Prompt 22: Recently modified interventions (test -last_updated sorting and update_period)

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 20
- **Response Time:** 3.36s
- **Verdict:** **PASS**

**Notes:**
- Returned 20 result(s)
- SORTING: Results are correctly sorted by -last_updated (descending)
- UPDATE_PERIOD: All results have last_updated >= 2026-02-01

**Response Keys:** `affected_jurisdictions, affected_products, affected_sectors, date_announced, date_implemented, date_published, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdiction_groups, implementing_jurisdictions, inferred_jurisdictions, intervention_description, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, last_updated, mast_chapter, mast_subchapter, state_act_id, state_act_source, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 78430,
    "state_act_id": 43202,
    "state_act_title": "India: Extension of definitive antidumping duty on imports of toluene diisocyanate from the EU and Saudi Arabia (definitive antidumping duty expired on imports from Chinese Taipei and the UAE)",
    "intervention_description": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-12 17:59",
        "text": "<p>On&nbsp;31 January 2020, the Indian authorities initiated an antidumping investigation on imports of toluene diisocyanate from the European Union and Saudi Arabia, as well as from Chinese Taipei, and the United Arab Emirates (please see the related intervention). The products subject to investigation are classified under HS code subheading 2929.10.20. The investigation follows the applications lodged by&nbsp;Gujarat Narmada Valley Fertilizers &amp; Chemicals Limited.</p><p>On 27 April 2021, the Indian authorities imposed a&nbsp;definitive antidumping on imports of toluene diisocyanate from the European Union and Saudi Arabia. The rate of duty on imports from the European Union ranges from USD 102.05 per MT to USD 264.96 per MT depending on the company. The rate of duty on imports from Saudi Arabia ranges from USD 217.55 per MT to USD 344.33 per MT depending on the company.</p><p>On 30 December 2024, the Indian authorities announced the initiation of a sunset review of the definitive duty imposed on imports of the subject good from the European Union and Saudi Arabia. This follows the application lodged&nbsp;by Gujarat Nmmada Valley Fertilizers &amp; Chemicals Limited.</p>"
      },
      {
        "status": "changed",
        "order_nr": 2,
        "modified": "2026-02-12 17:59",
        "text": "<p>On 20 August 2025, the Indian authorities extended the definitive duty on imports of the subject good from the European Union and Saudi Arabia until 1 March 2026 following the initiation of the sunset review.</p>"
      },
      {
        "status": "changed",
        "order_nr": 3,
        "modified": "2026-02-12 17:59",
        "text": "<p>On 10 February 2026, the Indian authorities extended the definitive duty imposed on imports of the subject good from the European Union and Saudi Arabia following the conclusion of the sunset review. The rate of duty remains unchanged. The definitive duty is in force for a period of five years.</p>"
      }
    ],
    "intervention_url": "https://globaltradealert.org/intervention/78430?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/43202?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_source": [
      {
        "status": "changed",
        "order_nr": 1,
        "modified": "2026-02-12 17:52",
        "text": "Government of India, Ministry of Commerce and Industry, Department of Commerce, Directorate General of Trade Remedies, File No. 6/43/2019-DGTR, 31 January 2020: http://www.dgtr.gov.in/sites/default/files/TDI%20I
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 20,
  "offset": 0,
  "sorting": "-last_updated",
  "request_data": {
    "update_period": [
      "2026-02-01",
      null
    ],
    "announcement_period": [
      "1900-01-01",
      "2099-12-31"
    ]
  }
}
```
</details>

### Prompt 23: Standard detail for specific IDs: [152717, 152307, 151336, 152386, 152078]

- **Endpoint:** `data`
- **HTTP Status:** 200
- **Result Count:** 5
- **Response Time:** 0.72s
- **Verdict:** **PASS**

**Notes:**
- Returned 5 result(s)
- SHOW_KEYS: Response contains exactly the requested standard fields
- IDs: All 5 requested intervention IDs are present

**Response Keys:** `affected_jurisdictions, affected_sectors, date_announced, date_implemented, date_removed, eligible_firm, gta_evaluation, implementation_level, implementing_jurisdictions, intervention_id, intervention_type, intervention_url, is_in_force, is_official_source, mast_chapter, state_act_id, state_act_title, state_act_url`

**Sample Results:**
```json
[
  {
    "intervention_id": 151336,
    "state_act_id": 95663,
    "state_act_title": "Republic of Korea: Eximbank announces KRW 22 trillion program to support AI industry",
    "intervention_url": "https://globaltradealert.org/intervention/151336?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/95663?key=eba65271-5400-4782-96c3-182099ef163d",
    "is_official_source": false,
    "gta_evaluation": "Red",
    "implementing_jurisdictions": [
      {
        "id": 410,
        "name": "Republic of Korea",
        "iso": "KOR"
      }
    ],
    "affected_jurisdictions": [
      {
        "id": 156,
        "name": "China",
        "iso": "CHN"
      },
      {
        "id": 276,
        "name": "Germany",
        "iso": "DEU"
      },
      {
        "id": 381,
        "name": "Italy",
        "iso": "ITA"
      },
      {
        "id": 392,
        "name": "Japan",
        "iso": "JPN"
      },
      {
        "id": 528,
        "name": "Netherlands",
        "iso": "NLD"
      }
    ],
    "_affected_jurisdictions_total": 51,
    "implementation_level": "NFI",
    "eligible_firm": "all",
    "intervention_type": "State loan",
    "mast_chapter": "L: Subsidies (excl. export subsidies)",
    "affected_sectors": [
      {
        "sector_id": 435,
        "name": "Lifting and handling..."
      },
      {
        "sector_id": 449,
        "name": "Other special-purpos..."
      },
      {
        "sector_id": 471,
        "name": "Electronic valves an..."
      },
      {
        "sector_id": 475,
        "name": "Disks, tapes, solid-..."
      },
      {
        "sector_id": 476,
        "name": "Audio, video and oth..."
      }
    ],
    "_affected_sectors_total": 6,
    "date_announced": "2026-01-22",
    "date_implemented": "2026-01-22",
    "date_removed": "2031-01-21",
    "is_in_force": 1
  },
  {
    "intervention_id": 152078,
    "state_act_id": 96098,
    "state_act_title": "United Kingdom: British Business Bank commits GBP 50 million to IQ Capital Fund V for deeptech investments",
    "intervention_url": "https://globaltradealert.org/intervention/152078?key=eba65271-5400-4782-96c3-182099ef163d",
    "state_act_url": "https://www.globaltradealert.org/state-act/96098?key=eba65271-5400-4782-96c3-182099ef163d",
    "is_official_source": false,
    "gta_evaluation": "Red",
    "implementing_jurisdictions": [
      {
        "id": 826,
        "name": "United Kingdom",
        "iso": "GBR"
      }
    ],
    "affected_jurisdictions": [
      {
        "id": 156,
        "name": "China",
        "iso": "CHN"
      },
      {
        "id": 699,
        "name": "India",
        "iso": "IND"
      },
      {
        "id": 56,
        "name": "Belgium",
        "iso": "BEL"
      },
      {
        "id": 276,
        "name": "Germany",
        "iso": "DEU"
      },
      {
        "id": 376,
        "name": "Israel",
        "iso": "ISR"
      }
    ],
    "_affected_jurisdictions_total": 8
```

<details>
<summary>Request Body</summary>

```json
{
  "limit": 5,
  "offset": 0,
  "request_data": {
    "intervention_id": [
      152717,
      152307,
      151336,
      152386,
      152078
    ],
    "announcement_period": [
      "1900-01-01",
      "2099-12-31"
    ]
  },
  "show_keys": [
    "intervention_id",
    "state_act_id",
    "state_act_title",
    "intervention_type",
    "mast_chapter",
    "gta_evaluation",
    "implementation_level",
    "eligible_firm",
    "date_announced",
    "date_implemented",
    "date_removed",
    "is_in_force",
    "implementing_jurisdictions",
    "affected_jurisdictions",
    "affected_sectors",
    "intervention_url",
    "state_act_url",
    "is_official_source"
  ]
}
```
</details>

---

## New Feature Verification (Prompts 21-23)

### Prompt 21: Overview mode -- semiconductor measures (test detail_level=overview via show_key

- **Verdict:** **PASS**
- Returned 500 result(s)
- SHOW_KEYS: Response contains exactly the requested fields
- LIMIT=500: Returned 500 results (more than default 50)

### Prompt 22: Recently modified interventions (test -last_updated sorting and update_period)

- **Verdict:** **PASS**
- Returned 20 result(s)
- SORTING: Results are correctly sorted by -last_updated (descending)
- UPDATE_PERIOD: All results have last_updated >= 2026-02-01

### Prompt 23: Standard detail for specific IDs: [152717, 152307, 151336, 152386, 152078]

- **Verdict:** **PASS**
- Returned 5 result(s)
- SHOW_KEYS: Response contains exactly the requested standard fields
- IDs: All 5 requested intervention IDs are present

---

## Overall Assessment

All prompts passed successfully. The GTA MCP server's API integration is working correctly for all 23 test cases.
