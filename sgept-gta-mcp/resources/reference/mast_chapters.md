# GTA MAST Chapter Reference

## Overview

UN MAST (Multi-Agency Support Team) chapters provide standardized classification of **non-tariff measures** ranging from import quotas to subsidies, localization requirements, investment actions, and beyond.

### When to Use MAST Chapters

**Use `mast_chapters` when:**
- Query is **generic**: "subsidies", "trade barriers", "export controls"
- Need **comprehensive coverage**: All subsidy types, not just one specific type
- **Broad analysis**: All measures within a category (e.g., all Chapter L measures)
- User asks about policy **categories** rather than specific instruments

**Use `intervention_types` instead when:**
- Query is **specific**: "Import tariff", "State aid", "Export ban"
- Need **precision**: Only exact measure types, not the broader category
- **Narrow filtering**: Specific intervention type required
- User asks about a **named policy instrument**

**Example Decision Tree:**
```
User asks: "Find all subsidies from Germany"
→ Use: mast_chapters=['L']  ✅ (broad - covers all subsidy types)

User asks: "Find German state aid measures"
→ Use: intervention_types=['State aid']  ✅ (specific - one subsidy type)

User asks: "Find import barriers affecting US"
→ Use: mast_chapters=['E', 'F']  ✅ (broad - multiple barrier types)

User asks: "Find import tariffs on Chinese goods"
→ Use: intervention_types=['Import tariff']  ✅ (specific - one barrier type)
```

---

## MAST Chapter Taxonomy (A-P)

### Technical Measures (A-C)

#### Chapter A: Sanitary and Phytosanitary Measures (SPS)

**ID**: 1 | **Letter**: A | **Category**: Technical

**Description:** Measures to protect human, animal, or plant life/health from risks arising from additives, contaminants, toxins, disease-causing organisms, or pests.

**Covers:**
- Food safety standards and testing requirements
- Animal health controls and disease prevention
- Plant health regulations and phytosanitary certificates
- Quarantine protocols and inspection requirements
- Maximum residue limits (MRLs) for pesticides
- Veterinary drug controls
- Certification and approval procedures

**Use Cases:**
- Agricultural import restrictions based on health concerns
- Food safety regulations and testing mandates
- Biosecurity measures and quarantine requirements
- Pest control and disease prevention measures

**Examples:**
```python
# All SPS measures globally
mast_chapters=['A']

# SPS measures affecting agricultural imports to EU
mast_chapters=['A']
implementing_jurisdictions=['EU']

# Health standards on meat products
mast_chapters=['A']
affected_products=[020110, 020120, 020130]  # Beef HS codes
```

---

#### Chapter B: Technical Barriers to Trade (TBT)

**ID**: 2 | **Letter**: B | **Category**: Technical

**Description:** Technical regulations, standards, testing, and certification requirements that products must meet to enter or be sold in a market.

**Covers:**
- Product standards and technical specifications
- Labeling and marking requirements
- Packaging regulations
- Testing and certification procedures
- Conformity assessment requirements
- Quality and performance standards
- Origin marking requirements

**Use Cases:**
- Technical product regulations and standards
- Labeling and packaging requirements
- Certification and testing mandates
- Quality control measures

**Examples:**
```python
# All TBT measures affecting electronics
mast_chapters=['B']
affected_sectors=['Computing machinery', 'Telecommunications equipment']

# EU technical regulations
mast_chapters=['B']
implementing_jurisdictions=['EU']

# Product testing requirements for medical devices
mast_chapters=['B']
affected_products=[901890]  # Medical instruments HS code
```

---

#### Chapter C: Pre-shipment Inspection and Other Formalities

**ID**: 17 | **Letter**: C | **Category**: Technical

**Description:** Requirements for verification of quality, quantity, price, or customs classification before shipment, plus other customs and administrative formalities.

**Covers:**
- Pre-shipment inspection (PSI) requirements
- Quality and quantity verification
- Price verification procedures
- Customs formalities and documentation
- Certificate of origin requirements
- Import/export licensing procedures

**Use Cases:**
- Inspection requirements before goods leave origin country
- Customs clearance procedures and documentation
- Quality verification mandates

**Examples:**
```python
# All pre-shipment inspection requirements
mast_chapters=['C']

# Customs formalities affecting imports to specific country
mast_chapters=['C']
affected_jurisdictions=['IND']
```

---

### Non-Technical Measures (D-P)

#### Chapter D: Contingent Trade-Protective Measures

**ID**: 3 | **Letter**: D | **Category**: Trade Defense

**Description:** Trade defense instruments applied contingently based on specific conditions (unfair trade, injury, or surge in imports).

