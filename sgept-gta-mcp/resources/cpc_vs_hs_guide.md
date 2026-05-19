# CPC Sectors vs HS Codes: When to Use Which?

## Quick Decision Guide

Use this guide to choose the right product classification for your GTA queries.

### Use **CPC Sectors** when:
- ✅ Querying about **services** (financial, legal, transport, education, etc.)
- ✅ Need **broad product categories** (e.g., "all cereals", "all machinery")
- ✅ Want **comprehensive coverage** of a product range
- ✅ Querying cross-cutting categories that span multiple specific products

### Use **HS Codes** when:
- ✅ Need **specific product details** (e.g., "dutiable ceramic tableware")
- ✅ Tracking **particular goods** with precise definitions
- ✅ Working with existing HS code data
- ✅ Need alignment with customs/trade data

---

## Understanding the Classifications

### CPC (Central Product Classification)
- **Scope**: Both goods AND services
- **Structure**: Hierarchical, 5-digit codes
- **Coverage**: ~2,000 categories
- **Services**: Sectors with ID >= 500
- **Goods**: Sectors with ID < 500
- **Best for**: Broad analysis, services, economic statistics

### HS (Harmonized System)
- **Scope**: Goods ONLY (no services)
- **Structure**: 6-digit codes (international standard)
- **Coverage**: ~5,000 product categories
- **Services**: NOT COVERED
- **Best for**: Customs, specific goods, tariff analysis

---

## Key Rule: Services REQUIRE CPC Sectors

**Services cannot be classified using HS codes.**

If your query involves ANY of these, you MUST use CPC sectors (ID >= 500):

### Financial Services (711-717)
- Banking, insurance, pension services
- Investment services
- Financial intermediation

### Professional Services (821-839)
- Legal, accounting, auditing
- Management consulting
- Engineering, architectural services
- Advertising, market research

### Transport Services (641-679)
- Passenger transport
- Freight transport
- Warehousing, cargo handling
- Transport support services

### Telecommunications (841-846)
- Telephony services
- Internet services
- Broadcasting services

### Education (921-929)
- All levels of education
- Training services

### Health Services (931-935)
- Medical services
- Hospital services
- Social care services

### Other Services
- Real estate (721-722)
- Rental and leasing (731-732)
- R&D services (811-814)
- Government services (911-913)
- Entertainment and recreation (961-969)
- Personal services (971-980)

---

## When to Choose Broader vs. Specific

### Scenario 1: Generic Product Queries
**Question**: "Trade measures affecting agricultural products"

**❌ DON'T**: Try to list hundreds of specific HS codes
**✅ DO**: Use CPC sectors:
- Sectors 11-19 (Crops: Cereals, Vegetables, Fruits, etc.)
- Sectors 21-29 (Livestock products)

### Scenario 2: Specific Product Queries
**Question**: "Tariffs on fresh bananas (HS 080300)"

**✅ DO**: Use HS code directly: `affected_products=[080300]`
**Alternative**: Use CPC sector 13 (Fruits and nuts) for broader coverage

### Scenario 3: Services Queries
**Question**: "Restrictions on financial services"

**✅ MUST**: Use CPC sectors 711-717 (Financial services)
**❌ IMPOSSIBLE**: Cannot use HS codes for services

### Scenario 4: Mixed Goods and Services
**Question**: "Trade barriers affecting both banking and agricultural products"

**✅ DO**: Use CPC sectors for comprehensive coverage:
```
affected_sectors=['Financial services', 'Cereals', 'Livestock']
```
or
```
affected_sectors=[711, 712, 11, 12, 21]
```

---

## Practical Examples

### Example 1: Steel Industry Analysis
```python
# Option A: Broad sector approach (CPC)
affected_sectors=[411, 412]  # Basic iron and steel + Products of iron or steel

# Option B: Specific HS codes (if you need precise product details)
affected_products=[720711, 720712, 730441]  # Specific steel products
```
**Recommendation**: Use CPC for industry-wide analysis, HS for specific products.

### Example 2: Technology Sector
```python
# Services component (MUST use CPC)
affected_sectors=[841, 842]  # Telecommunications, Internet services

# Goods component (can use either)
affected_sectors=[452, 471, 472]  # Computing machinery, Electronics
# OR
affected_products=[847130, 851712]  # Specific HS codes for laptops, phones
```

### Example 3: Food Industry
```python
# Broad categories (CPC recommended)
affected_sectors=[11, 211, 231, 235]  # Cereals, Meat products, Grain mill, Sugar

# Specific products (HS codes)
affected_products=[100630, 020130]  # Rice, Beef cuts
```

---

## Using Fuzzy Matching with CPC Sectors

The MCP server supports fuzzy name matching for CPC sectors:

### By Name (Exact)
```python
affected_sectors=['Cereals', 'Financial services']
```

### By Name (Fuzzy)
```python
affected_sectors=['financial']  # Matches 'Financial services'
affected_sectors=['cereals']    # Matches 'Cereals'
affected_sectors=['steel']      # Matches multiple: 'Basic iron and steel', 'Products of iron or steel'
```

### By ID
```python
affected_sectors=[11, 711, 841]  # Cereals, Financial services, Telecommunications
```

### Mixed
```python
affected_sectors=[11, 'financial services', 412]
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Using HS codes for services
```python
# WRONG - Services don't have HS codes
affected_products=[999999]  # for "financial services"
```
```python
# CORRECT
affected_sectors=[711, 712, 713]  # Financial services
```

### ❌ Mistake 2: Being too specific when you need broad coverage
```python
# WRONG - Missing many relevant interventions
affected_products=[100110]  # Only durum wheat
```
```python
# CORRECT - All cereals
affected_sectors=[11]  # Cereals sector
```

### ❌ Mistake 3: Mixing classifications incorrectly
```python
# WRONG - Inefficient or incomplete
affected_products=[100110]  # Specific wheat HS code
affected_sectors=[11]        # All cereals (includes wheat already)
```
```python
# CORRECT - Use one or the other based on need
affected_sectors=[11]  # For broad analysis
# OR
affected_products=[100110, 100190, 100200]  # For specific wheat types
```

---

## Decision Tree

```
Is your query about SERVICES?
├─ YES → Use CPC Sectors (ID >= 500) ✅
└─ NO → Continue...

Do you need BROAD COVERAGE of a product category?
├─ YES → Use CPC Sectors ✅
└─ NO → Continue...

Do you have SPECIFIC HS CODES or need precise product details?
├─ YES → Use HS Codes ✅
└─ NO → Use CPC Sectors for flexibility ✅
```

---

## Resources

- **View all CPC sectors**: Use `gta://reference/sectors-list` resource
- **View intervention types**: Use `gta://reference/intervention-types-list` resource
- **Search examples**: Use `gta://guide/search-tips` resource

---

## Summary Table

| Aspect | CPC Sectors | HS Codes |
|--------|-------------|----------|
| **Services** | ✅ Yes (ID >= 500) | ❌ No |
| **Goods** | ✅ Yes (ID < 500) | ✅ Yes |
| **Breadth** | Broad categories | Specific products |
| **Total categories** | ~2,000 | ~5,000 |
| **Fuzzy matching** | ✅ Supported | ❌ No |
| **By name** | ✅ Yes | ❌ No (ID only) |
| **Industry analysis** | ✅ Ideal | Possible |
| **Customs/Tariff data** | Possible | ✅ Ideal |

---

*For questions or clarifications, refer to the GTA API documentation or use the MCP server resources.*
