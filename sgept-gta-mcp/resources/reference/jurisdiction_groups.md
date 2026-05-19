# Jurisdiction Groups Reference

When a user asks about measures by "G20 countries" or "EU members," use the ISO codes below with `implementing_jurisdictions` or `affected_jurisdictions`.

---

## G7

| Country | ISO | UN Code |
|---------|-----|---------|
| Canada | CAN | 124 |
| France | FRA | 251 |
| Germany | DEU | 276 |
| Italy | ITA | 381 |
| Japan | JPN | 392 |
| United Kingdom | GBR | 826 |
| United States | USA | 840 |

**ISO list:** `['CAN', 'FRA', 'DEU', 'ITA', 'JPN', 'GBR', 'USA']`

---

## G20

Includes all G7 members plus:

| Country | ISO | UN Code |
|---------|-----|---------|
| Argentina | ARG | 32 |
| Australia | AUS | 36 |
| Brazil | BRA | 76 |
| China | CHN | 156 |
| India | IND | 699 |
| Indonesia | IDN | 360 |
| Mexico | MEX | 484 |
| Russia | RUS | 643 |
| Saudi Arabia | SAU | 682 |
| South Africa | ZAF | 710 |
| South Korea | KOR | 410 |
| Turkey | TUR | 792 |
| European Union | EUN | 1049 |

**ISO list:** `['ARG', 'AUS', 'BRA', 'CAN', 'CHN', 'FRA', 'DEU', 'IND', 'IDN', 'ITA', 'JPN', 'MEX', 'RUS', 'SAU', 'ZAF', 'KOR', 'TUR', 'GBR', 'USA', 'EUN']`

**Note:** India uses UN code 699 in GTA (not 356). The EU (EUN/1049) participates as a bloc.

---

## EU-27

| Country | ISO | UN Code |
|---------|-----|---------|
| Austria | AUT | 40 |
| Belgium | BEL | 56 |
| Bulgaria | BGR | 100 |
| Croatia | HRV | 191 |
| Cyprus | CYP | 196 |
| Czech Republic | CZE | 203 |
| Denmark | DNK | 208 |
| Estonia | EST | 233 |
| Finland | FIN | 246 |
| France | FRA | 251 |
| Germany | DEU | 276 |
| Greece | GRC | 300 |
| Hungary | HUN | 348 |
| Ireland | IRL | 372 |
| Italy | ITA | 381 |
| Latvia | LVA | 428 |
| Lithuania | LTU | 440 |
| Luxembourg | LUX | 442 |
| Malta | MLT | 470 |
| Netherlands | NLD | 528 |
| Poland | POL | 616 |
| Portugal | PRT | 620 |
| Romania | ROU | 642 |
| Slovakia | SVK | 703 |
| Slovenia | SVN | 705 |
| Spain | ESP | 724 |
| Sweden | SWE | 752 |

**ISO list:** `['AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE']`

**Tip:** For EU-level policies, use `implementing_jurisdictions=['EUN']` (EU as a bloc). For member state policies, use the full EU-27 list above.

---

## BRICS (expanded, as of 2024)

| Country | ISO | UN Code |
|---------|-----|---------|
| Brazil | BRA | 76 |
| Russia | RUS | 643 |
| India | IND | 699 |
| China | CHN | 156 |
| South Africa | ZAF | 710 |
| Egypt | EGY | 818 |
| Ethiopia | ETH | 231 |
| Iran | IRN | 364 |
| Saudi Arabia | SAU | 682 |
| United Arab Emirates | ARE | 784 |

**ISO list (original 5):** `['BRA', 'RUS', 'IND', 'CHN', 'ZAF']`
**ISO list (expanded):** `['BRA', 'RUS', 'IND', 'CHN', 'ZAF', 'EGY', 'ETH', 'IRN', 'SAU', 'ARE']`

---

## ASEAN

| Country | ISO | UN Code |
|---------|-----|---------|
| Brunei | BRN | 96 |
| Cambodia | KHM | 116 |
| Indonesia | IDN | 360 |
| Laos | LAO | 418 |
| Malaysia | MYS | 458 |
| Myanmar | MMR | 104 |
| Philippines | PHL | 608 |
| Singapore | SGP | 702 |
| Thailand | THA | 764 |
| Vietnam | VNM | 704 |

**ISO list:** `['BRN', 'KHM', 'IDN', 'LAO', 'MYS', 'MMR', 'PHL', 'SGP', 'THA', 'VNM']`

---

## CPTPP (Comprehensive and Progressive Agreement for Trans-Pacific Partnership)

| Country | ISO | UN Code |
|---------|-----|---------|
| Australia | AUS | 36 |
| Brunei | BRN | 96 |
| Canada | CAN | 124 |
| Chile | CHL | 152 |
| Japan | JPN | 392 |
| Malaysia | MYS | 458 |
| Mexico | MEX | 484 |
| New Zealand | NZL | 554 |
| Peru | PER | 604 |
| Singapore | SGP | 702 |
| Vietnam | VNM | 704 |
| United Kingdom | GBR | 826 |

**ISO list:** `['AUS', 'BRN', 'CAN', 'CHL', 'JPN', 'MYS', 'MEX', 'NZL', 'PER', 'SGP', 'VNM', 'GBR']`

---

## RCEP (Regional Comprehensive Economic Partnership)

| Country | ISO | UN Code |
|---------|-----|---------|
| Australia | AUS | 36 |
| Brunei | BRN | 96 |
| Cambodia | KHM | 116 |
| China | CHN | 156 |
| Indonesia | IDN | 360 |
| Japan | JPN | 392 |
| South Korea | KOR | 410 |
| Laos | LAO | 418 |
| Malaysia | MYS | 458 |
| Myanmar | MMR | 104 |
| New Zealand | NZL | 554 |
| Philippines | PHL | 608 |
| Singapore | SGP | 702 |
| Thailand | THA | 764 |
| Vietnam | VNM | 704 |

**ISO list:** `['AUS', 'BRN', 'KHM', 'CHN', 'IDN', 'JPN', 'KOR', 'LAO', 'MYS', 'MMR', 'NZL', 'PHL', 'SGP', 'THA', 'VNM']`

---

## Usage Examples

**G20 subsidies to EVs:**
```
implementing_jurisdictions=['ARG','AUS','BRA','CAN','CHN','FRA','DEU','IND','IDN','ITA','JPN','MEX','RUS','SAU','ZAF','KOR','TUR','GBR','USA','EUN']
mast_chapters=['L']
query='electric vehicle'
```

**EU measures affecting US exports:**
```
implementing_jurisdictions=['EUN']
affected_jurisdictions=['USA']
gta_evaluation=['Harmful']
```

**ASEAN investment restrictions:**
```
implementing_jurisdictions=['BRN','KHM','IDN','LAO','MYS','MMR','PHL','SGP','THA','VNM']
mast_chapters=['I']
```