**Covers:**
- Anti-dumping duties
- Countervailing duties (anti-subsidy measures)
- Safeguard measures (emergency import restrictions)
- Special safeguards (for agriculture)

**Use Cases:**
- Trade defense investigations and measures
- Anti-dumping and countervailing duty cases
- Emergency import restrictions (safeguards)
- Responses to unfair trade practices

**Examples:**
```python
# All trade defense measures globally
mast_chapters=['D']

# US anti-dumping measures against China
mast_chapters=['D']
implementing_jurisdictions=['USA']
affected_jurisdictions=['CHN']

# Steel safeguards
mast_chapters=['D']
affected_sectors=['Basic iron and steel']
date_announced_gte='2018-01-01'
```

---

#### Chapter E: Non-Automatic Licensing, Quotas, Prohibitions

**ID**: 4 | **Letter**: E | **Category**: Quantitative Restrictions

**Description:** Quantitative restrictions and administrative measures controlling the volume or value of imports/exports.

**Covers:**
- Import/export licensing requirements
- Import/export quotas (quantitative restrictions)
- Import/export prohibitions and bans
- Tariff-rate quotas (TRQs)
- Voluntary export restraints (VERs)
- Seasonal restrictions

**Use Cases:**
- Import/export bans and prohibitions
- Licensing requirements for controlled goods
- Quota systems limiting import volumes
- Quantitative restrictions on trade flows

**Examples:**
```python
# All import restrictions (quotas, bans, licenses)
mast_chapters=['E']

# Export bans from Russia
mast_chapters=['E']
implementing_jurisdictions=['RUS']

# Import quotas on agricultural products
mast_chapters=['E']
affected_sectors=[11, 12, 13, 21, 22]  # Agricultural CPC sectors
```

---

#### Chapter F: Price-Control Measures

**ID**: 5 | **Letter**: F | **Category**: Price Intervention

**Description:** Administrative measures that directly influence import/export prices.

**Covers:**
- Minimum import prices
- Reference prices for customs valuation
- Variable import levies
- Customs valuation methods
- Price investigations
- Administrative pricing measures

**Use Cases:**
- Minimum price requirements for imports
- Price-based trade barriers
- Customs valuation disputes
- Variable levy systems

**Examples:**
```python
# All price control measures
mast_chapters=['F']

# EU minimum import prices
mast_chapters=['F']
implementing_jurisdictions=['EU']

# Price controls affecting agricultural imports
mast_chapters=['F']
affected_sectors=[11, 12, 21, 22]
```

---

#### Chapter G: Finance Measures

**ID**: 6 | **Letter**: G | **Category**: Financial Conditions

**Description:** Financial terms and conditions affecting international trade transactions.

**Covers:**
- Payment terms requirements
- Advance payment obligations
- Credit restrictions
- Restrictions on terms of payment
- Foreign exchange controls affecting trade

**Use Cases:**
- Payment term requirements for imports
- Credit restrictions on trade financing
- Financial conditions of trade

**Examples:**
```python
# All finance measures affecting trade
mast_chapters=['G']

# Payment term restrictions
mast_chapters=['G']
implementing_jurisdictions=['ARG', 'BRA']
```

---

#### Chapter H: Anti-Competitive Measures

**ID**: 7 | **Letter**: H | **Category**: Competition

**Description:** State measures creating monopolies or exclusive rights that restrict competition.

**Covers:**
- State trading enterprises (STEs)
- State monopolies on imports/exports
- Exclusive import/export rights
- Single-desk selling arrangements
- Compulsory national services

**Use Cases:**
- State monopolies and exclusive trading rights
- Competition restrictions in trade
- State trading enterprise requirements

**Examples:**
```python
# All anti-competitive measures
mast_chapters=['H']

# State monopolies in agricultural trade
mast_chapters=['H']
affected_sectors=[11, 12, 13, 21, 22]
```

---

#### Chapter I: Trade-Related Investment Measures

**ID**: 8 | **Letter**: I | **Category**: Investment

**Description:** Investment measures that restrict or distort trade flows.

**Covers:**
- Local content requirements (LCRs)
- Trade balancing requirements
- Foreign exchange restrictions on trade
- Export performance requirements
- Domestic sales requirements

**Use Cases:**
- Local content and localization requirements
- Investment conditions affecting trade
- Trade balancing obligations

**Examples:**
```python
# All trade-related investment measures
mast_chapters=['I']

# Local content requirements in automotive
mast_chapters=['I']
affected_sectors=['Motor vehicles', 'Transport equipment']

# Localization requirements globally
mast_chapters=['I']
date_announced_gte='2020-01-01'
```

---

#### Chapter J: Distribution Restrictions

**ID**: 9 | **Letter**: J | **Category**: Distribution

**Description:** Restrictions on distribution channels, retail, and resale of imported products.

