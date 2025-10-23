# DPA MCP Server - Usage Examples

Real-world query patterns and use cases for the Digital Policy Alert MCP server.

## AI Regulation Research

### Example 1: Recent EU AI Regulations

**Query:**
```
Find all AI regulations adopted by the EU in 2024
```

**What Claude will do:**
```
dpa_search_events({
  implementing_jurisdictions: ["DEU", "FRA", "ITA", ...],  // EU member states
  economic_activities: ["ML and AI development"],
  event_period_start: "2024-01-01",
  event_period_end: "2024-12-31",
  limit: 50
})
```

**Use Case:** Tracking the implementation of EU AI Act and related regulations

---

### Example 2: Global AI Governance Frameworks

**Query:**
```
Search for AI governance frameworks and outlines from G20 countries since 2023
```

**What Claude will do:**
```
dpa_search_events({
  implementing_jurisdictions: ["USA", "CHN", "JPN", "DEU", ...],  // G20
  economic_activities: ["ML and AI development"],
  event_types: ["outline"],
  event_period_start: "2023-01-01",
  limit: 100
})
```

**Use Case:** Comparing national AI strategies and non-binding guidance

---

## Data Governance Analysis

### Example 3: Data Localization Requirements

**Query:**
```
Find all data localization requirements globally from the last 2 years with full details
```

**What Claude will do:**
```
dpa_search_events({
  policy_areas: ["Data governance"],
  event_period_start: "2022-01-01",
  limit: 100
})
```

Then filter results mentioning "data localization" or "data residency"

**Use Case:** Understanding global data sovereignty trends

---

### Example 4: GDPR-style Data Protection Laws

**Query:**
```
Search for comprehensive data protection regulations adopted nationally since 2020
```

**What Claude will do:**
```
dpa_search_events({
  policy_areas: ["Data governance"],
  event_types: ["law"],
  dpa_implementation_level: ["national"],
  event_period_start: "2020-01-01",
  limit: 100
})
```

**Use Case:** Tracking global privacy regulation trends

---

## Content Moderation Tracking

### Example 5: Social Media Platform Regulations

**Query:**
```
Recent content moderation laws affecting social media platforms in G20 countries
```

**What Claude will do:**
```
dpa_search_events({
  implementing_jurisdictions: ["USA", "CHN", "JPN", ...],  // G20
  policy_areas: ["Content moderation"],
  economic_activities: ["platform intermediary: user-generated content"],
  event_period_start: "2023-01-01",
  limit: 100
})
```

**Use Case:** Compliance analysis for social media platforms

---

### Example 6: Content Remuneration Policies

**Query:**
```
Find policies requiring platforms to pay content creators or news publishers
```

**What Claude will do:**
```
dpa_search_events({
  policy_areas: ["Content moderation"],
  limit: 100
})
```

Then filter for content remuneration regulations

**Use Case:** Media industry policy analysis

---

## Competition Policy Research

### Example 7: Big Tech Merger Control

**Query:**
```
Search for merger control regulations affecting technology platforms since 2022
```

**What Claude will do:**
```
dpa_search_events({
  policy_areas: ["Competition"],
  economic_activities: ["platform intermediary: user-generated content",
                       "platform intermediary: e-commerce"],
  event_period_start: "2022-01-01",
  limit: 100
})
```

**Use Case:** M&A compliance and antitrust analysis

---

### Example 8: Unilateral Conduct Regulations

**Query:**
```
Find regulations addressing abuse of market power by large digital firms in the EU
```

**What Claude will do:**
```
dpa_search_events({
  implementing_jurisdictions: ["DEU", "FRA", "ITA", ...],  // EU
  policy_areas: ["Competition"],
  event_period_start: "2020-01-01",
  limit: 100
})
```

Then filter for unilateral conduct regulations

**Use Case:** Digital Markets Act compliance

---

## Taxation Research

### Example 9: Digital Service Taxes

**Query:**
```
Search for digital service tax implementations globally
```

**What Claude will do:**
```
dpa_search_events({
  policy_areas: ["Taxation"],
  event_period_start: "2019-01-01",
  limit: 100
})
```

Then filter for direct digital service taxes

**Use Case:** International tax compliance

---

## Cross-Border Data Transfer

### Example 10: Data Transfer Regulations

**Query:**
```
Find cross-border data transfer regulations affecting cloud service providers
```

**What Claude will do:**
```
dpa_search_events({
  policy_areas: ["Data governance"],
  economic_activities: ["infrastructure provider: cloud computing, storage and databases"],
  limit: 100
})
```

Then filter for cross-border data transfer requirements

**Use Case:** Cloud compliance and data flow mapping

---

## Event Lifecycle Tracking

### Example 11: Proposals to Implementation

