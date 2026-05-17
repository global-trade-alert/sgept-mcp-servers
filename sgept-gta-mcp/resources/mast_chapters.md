# UN MAST Chapter Classifications

The Multi-Agency Support Team (MAST) classification system provides a comprehensive taxonomy for categorizing non-tariff measures (NTMs) in international trade. The system uses 16 main chapters (A-P) to classify different types of trade policy measures.

## When to Use MAST Chapters

**Use `mast_chapters` for:**
- Broad categorization (e.g., "all subsidies", "all import restrictions")
- Generic queries where the user doesn't specify a particular measure type
- Comprehensive searches across related measure types

**Use `intervention_types` for:**
- Specific measure types (e.g., "Import tariff", "State aid")
- Narrow, focused queries
- When the user explicitly mentions a particular intervention type

## MAST Chapter ID Mapping

The GTA API uses integer IDs (1-20) to identify MAST chapters. You can use either letters (A-P) or IDs - the MCP server automatically converts letters to IDs.

### Standard Chapters (A-P)

| Letter | ID | Chapter Name |
|--------|----|--------------|
| A | 1 | Sanitary and phytosanitary measure |
| B | 2 | Technical barriers to trade |
| C | 17 | Pre-shipment inspection and other formalities |
| D | 4 | Contingent trade-protective measures |
| E | 5 | Non-automatic licensing, quotas etc. |
| F | 6 | Price-control measures, including additional taxes and charges |
| G | 8 | Finance measures |
| H | 18 | Measures affecting competition |
| I | 9 | Trade-related investment measures |
| J | 19 | Distribution restrictions |
| K | 20 | Restrictions on post-sales services |
| L | 10 | Subsidies (excl. export subsidies) |
| M | 11 | Government procurement restrictions |
| N | 13 | Intellectual Property |
| P | 14 | Export-related measures (incl. subsidies) |

### Special Categories (Non-Letter)

| ID | Category Name |
|----|--------------|
| 3 | Capital control measures |
| 7 | FDI measures |
| 12 | Migration measures |
| 15 | Tariff measures |
| 16 | Instrument unclear |

**Note:** Special categories can be referenced by their full name (e.g., "Capital control measures") or ID number.

## Accepted Input Formats

When using the `mast_chapters` parameter, you can provide:

1. **Letters (Recommended)**: `['A', 'B', 'L']` - automatically converted to IDs
2. **Integer IDs**: `[1, 2, 10]` or `['1', '2', '10']` - passed directly to API
3. **Special Category Names**: `['Capital control measures', 'FDI measures']` - converted to IDs

## MAST Chapter Reference

### **Technical Measures**

#### **Chapter A: Sanitary and Phytosanitary (SPS) Measures**

This chapter is for researchers looking for policies related to the protection of human, animal, or plant life and health. It covers all measures aimed at ensuring food safety and preventing the spread of diseases and pests. Look here for interventions such as import prohibitions from disease-affected regions, tolerance limits for pesticides or veterinary drugs, food labeling requirements, and quarantine procedures.

**Prominent Intervention Types:**
- Prohibitions for SPS reasons (e.g., bans on poultry from avian flu-affected areas)
- Tolerance limits for residues (e.g., maximum levels of pesticides)
- Food safety-related labeling requirements
- Testing, inspection, and quarantine requirements

**Corresponding GTA Intervention Type(s):**
- Generally outside of GTA scope

---

#### **Chapter B: Technical Barriers to Trade (TBT)**

A researcher should consult this chapter for technical regulations, standards, and conformity assessment procedures not covered by SPS measures. This includes rules on product characteristics, quality, safety, performance, and environmental protection. Examples include labeling requirements for energy efficiency, safety standards for toys, or regulations on the composition of chemicals in consumer goods.

**Prominent Intervention Types:**
- Product quality, safety, or performance requirements
- Labeling, marking, and packaging requirements (e.g., energy efficiency labels)
- Certification of conformity to technical standards
- Testing and inspection to ensure compliance

**Corresponding GTA Intervention Type(s):**
- Generally outside of GTA scope