**Covers:**
- Geographic distribution restrictions
- Authorized dealer requirements
- Exclusive distribution networks
- Resale price maintenance
- Retail location restrictions

**Use Cases:**
- Distribution channel requirements
- Authorized dealer mandates
- Geographic sales restrictions

**Examples:**
```python
# All distribution restrictions
mast_chapters=['J']

# Distribution requirements for pharmaceuticals
mast_chapters=['J']
affected_sectors=['Pharmaceuticals']
```

---

#### Chapter K: Restrictions on Post-Sales Services

**ID**: 18 | **Letter**: K | **Category**: After-Sales

**Description:** Requirements and restrictions on warranty, repair, and maintenance services.

**Covers:**
- Warranty obligations
- Repair and maintenance requirements
- After-sales service mandates
- Spare parts availability requirements

**Use Cases:**
- Warranty and repair service requirements
- After-sales service obligations

**Examples:**
```python
# All post-sales service restrictions
mast_chapters=['K']

# Warranty requirements for vehicles
mast_chapters=['K']
affected_sectors=['Motor vehicles']
```

---

#### Chapter L: Subsidies and Other Forms of Support

**ID**: 10 | **Letter**: L | **Category**: Subsidies

**Description:** All forms of government financial support and subsidies benefiting production or trade.

**Covers:**
- Export subsidies
- Domestic production subsidies
- State aid and grants
- Tax breaks and tax incentives
- Concessional loans and loan guarantees
- Equity injections
- In-kind support
- Bailouts and rescue packages

**Use Cases:**
- **ANY subsidy-related queries** (most comprehensive coverage)
- State aid and government support programs
- Export incentive programs
- Production subsidies and domestic support

**Examples:**
```python
# All subsidies globally (BROAD)
mast_chapters=['L']

# US subsidies in 2024
mast_chapters=['L']
implementing_jurisdictions=['USA']
date_announced_gte='2024-01-01'

# EV subsidies (broad search)
mast_chapters=['L']
query='electric | EV'
affected_sectors=['Motor vehicles']

# Specific state aid measures (NARROW - use intervention_types instead)
intervention_types=['State aid']  # More precise than mast_chapters=['L']
```

**⚠️ IMPORTANT**: Chapter L is the **most commonly used MAST chapter**. Use it for any generic subsidy questions.

---

#### Chapter M: Government Procurement Restrictions

**ID**: 11 | **Letter**: M | **Category**: Procurement

**Description:** Discriminatory government procurement practices and "Buy National" policies.

**Covers:**
- Local preferences in public procurement
- Buy National policies
- Closed tendering procedures
- Discriminatory bidding requirements
- Set-asides for domestic suppliers
- Price preferences for local bidders

**Use Cases:**
- Government procurement restrictions
- Buy National policies (Buy American, Buy Chinese, etc.)
- Public tender discrimination
- Preferential procurement measures

**Examples:**
```python
# All government procurement restrictions
mast_chapters=['M']

# Buy American provisions
mast_chapters=['M']
implementing_jurisdictions=['USA']
query='Buy American | Made in America'

# EU procurement restrictions
mast_chapters=['M']
implementing_jurisdictions=['EU']
date_announced_gte='2020-01-01'
```

---

#### Chapter N: Intellectual Property

**ID**: 12 | **Letter**: N | **Category**: IP

**Description:** Intellectual property protection requirements and technology transfer rules.

**Covers:**
- Patent requirements and protection
- Trademark and branding rules
- Copyright and design protections
- Trade secret regulations
- Geographical indications (GIs)
- Technology transfer requirements
- Forced technology transfer

**Use Cases:**
- IP protection measures
- Technology transfer requirements
- Patent and trademark regulations
- Trade secret protections

**Examples:**
```python
# All IP-related measures
mast_chapters=['N']

# Technology transfer requirements
mast_chapters=['N']
query='technology transfer | forced transfer'

# Patent regulations affecting pharmaceuticals
mast_chapters=['N']
affected_sectors=['Pharmaceuticals']
```

---

#### Chapter O: Rules of Origin

**ID**: 13 | **Letter**: O | **Category**: Origin

**Description:** Criteria and requirements for determining the nationality of products.

**Covers:**
- Origin determination criteria
- Local content requirements for origin
- Substantial transformation rules
- Origin certification requirements
- Preferential origin rules

**Use Cases:**
- Rules of origin requirements
- Local content for origin determination
- Origin certification measures

**Examples:**
```python
# All rules of origin measures
mast_chapters=['O']

# Origin requirements in FTAs
mast_chapters=['O']
implementing_jurisdictions=['USA', 'MEX', 'CAN']  # USMCA
```

---

#### Chapter P: Export-Related Measures

