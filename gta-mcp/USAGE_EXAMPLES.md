# GTA MCP Server - Usage Examples

Real-world query patterns for SGEPT's rapid response analytical work.

## Rapid Response Scenarios

### Chinese Rare Earth Export Controls

**Your workflow**: Hours after China announces new rare earth export restrictions, you need historical context and cross-government comparisons.

**Query to Claude:**
```
Using the GTA tools:

1. Search for all Chinese export controls on rare earth products (HS codes: 280530, 
   280519, 250400) announced in the last 12 months
2. Get full details including sources for the 3 most recent interventions
3. Compare with similar measures by US and Australia - search for export restrictions 
   by these countries on rare earth products in the last 5 years
```

**What happens:**
- Claude calls `gta_search_interventions` with Chinese jurisdiction filter + product codes + date filter
- Gets intervention IDs and summaries
- Calls `gta_get_intervention` for detailed info on top 3
- Repeats search for US and Australia with broader date range
- Synthesizes comparison table with implementation dates, evaluation, sources

### Section 232 Inclusion Requests

**Your workflow**: When new Section 232 inclusion requests are filed, you need rapid context on similar past requests and outcomes.

**Query to Claude:**
```
Search GTA for all US interventions classified as "Import tariff" with "Section 232" 
mentioned in the title or description from 2018 onwards. 

For each result, extract:
- Product categories affected (HS codes)
- Announcement vs implementation timeline
- GTA evaluation (harmful/mixed/liberalizing)
- Current status (in force or removed)
- Sources

Format as a timeline table.
```

**What happens:**
- Claude searches with `implementing_jurisdictions: ["USA"]`, `intervention_types: ["Import tariff"]`, `date_announced_gte: "2018-01-01"`
- Filters results containing "Section 232" (Claude does this filtering)
- Calls `gta_get_intervention` for detailed info on relevant cases
- Creates structured timeline with all requested fields

### EU Goods Availability Act Analysis

**Your workflow**: Netherlands proposes emergency economic security measures. You need precedent from other EU countries.

**Query to Claude:**
```
Find all EU member state interventions classified under emergency powers or 
economic security measures from 2020-present.

Focus on:
- Which EU countries have used emergency trade powers
- What products were targeted
- How long measures stayed in force
- Official sources for each measure

Prioritize interventions still in force.
```

**What happens:**
- Claude searches with all EU country ISO codes as implementing jurisdictions
- Uses `is_in_force: true` to prioritize active measures
- Filters by date range
- Extracts patterns across countries
- Provides comparative analysis with source links

### Financial Services Restrictions Analysis

**Your workflow**: Bank association requests analysis of financial service barriers implemented by major economies.

**Query to Claude:**
```
Using GTA tools, search for all interventions affecting financial services sectors
implemented by USA, EU, UK, and China from 2020 onwards.

NOTE: Financial services are NOT in HS codes - they require CPC sector classification.

Provide:
- Breakdown by implementing country
- Types of restrictions (licensing, local operations, etc.)
- Current status (in force vs removed)
- Cross-border service implications
```

**What happens:**
- Claude recognizes this is a SERVICE query and uses CPC sectors (not HS codes)
- Searches with `affected_sectors: ["Financial services"]` (ID 711-717)
- Filters by implementing jurisdictions and date range
- Uses `gta_get_intervention` for detailed analysis of key measures
- Synthesizes insights on regulatory barriers to cross-border financial services

### Industry Association Outreach

**Your workflow**: VDMA asks about recent trade measures affecting machinery exports to China.

**Query to Claude:**
```
Search GTA for interventions where:
- Affected jurisdiction is China (CHN)
- Affected products are in machinery categories (HS codes 8401-8487)
- Announced in the last 6 months
- Evaluated as "Red" (harmful) by GTA

For the top 5 results, provide:
- Implementing country
- Specific HS codes
- Implementation date
- Direct link to GTA page
- Link to official source
```

**What happens:**
- Claude searches with precise filters
- Gets top 5 harmful interventions
- Extracts all requested fields from markdown or JSON response
- Formats for quick email to VDMA

## Data Extraction Patterns

### Bilateral Trade Flows

**Query:**
```
Get impact chains at product level where US is implementing jurisdiction and China 
is affected jurisdiction. Focus on products in electronics (HS 85).

Extract unique product codes and count how many interventions affect each.
```

**Tools used:**
- `gta_get_impact_chains` with `granularity: "product"`, filters for US→China
- Claude processes results to aggregate by product code

### Policy Update Monitoring

**Query:**
```
Check ticker updates from the last 7 days for any changes to US or EU trade measures.

Summarize:
- Which interventions were updated
- Nature of changes (new products added, measures extended, etc.)
- Provide intervention IDs for detailed follow-up
```

**Tools used:**
- `gta_list_ticker_updates` with `date_modified_gte: [7 days ago]`, jurisdiction filters
- Claude summarizes changes and flags significant updates

### Sector-Level Analysis

**Query:**
```
Analyze all subsidies (state aid) implemented globally in 2024 affecting 
semiconductor sector.

Show:
- Count by implementing country
- Total interventions by GTA evaluation (Red/Amber/Green)
- Timeline of announcements
- Aggregate affected jurisdictions
```

**Tools used:**
- `gta_search_interventions` with `intervention_types: ["State aid"]`, sector filters, date range
- Claude aggregates and analyzes results
- May need multiple queries with pagination

## Advanced Filtering

### Complex Multi-Country Analysis