---

#### **Chapter C: Pre-shipment Inspection and Other Formalities**

This chapter is relevant for researchers investigating procedural obstacles in trade. It covers requirements that goods must undergo before being shipped from the exporting country, such as compulsory inspection of quality, quantity, and price. It also includes rules requiring goods to be shipped directly from the country of origin or to pass through specific customs ports.

**Prominent Intervention Types:**
- Compulsory pre-shipment inspection by a third party
- Direct consignment requirements
- Obligation to pass imports through a specified port of customs
- Import monitoring and surveillance

**Corresponding GTA Intervention Type(s):**
- Entry port restriction
- Import monitoring
- (Other sub-chapters are out of GTA scope)

---

### **Non-technical Measures**

#### **Chapter D: Contingent Trade-Protective Measures**

This chapter details "trade remedy" measures. A researcher should look here for policies that countries implement to protect their domestic industries from what are considered unfair trade practices or surges in imports. This includes anti-dumping duties, countervailing measures to offset foreign subsidies, and safeguard measures (e.g., temporary tariffs or quotas).

**Prominent Intervention Types:**
- Anti-dumping duties
- Countervailing duties (to offset subsidies)
- Safeguard duties or quantitative restrictions to manage import surges

**Corresponding GTA Intervention Type(s):**
- Anti-dumping
- Anti-circumvention
- Anti-subsidy
- Safeguard
- Special safeguard

---

#### **Chapter E: Non-automatic Import Licensing, Quotas, Prohibitions, and Other Quantity Control Measures**

For researchers studying direct quantitative restrictions on trade, this chapter is the primary reference. It covers policies that limit the volume or value of imported goods, such as import quotas, import prohibitions (bans), and licensing requirements that are not automatically granted. It also includes tariff-rate quotas (TRQs), where a certain quantity of imports is allowed at a lower tariff.

**Prominent Intervention Types:**
- Quotas (global, country-specific, seasonal)
- Full prohibitions (import bans)
- Non-automatic import licensing procedures
- Tariff-rate quotas (TRQs)

**Corresponding GTA Intervention Type(s):**
- Import licensing requirement
- Import quota
- Import ban
- Import tariff quota
- (Export-restraint arrangements are out of GTA scope)

---

#### **Chapter F: Price-control Measures, Including Additional Taxes and Charges**

This chapter is for researchers examining policies that directly control or influence the price of imported goods, apart from standard tariffs. It includes measures like minimum import prices, customs surcharges, and various additional taxes and fees (e.g., statistical taxes, consular fees). It also covers internal taxes, such as excise and consumption taxes, that are levied on imported products.

**Prominent Intervention Types:**
- Minimum import prices
- Customs surcharges and additional duties
- Variable levies on agricultural products
- Internal taxes and charges levied on imports (e.g., excise taxes, consumption taxes)

**Corresponding GTA Intervention Type(s):**
- Minimum import price
- Import price benchmark
- Voluntary export-price restraints
- Other import charges
- Internal taxation of imports
- Import tariff

---

#### **Chapter G: Finance Measures**

A researcher interested in how financial regulations can act as trade barriers should consult this chapter. It details measures that regulate access to and the cost of foreign exchange for imports. This includes requirements for advance import deposits, multiple exchange rates for different products, and restrictions on payment terms.

**Prominent Intervention Types:**
- Advance import deposits
- Cash margin requirements before opening a letter of credit
- Multiple exchange rate systems
- Regulations concerning terms of payment for imports

**Corresponding GTA Intervention Type(s):**
- Trade payment measure
- (Multiple exchange rates and regulations on official foreign exchange allocation are out of GTA scope)

---

#### **Chapter H: Measures Affecting Competition**

This chapter is relevant for research on policies that grant exclusive or special privileges to a limited number of companies, thereby restricting competition from imported goods. Key examples include the mandated use of state-trading enterprises for importing certain goods or requiring that imports be transported or insured by national companies.

**Prominent Intervention Types:**
- State-trading enterprises or other sole importing agencies
- Compulsory use of national transport services
- Compulsory use of national insurance services