**ID**: 14 | **Letter**: P | **Category**: Export Controls

**Description:** Measures restricting or controlling exports.

**Covers:**
- Export taxes and duties
- Export bans and prohibitions
- Export licensing requirements
- Export quotas and restrictions
- Export controls on strategic goods
- Technology export controls

**Use Cases:**
- Export bans and restrictions
- Export taxes and duties
- Strategic goods export controls
- Technology export restrictions

**Examples:**
```python
# All export-related measures
mast_chapters=['P']

# Export controls from US
mast_chapters=['P']
implementing_jurisdictions=['USA']

# Technology export controls
mast_chapters=['P']
query='semiconductor | chip | AI | quantum'
date_announced_gte='2022-01-01'

# Export bans affecting specific countries
mast_chapters=['P']
affected_jurisdictions=['RUS', 'CHN']
```

---

### Special Categories (Non-Standard MAST)

Beyond the standard A-P chapters, GTA includes special cross-cutting categories:

#### Capital Control Measures

**ID**: 15 | **Category**: Special

**Description:** Capital account restrictions and exchange controls.

**Usage:**
```python
mast_chapters=['Capital control measures']
```

#### FDI Measures

**ID**: 16 | **Category**: Special

**Description:** Foreign direct investment regulations and restrictions.

**Usage:**
```python
mast_chapters=['FDI measures']
```

#### Migration Measures

**ID**: 19 | **Category**: Special

**Description:** Labor mobility and migration policies affecting trade.

**Usage:**
```python
mast_chapters=['Migration measures']
```

#### Tariff Measures

**ID**: 20 | **Category**: Special

**Description:** Tariff and customs duty measures (distinct from MAST focus on non-tariff measures).

**Usage:**
```python
mast_chapters=['Tariff measures']
```

---

## Format Reference

### Accepted Input Formats

The `mast_chapters` parameter accepts three formats:

#### 1. Letters (Recommended)
```python
mast_chapters=['A', 'B', 'L']  # SPS, TBT, Subsidies
```

#### 2. Integer IDs
```python
mast_chapters=[1, 2, 10]  # Same as above
# or as strings:
mast_chapters=['1', '2', '10']
```

#### 3. Special Category Names
```python
mast_chapters=['Capital control measures', 'FDI measures']
```

### Letter-to-ID Mapping Table

⚠️ **Important**: MAST chapter IDs are NON-ALPHABETICAL. The mapping is NOT A=1, B=2, C=3.

| Letter | ID | Chapter Name |
|--------|----|--------------|
| A | 1 | Sanitary and phytosanitary measures |
| B | 2 | Technical barriers to trade |
| C | **17** | Pre-shipment inspection ⚠️ |
| D | 3 | Contingent trade-protective measures |
| E | 4 | Non-automatic licensing, quotas, prohibitions |
| F | 5 | Price-control measures |
| G | 6 | Finance measures |
| H | 7 | Anti-competitive measures |
| I | 8 | Trade-related investment measures |
| J | 9 | Distribution restrictions |
| K | **18** | Restrictions on post-sales services ⚠️ |
| L | 10 | Subsidies and other forms of support |
| M | 11 | Government procurement restrictions |
| N | 12 | Intellectual property |
| O | 13 | Rules of origin |
| P | 14 | Export-related measures |

**Special Categories:**
- Capital control measures: ID 15
- FDI measures: ID 16
- Migration measures: ID 19
- Tariff measures: ID 20

---

## Quick Reference: Most Common Chapters

### Top 5 Most Used MAST Chapters

1. **L (Subsidies)** - All government support measures
2. **P (Export controls)** - Export bans, restrictions, duties
3. **E (Quotas/Bans)** - Import restrictions, licenses, prohibitions
4. **D (Trade defense)** - Anti-dumping, safeguards
5. **M (Procurement)** - Buy National policies

### Common Query Patterns

```python
# Broad subsidy search
mast_chapters=['L']

# All trade barriers (import restrictions + price controls)
mast_chapters=['E', 'F']

# Technical regulations (SPS + TBT)
mast_chapters=['A', 'B']

# Export controls and restrictions
mast_chapters=['P']

# Localization (investment + procurement + origin)
mast_chapters=['I', 'M', 'O']

# Trade defense measures
mast_chapters=['D']
```

---

## Related Resources

- **Intervention Types**: See `gta://reference/intervention-types` for specific measure types within MAST chapters
- **Query Examples**: See `gta://guide/query-examples` for more MAST chapter usage examples
- **Parameters Guide**: See `gta://guide/parameters` for parameter selection strategy
- **Search Guide**: See `gta://guide/searching` for comprehensive search strategies

---

**Last Updated**: 2025-01-09