**Query:**
```
Compare trade restrictions implemented by G7 countries (USA, CAN, GBR, FRA, DEU, ITA, JPN) 
vs BRICS countries (BRA, RUS, IND, CHN, ZAF) in 2023-2024.

For each group:
- Total number of interventions
- Breakdown by type (tariff, subsidy, quota, etc.)
- Most affected products by HS code
- Average time from announcement to implementation
```

**Approach:**
- Two searches: one for G7, one for BRICS
- Claude aggregates and compares results
- Uses JSON format for precise data extraction

### Product-Specific Deep Dive

**Query:**
```
For HS product code 292149 (specific pharmaceutical intermediate):

1. Find all interventions affecting this product globally
2. Get impact chains showing exact bilateral flows
3. Identify which implementing jurisdictions apply the highest tariff changes
4. Extract all official sources for measures with tariff increases > 5%
```

**Tools used:**
- `gta_search_interventions` filtered to product
- `gta_get_impact_chains` for bilateral details
- `gta_get_intervention` for detailed source documentation

### Temporal Analysis

**Query:**
```
Track evolution of Chinese export controls over the last 3 years:

- Search for CHN as implementing jurisdiction, intervention type "Export quota" or 
  "Export restriction"
- Group by year (2022, 2023, 2024)
- For each year: count interventions, identify affected product categories
- Use ticker to see how measures were modified over time
```

**Approach:**
- Three searches with annual date ranges
- One ticker search for all Chinese measures
- Claude identifies patterns and trends

## Common Parameter Combinations

### Recent Harmful Measures
```python
{
  "gta_evaluation": ["Red"],
  "date_announced_gte": "2024-01-01",
  "is_in_force": true,
  "limit": 100,
  "response_format": "json"  # For data processing
}
```

### Bilateral Impact
```python
{
  "implementing_jurisdictions": ["USA"],
  "affected_jurisdictions": ["CHN"],
  "date_implemented_gte": "2023-01-01",
  "response_format": "markdown"  # For reporting
}
```

### Product-Specific
```python
{
  "affected_products": [292149, 292229, 292429],  # Multiple HS codes
  "intervention_types": ["Import tariff"],
  "limit": 500,
  "offset": 0  # Paginate if needed
}
```

### CPC Sector - Services
```python
{
  "affected_sectors": ["Financial services", "Legal services"],  # Services (ID >= 500)
  "implementing_jurisdictions": ["USA", "CHN"],
  "date_announced_gte": "2020-01-01",
  "response_format": "markdown"
}
```

### CPC Sector - Broad Product Categories
```python
{
  "affected_sectors": [11, 12, 13],  # Cereals, Vegetables, Fruits
  "intervention_types": ["Import tariff", "Import quota"],
  "mast_chapters": ["E", "F"],  # Non-automatic licensing + price controls
  "date_announced_gte": "2023-01-01"
}
```

### CPC Sector - Mixed Services and Goods
```python
{
  "affected_sectors": [
    841,  # Telecommunications services
    452,  # Computing machinery
    471   # Electronics
  ],
  "affected_jurisdictions": ["CHN", "RUS"],
  "gta_evaluation": ["Red"],
  "response_format": "json"
}
```

### Update Monitoring
```python
{
  "date_modified_gte": "2024-10-15",  # Last week
  "implementing_jurisdictions": ["USA", "CHN", "DEU"],
  "response_format": "markdown"
}
```

## Best Practices for Queries

### 1. Start Broad, Then Narrow
```
"Search for all US tariffs on Chinese products in 2024"
[Gets 200 results]

"Now filter those to only semiconductor products (HS 8541, 8542)"
[Gets 15 results]

"Get full details with sources for the 5 most recent"
[Uses intervention IDs from first search]
```

### 2. Use JSON for Data Processing
```
"Search for all export subsidies by EU countries in 2024, return as JSON. 
Then aggregate by country and intervention type."
```
JSON format gives Claude precise structure for analysis.

### 3. Leverage Pagination for Large Datasets
```
"Search for all interventions affecting China - this might be many results. 
Use pagination to get the first 100, then analyze patterns before deciding 
if we need more."
```

### 4. Combine Tools for Comprehensive Analysis
```
"First search for recent US tariffs, then for each result get the impact chains 
to see exact bilateral product flows, then get full details including sources 
for any with significant tariff increases."
```

### 5. Use Ticker for Monitoring
```
"Show me all updates to trade measures in the last 48 hours, then flag any 
that mention 'semiconductor' or 'critical minerals' for deeper investigation."
```

## Integration with Your Workflow

### Morning Briefing
```
"Using GTA tools, create my morning briefing:
1. Any new interventions announced yesterday by US, EU, or China
2. Any ticker updates to measures I'm tracking (intervention IDs: 138295, 137842, 139103)
3. Highlight anything flagged as 'Red' or affecting semiconductors/rare earths"
```

### Client Response
```
"A journalist asks: 'How many export controls has China implemented this year?' 

Search GTA and provide:
- Exact count
- Month-by-month breakdown
- Product categories most affected
- Comparison to same period last year
- Sources for 3 most significant measures"
```

### Policy Context Document
```
"I need rapid context on emergency trade powers. Search GTA for all interventions 
classified under emergency legislation (any implementing jurisdiction) since 2020.

Create a 2-page briefing with:
- Timeline of use
- Which countries invoked emergency powers
- Common justifications (from descriptions)
- How long measures typically lasted
- Include all source links"
```

---

**Key insight**: These queries work because the MCP server handles the complexity (authentication, pagination, formatting, error handling) while Claude orchestrates the analytical workflow. You focus on the questions, not the API mechanics.
