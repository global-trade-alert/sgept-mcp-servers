# GTA Data Model

## Hierarchy

State Act (announcement) → Intervention(s) (specific measures)

One government action (state act) can contain multiple interventions when:
- Multiple policy instruments are used (e.g., tariff + quota)
- Parts have different evaluations (e.g., one Red, one Green)
- Different eligible firm categories apply

## Counting Units

- `count_variable: "intervention_id"` — counts individual measures (default, most granular)
- `count_variable: "state_act_id"` — counts government actions (fewer, as one act may contain multiple interventions)

## Product/Sector Relationship

Each intervention can affect:
- Multiple HS codes (6-digit product codes, goods only)
- Multiple CPC sectors (3-digit, goods AND services)

⚠️ Counting by sector/product produces intervention-sector/product COMBINATIONS,
   not unique interventions. The same intervention appears in multiple sector counts.