**Corresponding GTA Intervention Type(s):**
- Selective import channel restriction
- Local operations requirement

---

#### **Chapter I: Trade-related Investment Measures (TRIMs)**

A researcher studying the intersection of investment policy and trade should refer to this chapter. It covers policies that link foreign investment to trade performance, potentially distorting international trade. The main examples are local content requirements (obliging firms to use a certain amount of domestic inputs) and trade-balancing requirements (restricting a firm's imports based on its export volumes).

**Prominent Intervention Types:**
- Local content measures (requiring use of domestic inputs)
- Trade-balancing measures (linking import rights to export performance)

**Corresponding GTA Intervention Type(s):**
- Local content requirement
- Local content incentive
- Local labour requirement
- Local labour incentive
- Local operations requirement
- Local operations incentive
- Local value added requirement
- Local value added incentive
- Localisation, nes
- Trade balancing measure

---

#### **Chapter J: Distribution Restrictions**

For "behind-the-border" barriers that affect goods after they have entered a country, this chapter is key. A researcher will find policies restricting the internal sale and distribution of imported products. This includes limiting sales to certain geographic areas or prohibiting foreign companies from establishing their own distribution networks.

**Prominent Intervention Types:**
- Measures restricting access to domestic distributors
- Measures prohibiting the establishment of own distribution channels
- Restrictions on the sale of goods to certain areas or persons

**Corresponding GTA Intervention Type(s):**
- Distribution restrictions

---

#### **Chapter K: Restrictions on Post-Sales Services**

This chapter is for researchers looking at barriers related to services provided after a product is sold, such as maintenance and repair. It includes measures that restrict foreign firms from providing after-sales services or require them to use local service channels.

**Prominent Intervention Types:**
- Measures prohibiting access to domestic post-sale service channels
- Measures restricting the establishment of own post-sale service channels

**Corresponding GTA Intervention Type(s):**
- Post-sales service restriction

---

#### **Chapter L: Subsidies and Other Forms of Support**

A researcher investigating government support to domestic industries should consult this comprehensive chapter. It classifies various forms of government subsidies that can affect trade, including direct grants, loans, tax exemptions, and the provision of goods and services below market price. The classification covers support given to both producing enterprises and final consumers.

**Prominent Intervention Types:**
- Grants (monetary transfers)
- Tax and duty exemptions or reductions
- Credit support (e.g., loans at below-market rates)
- Price support and other price-related direct payments

**Corresponding GTA Intervention Type(s):**
- Financial grant
- State loan
- Capital injection or equity participation
- Production subsidy
- Price stabilisation
- Loan guarantee
- Tax or social insurance relief
- In-kind grant
- Localisation, nes
- Interest payment subsidy
- Import incentive
- State aid, unspecified
- State aid, nes
- (Price regulation and certain transfers to consumers are out of GTA scope)

---

#### **Chapter M: Government Procurement Restrictions**

This chapter is essential for research on discrimination against foreign suppliers in public purchasing. It details measures that restrict foreign companies from participating in government tenders, such as outright bans, domestic price preferences, and requirements for local content or subcontracting.

**Prominent Intervention Types:**
- Market access restrictions (e.g., reserving procurement for national suppliers)
- Domestic price preferences
- Offsets, including local content requirements on inputs or staff
- Qualification criteria that favor domestic firms (e.g., prior domestic experience)

**Corresponding GTA Intervention Type(s):**
- Public procurement access
- Public procurement preference margin
- Public procurement localisation
- Public procurement, nes
- (Qualification criteria, evaluation, and review mechanisms are out of GTA scope)

---

#### **Chapter N: Intellectual Property (IP)**

For research on how intellectual property rights affect trade, this chapter provides the framework. It covers the rules for obtaining and maintaining IP rights (patents, trademarks, copyrights), the principles of exhaustion (which determine the legality of parallel imports), and the enforcement mechanisms against infringement.

**Prominent Intervention Types:**
- Procedures for patent, trademark, and copyright acquisition and maintenance
- Rules on exhaustion (national, regional, international)
- Enforcement procedures (border measures, civil/criminal remedies)

**Corresponding GTA Intervention Type(s):**
- Intellectual property protection

---

#### **Chapter O: Rules of Origin**

This chapter is crucial for researchers studying preferential trade agreements or trade policy enforcement. It explains the criteria used to determine the "nationality" of a product. These rules are necessary to establish whether a product qualifies for lower tariffs under a trade agreement and are also used in applying trade remedies.

**Prominent Intervention Types:**
- Origin criteria (wholly obtained, substantial transformation)
- Methods for substantial transformation (change in tariff classification, ad valorem percentage)
- Proofs of origin (e.g., certificate of origin)

**Corresponding GTA Intervention Type(s):**
- Out of GTA scope

---

#### **Chapter P: Export-related Measures**

Finally, for researchers looking at policies a country applies to its *own exports*, this chapter provides a comprehensive classification. This includes export taxes, export quotas or prohibitions, export licensing, and export subsidies or other support measures. It is the counterpart to the many import-focused chapters.

**Prominent Intervention Types:**
- Export prohibition
- Export quotas
- Licensing or permit requirements to export
- Export taxes and duties

**Corresponding GTA Intervention Type(s):**
- Sanitary and phytosanitary measure
- Export-related non-tariff measure, nes
- Export ban
- Export quota
- Export licensing requirement
- Export tariff quota
- Foreign customer limit
- Export tax
- Tax-based export incentive
- Export subsidy
- Trade finance
- Financial assistance in foreign market
- Other export incentive
- Local supply requirements for exports
- (Measures on re-export are out of GTA scope)

---

## MAST vs GTA Intervention Types

**Key Principle:**
The GTA API handles the correspondence between MAST chapters and specific GTA intervention types. When you provide `mast_chapters` parameter, the API automatically includes all relevant intervention types that fall under those chapters.

**In Practice:**
- For **broad queries**: Use `mast_chapters` (e.g., "all subsidies" → Chapter L)
- For **specific queries**: Use `intervention_types` (e.g., "state aid" → specific type)
- **Don't combine** both parameters unless you want the intersection (more restrictive)

## Usage Examples

### Example 1: All Government Support (Broad)
```python
mast_chapters=['L']
implementing_jurisdictions=['USA', 'CHN']
```
Returns all forms of subsidies and government support from US and China (includes state aid, grants, loans, tax relief, etc.).

### Example 2: Specific Subsidy Type (Narrow)
```python
intervention_types=['State aid']
implementing_jurisdictions=['DEU']
```
Returns only state aid measures from Germany.

### Example 3: All Import Restrictions (Broad)
```python
mast_chapters=['E', 'F']
affected_jurisdictions=['USA']
```
Returns all quotas, licensing, prohibitions, and price controls affecting US.

### Example 4: Trade Defense Measures (Broad)
```python
mast_chapters=['D']
date_announced_gte='2020-01-01'
```
Returns all anti-dumping, countervailing duties, and safeguards since 2020.

### Example 5: Technical Measures on Agricultural Products (Broad)
```python
mast_chapters=['A', 'B', 'C']
affected_products=[100630]  # Rice HS code
```
Returns all SPS, TBT, and pre-shipment measures affecting rice (note: many may be outside GTA scope).

### Example 6: Investment Measures (Broad)
```python
mast_chapters=['I']
implementing_jurisdictions=['CHN', 'IND']
```
Returns all local content requirements, trade balancing measures, and localization requirements from China and India.

### Example 7: Export Controls (Broad)
```python
mast_chapters=['P']
implementing_jurisdictions=['USA']
affected_jurisdictions=['CHN']
```
Returns all US export restrictions, bans, quotas, and licensing requirements affecting China.

## Related Resources

- **GTA Intervention Types**: See `gta_intervention_type_list.md` for specific intervention type names
- **GTA Handbook**: See `GTA handbook.md` for general GTA database information
- **Search Guide**: See `search_guide.md` for comprehensive search strategies