**Query:**
```
Track the lifecycle of EU Digital Services Act from proposal to implementation
```

**What Claude will do:**
```
dpa_search_events({
  implementing_jurisdictions: ["EU"],
  event_period_start: "2020-01-01",
  limit: 100,
  sorting: "date"  // Chronological order
})
```

Then filter for DSA-related events

**Use Case:** Understanding policy development timelines

---

## Detailed Event Analysis

### Example 12: Deep Dive on Specific Event

**Query:**
```
Get complete details for DPA event 20442 - Singapore AI Governance Framework
```

**What Claude will do:**
```
dpa_get_event({
  event_id: 20442
})
```

**Use Case:** In-depth policy analysis with full context

---

## Multi-Jurisdiction Comparisons

### Example 13: US vs EU Digital Policy

**Query:**
```
Compare digital policy approaches between US and EU in 2024
```

**What Claude will do:**
```
# Search US events
dpa_search_events({
  implementing_jurisdictions: ["USA"],
  event_period_start: "2024-01-01",
  limit: 100
})

# Search EU events
dpa_search_events({
  implementing_jurisdictions: ["DEU", "FRA", ...],  // EU states
  event_period_start: "2024-01-01",
  limit: 100
})
```

**Use Case:** Comparative policy research

---

## Economic Activity Focus

### Example 14: Cryptocurrency Regulations

**Query:**
```
Find all cryptocurrency and digital payment regulations from 2023-2024
```

**What Claude will do:**
```
dpa_search_events({
  economic_activities: ["digital payment provider (incl. cryptocurrencies)"],
  event_period_start: "2023-01-01",
  limit: 100
})
```

**Use Case:** Crypto compliance analysis

---

### Example 15: Semiconductor Supply Chain

**Query:**
```
Search for policies affecting semiconductor industry
```

**What Claude will do:**
```
dpa_search_events({
  economic_activities: ["semiconductors"],
  limit: 100
})
```

**Use Case:** Supply chain security research

---

## Advanced Filtering

### Example 16: Binding Executive Orders

**Query:**
```
Find binding executive orders on AI from the US in 2024
```

**What Claude will do:**
```
dpa_search_events({
  implementing_jurisdictions: ["USA"],
  event_types: ["order"],
  economic_activities: ["ML and AI development"],
  government_branch: ["executive"],
  event_period_start: "2024-01-01",
  limit: 50
})
```

**Use Case:** Specific policy instrument tracking

---

### Example 17: Supranational Agreements

**Query:**
```
Search for international agreements on digital policy
```

**What Claude will do:**
```
dpa_search_events({
  event_types: ["treaty"],
  dpa_implementation_level: ["multilateral agreement", "bi- or plurilateral agreement"],
  limit: 100
})
```

**Use Case:** International cooperation analysis

---

## Pagination Examples

### Example 18: Large Result Sets

**Query:**
```
Get all data governance events from 2024, paginated
```

**What Claude will do:**
```
# First batch
dpa_search_events({
  policy_areas: ["Data governance"],
  event_period_start: "2024-01-01",
  limit: 100,
  offset: 0
})

# Second batch if needed
dpa_search_events({
  policy_areas: ["Data governance"],
  event_period_start: "2024-01-01",
  limit: 100,
  offset: 100
})
```

**Use Case:** Comprehensive dataset retrieval

---

## Best Practices

### Effective Searching

1. **Start broad, then narrow:**
   - First query: General topic and time range
   - Follow-up: Add specific filters based on results

2. **Use date ranges:**
   - Always specify `event_period_start` for recent data
   - Use ranges to focus on relevant periods

3. **Combine filters strategically:**
   - Jurisdiction + Policy Area + Economic Activity = precise results
   - Too many filters = too few results

4. **Check reference lists:**
   - Always review the reference list for related events
   - Follow up on interesting IDs with `dpa_get_event`

### Common Patterns

**Pattern 1: Recent developments**
```
event_period_start: "2024-01-01"
sorting: "-id"  // Newest first
```

**Pattern 2: Specific jurisdiction focus**
```
implementing_jurisdictions: ["USA"]
policy_areas: ["Competition"]
```

**Pattern 3: Economic sector analysis**
```
economic_activities: ["platform intermediary: e-commerce"]
event_period_start: "2023-01-01"
```

**Pattern 4: Policy instrument tracking**
```
policy_areas: ["Data governance"]
event_types: ["law"]  // Only binding laws
```

---

## Next Steps

- Explore [README.md](./README.md) for complete tool documentation
- Check [DPA website](https://digitalpolicyalert.org/) for interactive exploration
- Review [DPA handbook](./resources/dpa_activity_tracking_handbook.md) for methodology

---

**Remember:** All responses include clickable references to DPA website for verification and further research.
