# GTA Data Model

## Hierarchy

**State Act (announcement) → Intervention(s) (specific measures)**

One government action (state act) can contain multiple interventions when:
- Multiple policy instruments are used (e.g., tariff + quota)
- Parts have different evaluations (e.g., one Red, one Green)
- Different eligible firm categories apply

### Concrete Example

**State Act:** "US Executive Order imposing tariffs on Chinese technology products (January 2025)"

This single state act contains 3 separate interventions:
- **Intervention A:** 25% tariff on semiconductor imports (Red, HS 8542)
- **Intervention B:** 10% tariff on electronic components (Red, HS 8534)
- **Intervention C:** Tariff exemption for components used in medical devices (Green, HS 9018)

When counting by `state_act_id`, this appears as 1 action. When counting by `intervention_id`, it appears as 3 measures.

## Key Fields

**Identifiers:**
- `intervention_id` — unique measure identifier (most granular)
- `state_act_id` — parent announcement identifier (one-to-many with interventions)

**Descriptions:**
- `title` — short description of the measure
- `description` — full text explanation (typically 2-4 paragraphs)

**Jurisdictions:**
- `implementing_jurisdictions` — countries/blocs enacting the measure
- `affected_jurisdictions` — countries/blocs harmed by the measure

**Product/Sector Coverage:**
- `affected_products` — HS codes (6-digit, goods only)
- `affected_sectors` — CPC codes (3-digit, goods and services)

**Policy Classification:**
- `intervention_type` — instrument used (e.g., tariff, subsidy, quota)
- `gta_evaluation` — harm assessment (Red=harmful, Amber=likely harmful, Green=liberalising)

**Temporal Data:**
- `date_announced` — when measure was publicly announced
- `date_implemented` — when measure came into force
- `date_removed` — when measure was lifted (if applicable)
- `is_in_force` — boolean indicating current status

**Evidence:**
- `sources` — official documentation links (government gazettes, press releases, legal texts)

## Counting Units

- `count_variable: "intervention_id"` — counts individual measures (default, most granular)
- `count_variable: "state_act_id"` — counts government actions (fewer, as one act may contain multiple interventions)

## Overcounting Warning

**Problem:** Counting by sector or product produces intervention-sector/product COMBINATIONS, not unique interventions. The same intervention appears multiple times.

**Worked Example:**

India announces 1 intervention blocking steel imports to protect domestic producers. This intervention affects 50 different HS codes (various types of steel products).

- Counting by `count_variable: "affected_products"` → this intervention appears **50 times** (once per HS code)
- Counting by `count_variable: "intervention_id"` → this intervention appears **once**

**Best Practice:** Always report which counting unit you used when presenting statistics. If you count by sector or product, explicitly state that results show "intervention-sector combinations" rather than "unique interventions."

## Product/Sector Relationship

Each intervention can affect:
- Multiple HS codes (6-digit product codes, goods only)
- Multiple CPC sectors (3-digit, goods AND services)

HS codes are more granular than CPC sectors. A single CPC sector may contain dozens of HS codes. An intervention can affect products in multiple sectors simultaneously.

## Date Flow

**Typical lifecycle:** Announcement → Implementation → (possible) Removal

- **Announcement date:** when the government publicly declares the measure (press release, official statement)
- **Implementation date:** when the measure legally enters into force (may be weeks or months after announcement)
- **Removal date:** when the measure is officially lifted (many measures have no removal date and remain in force)

**Important notes:**
- Gap between announcement and implementation can be months (allows firms to adjust)
- Many interventions only have announcement dates (implementation date not yet known or not recorded)
- Year-only dates default conservatively (e.g., "2024" defaults to 2024-12-31 for implemented date)
- Use `date_announced_gte` for monitoring new policy developments
- Use `date_implemented_gte` for analysing measures currently in effect

## Product Hierarchy Notes

- HS codes are 6-digit: 854210 = "Cards incorporating an electronic integrated circuit (smart cards)"
- CPC sectors are 3-digit: 452 = "Electronic and optical equipment"
- The same intervention affecting smart cards would appear in both classifications
- When counting by products vs sectors, you're using different levels of aggregation
