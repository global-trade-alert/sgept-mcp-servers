"""GTA API client for making authenticated requests."""

import json
from typing import Dict, Any, Optional, List, Tuple
import httpx
from rapidfuzz import fuzz

# MAST chapter letter to API ID mapping
# Based on API schema MastChaptersEnum
MAST_CHAPTER_TO_ID = {
	"A": 1,   # Sanitary and phytosanitary measure
	"B": 2,   # Technical barriers to trade
	"C": 17,  # Pre-shipment inspection and other formalities
	"D": 4,   # Contingent trade-protective measures
	"E": 5,   # Non-automatic licensing, quotas etc.
	"F": 6,   # Price-control measures, including additional taxes and charges
	"G": 8,   # Finance measures
	"H": 18,  # Measures affecting competition
	"I": 9,   # Trade-related investment measures
	"J": 19,  # Distribution restrictions
	"K": 20,  # Restrictions on post-sales services
	"L": 10,  # Subsidies (excl. export subsidies)
	"M": 11,  # Government procurement restrictions
	"N": 13,  # Intellectual Property
	"P": 14,  # Export-related measures (incl. subsidies)
}

# Additional non-letter MAST categories from API
MAST_SPECIAL_CATEGORIES = {
	"Capital control measures": 3,
	"FDI measures": 7,
	"Migration measures": 12,
	"Tariff measures": 15,
	"Instrument unclear": 16,
}

# ISO to UN country code mapping
# Intervention type name to ID mapping
# Based on gta_intervention_type_list.md
INTERVENTION_TYPE_TO_ID = {
    "Capital injection and equity stakes (including bailouts)": 1,
    "State loan": 2,
    "Financial grant": 3,
    "In-kind grant": 4,
    "Production subsidy": 5,
    "Interest payment subsidy": 6,
    "Loan guarantee": 7,
    "Tax or social insurance relief": 8,
    "Competitive devaluation": 9,
    "Repatriation & surrender requirements": 10,
    "Controls on commercial transactions and investment instruments": 11,
    "Controls on credit operations": 12,
    "Control on personal transactions": 13,
    "Consumption subsidy": 14,
    "Tax-based export incentive": 15,
    "Export subsidy": 16,
    "Other export incentive": 17,
    "Export tax": 18,
    "Export ban": 19,
    "Export tariff quota": 20,
    "Export quota": 21,
    "Import ban": 22,
    "Import incentive": 23,
    "Intellectual property protection": 24,
    "FDI: Entry and ownership rule": 25,
    "FDI: Treatment and operations, nes": 26,
    "FDI: Financial incentive": 27,
    "Local content requirement": 28,
    "Local operations requirement": 29,
    "Local labour requirement": 30,
    "Labour market access": 31,
    "Post-migration treatment": 32,
    "Trade payment measure": 33,
    "Trade balancing measure": 34,
    "Export licensing requirement": 35,
    "Import licensing requirement": 36,
    "Export-related non-tariff measure, nes": 37,
    "Import-related non-tariff measure, nes": 38,
    "Foreign customer limit": 39,
    "Public procurement preference margin": 40,
    "Public procurement localisation": 41,
    "Public procurement access": 42,
    "Public procurement, nes": 43,
    "Import tariff quota": 44,
    "Import quota": 45,
    "Sanitary and phytosanitary measure": 46,
    "Import tariff": 47,
    "Internal taxation of imports": 48,
    "Technical barrier to trade": 49,
    "Import monitoring": 50,
    "Anti-dumping": 51,
    "Safeguard": 52,
    "Anti-subsidy": 53,
    "Trade finance": 54,
    "Financial assistance in foreign market": 55,
    "Anti-circumvention": 56,
    "Local content incentive": 57,
    "Special safeguard": 58,
    "State aid, nes": 59,
    "Instrument unclear": 60,
    "Price stabilisation": 61,
    "State aid, unspecified": 62,
    "Local supply requirement for exports": 63,
    "Local value added requirement": 64,
    "Local value added incentive": 65,
    "Local operations incentive": 66,
    "Local labour incentive": 67,
    "Localisation, nes": 68,
    "Voluntary export-restraint arrangements": 69,
    "Voluntary export-price restraints": 70,
    "Minimum import price": 71,
    "Import price benchmark": 72,
    "Other import charges": 73,
    "Export price benchmark": 74,
    "Port restriction": 75,
    "Selective import channel restriction": 76,
    "Distribution restriction": 77,
    "Post-sales service restriction (MAST Chapter K1)": 78,
    "Corporate control order": 79,
}

ISO_TO_UN_CODE = {
    "AFG": 4, "ALB": 8, "DZA": 12, "ASM": 16, "AND": 20, "AGO": 24,
    "ATG": 28, "AZE": 31, "ARG": 32, "AUS": 36, "AUT": 40, "BHS": 44,
    "BHR": 48, "BGD": 50, "ARM": 51, "BRB": 52, "BEL": 56, "BMU": 60,
    "BTN": 64, "BOL": 68, "BIH": 70, "BWA": 72, "BRA": 76, "BLZ": 84,
    "SLB": 90, "VGB": 92, "BRN": 96, "BGR": 100, "MMR": 104, "BDI": 108,
    "BLR": 112, "KHM": 116, "CMR": 120, "CAN": 124, "CPV": 132, "CYM": 136,
    "CAF": 140, "LKA": 144, "TCD": 148, "CHL": 152, "CHN": 156, "TWN": 158,
    "COL": 170, "COM": 174, "MYT": 175, "COG": 178, "COD": 180, "COK": 184,
    "CRI": 188, "HRV": 191, "CUB": 192, "CYP": 196, "CZE": 203, "BEN": 204,
    "DNK": 208, "DMA": 212, "DOM": 214, "ECU": 218, "SLV": 222, "GNQ": 226,
    "ETH": 231, "ERI": 232, "EST": 233, "FRO": 234, "FLK": 238, "FJI": 242,
    "FIN": 246, "FRA": 251, "GUF": 254, "PYF": 258, "DJI": 262, "GAB": 266,
    "GEO": 268, "GMB": 270, "PSE": 275, "DEU": 276, "GHA": 288, "KIR": 296,
    "GRC": 300, "GRL": 304, "GRD": 308, "GLP": 312, "GUM": 316, "GTM": 320,
    "GIN": 324, "GUY": 328, "HTI": 332, "VAT": 336, "HND": 340, "HKG": 344,
    "HUN": 348, "ISL": 352, "IND": 699, "IDN": 360, "IRN": 364, "IRQ": 368,
    "IRL": 372, "ISR": 376, "ITA": 381, "CIV": 384, "JAM": 388, "JPN": 392,
    "KAZ": 398, "JOR": 400, "KEN": 404, "PRK": 408, "KOR": 410, "KWT": 414,
    "KGZ": 417, "LAO": 418, "LBN": 422, "LSO": 426, "LVA": 428, "LBR": 430,
    "LBY": 434, "LIE": 438, "LTU": 440, "LUX": 442, "MAC": 446, "MDG": 450,
    "MWI": 454, "MYS": 458, "MDV": 462, "MLI": 466, "MLT": 470, "MTQ": 474,
    "MRT": 478, "MUS": 480, "MEX": 484, "MCO": 492, "MNG": 496, "MDA": 498,
    "MNE": 499, "MSR": 500, "MAR": 504, "MOZ": 508, "OMN": 512, "NAM": 516,
    "NRU": 520, "NPL": 524, "NLD": 528, "ANT": 532, "ABW": 533, "NCL": 540,
    "VUT": 548, "NZL": 554, "NIC": 558, "NER": 562, "NGA": 566, "NIU": 570,
    "NFK": 574, "NOR": 578, "MNP": 580, "FSM": 583, "MHL": 584, "PLW": 585,
    "PAK": 586, "PAN": 591, "PNG": 598, "PRY": 600, "PER": 604, "PHL": 608,
    "PCN": 612, "POL": 616, "PRT": 620, "GNB": 624, "TLS": 626, "PRI": 630,
    "QAT": 634, "REU": 638, "ROU": 642, "RUS": 643, "RWA": 646, "BLM": 652,
    "SHN": 654, "KNA": 659, "AIA": 660, "LCA": 662, "MAF": 663, "SPM": 666,
    "VCT": 670, "SMR": 674, "STP": 678, "SAU": 682, "SEN": 686, "SRB": 688,
    "SYC": 690, "SLE": 694, "SGP": 702, "SVK": 703, "VNM": 704, "SVN": 705,
    "SOM": 706, "ZAF": 710, "ZWE": 716, "ESP": 724, "SSD": 728, "SDN": 729,
    "ESH": 732, "SUR": 740, "SJM": 744, "SWZ": 748, "SWE": 752, "CHE": 756,
    "SYR": 760, "TJK": 762, "THA": 764, "TGO": 768, "TKL": 772, "TON": 776,
    "TTO": 780, "ARE": 784, "TUN": 788, "TUR": 792, "TKM": 795, "TCA": 796,
    "TUV": 798, "UGA": 800, "UKR": 804, "MKD": 807, "EGY": 818, "GBR": 826,
    "TZA": 834, "USA": 840, "VIR": 850, "BFA": 854, "URY": 858, "UZB": 860,
    "VEN": 862, "WLF": 876, "WSM": 882, "YEM": 887, "ZMB": 894, "XKX": 999,
    # Additional common codes
    "EU": 1000  # European Union (custom)
}

# CPC Sector name to ID mapping
# Based on api_sector_list_202511090751.md
# Note: Sectors with ID >= 500 are services, < 500 are goods
SECTOR_NAME_TO_ID = {
	"Cereals": 11, "Vegetables": 12, "Fruits and nuts": 13,
	"Oilseeds and oleaginous fruits": 14,
	"Edible roots and tubers with high starch or inulin content": 15,
	"Stimulant, spice and aromatic crops": 16,
	"Pulses (dried leguminous vegetables)": 17, "Sugar crops": 18,
	"Forage products, fibre crops, plants used in perfumery, pharmacy, or for insecticidal, fungicidal or similar purposes, beet, forage plant and flower seeds, natural rubber, living plants, cut flowers and flower buds, unmanufactured tobacco, other raw veget": 19,
	"Live animals": 21, "Raw milk": 22,
	"Eggs of hens or other birds in shell, fresh": 23,
	"Reproductive materials of animals": 24, "Other animal products": 29,
	"Wood in the rough": 31, "Non-wood forest products": 32,
	"Fish, live, not for human consumption": 41,
	"Fish live, fresh or chilled for human consumption": 42,
	"Crustaceans, live, fresh or chilled": 43,
	"Molluscs live, fresh or chilled": 44,
	"Other aquatic invertebrates, live, fresh or chilled": 45,
	"Other aquatic plants and animals": 49,
	"Coal and peat": 110, "Crude petroleum and natural gas": 120,
	"Uranium and thorium ores and concentrates": 130,
	"Iron ores and concentrates, other than roasted iron pyrites": 141,
	"Non-ferrous metal ores and concentrates (other than uranium or thorium ores and concentrates)": 142,
	"Monumental or building stone": 151,
	"Gypsum; anhydrite; limestone flux; limestone and other calcareous stone, of a kind used for the manufacture of lime or cement": 152,
	"Sands, pebbles, gravel, broken or crushed stone, natural bitumen and asphalt": 153,
	"Clays": 154, "Chemical and fertilizer minerals": 161,
	"Salt and pure sodium chloride; sea water": 162,
	"Precious and semi-precious stones; pumice stone; emery; natural abrasives; other minerals": 163,
	"Electrical energy": 171,
	"Coal gas, water gas, producer gas and similar gases, other than petroleum gases and other gaseous hydrocarbons": 172,
	"Steam and hot water": 173, "Ice and snow": 174, "Natural water": 180,
	"Meat and meat products": 211,
	"Prepared and preserved fish, crustaceans, molluscs and other aquatic invertebrates": 212,
	"Prepared and preserved vegetables, pulses and potatoes": 213,
	"Prepared and preserved fruits and nuts": 214, "Animal fats": 215,
	"Vegetable oils": 216, "Margarine and similar preparations": 217,
	"Cotton linters": 218,
	"Oil-cake and other residues resulting from the extraction of vegetable fats or oils; flours and meals of oil seeds or oleaginous fruits, except those of mustard; vegetable waxes, except triglycerides; degras; residues resulting from the treatment of fatty": 219,
	"Processed liquid milk, cream and whey": 221, "Other dairy products": 222,
	"Eggs, in shell, preserved or cooked": 223, "Grain mill products": 231,
	"Starches and starch products; sugars and sugar syrups n.e.c.": 232,
	"Preparations used in animal feeding; lucerne (alfalfa) meal and pellets": 233,
	"Bakery products": 234, "Sugar and molasses": 235,
	"Cocoa, chocolate and sugar confectionery": 236,
	"Macaroni, noodles, couscous and similar farinaceous products": 237,
	"Food products n.e.c.": 239,
	"Ethyl alcohol; spirits, liqueurs and other spirituous beverages": 241,
	"Wines": 242, "Malt liquors and malt": 243,
	"Soft drinks; bottled mineral waters": 244, "Tobacco products": 250,
	"Natural textile fibres prepared for spinning": 261,
	"Man-made textile staple fibres processed for spinning": 262,
	"Textile yarn and thread of natural fibres": 263,
	"Textile yarn and thread of man-made filaments or staple fibres": 264,
	"Woven fabrics (except special fabrics) of natural fibres other than cotton": 265,
	"Woven fabrics (except special fabrics) of cotton": 266,
	"Woven fabrics (except special fabrics) of man-made filaments and staple fibres": 267,
	"Special fabrics": 268, "Made-up textile articles": 271,
	"Carpets and other textile floor coverings": 272,
	"Twine, cordage, ropes and cables and articles thereof (including netting)": 273,
	"Textiles n.e.c.": 279, "Knitted or crocheted fabrics": 281,
	"Wearing apparel, except fur apparel": 282,
	"Tanned or dressed furskins and artificial fur; articles thereof (except headgear)": 283,
	"Tanned or dressed leather; composition leather": 291,
	"Luggage, handbags and the like; saddlery and harness; other articles of leather": 292,
	"Footwear, with outer soles and uppers of rubber or plastics, or with uppers of leather or textile materials, other than sports footwear, footwear incorporating a protective metal toe- cap and miscellaneous special footwear": 293,
	"Sports footwear, except skating boots": 294,
	"Other footwear, except asbestos footwear, orthopaedic footwear and skating boots": 295,
	"Parts of footwear; removable insoles, heel cushions and similar articles; gaiters, leggings and similar articles, and parts thereof": 296,
	"Wood, sawn or chipped lengthwise, sliced or peeled, of a thickness exceeding 6 mm; railway or tramway sleepers (cross-ties) of wood, not impregnated": 311,
	"Wood continuously shaped along any of its edges or faces; wood wool; wood flour; wood in chips or particles": 312,
	"Wood in the rough, treated with paint, stains, creosote or other preservatives; railway or tramway sleepers (cross-ties) of wood, impregnated; hoopwood, split poles, wooden sticks and the like": 313,
	"Boards and panels": 314, "Veneer sheets; sheets for plywood; densified wood": 315,
	"Builders' joinery and carpentry of wood (including cellular wood panels, assembled parquet panels, shingles and shakes)": 316,
	"Packing cases, boxes, crates, drums and similar packings, of wood; cable-drums of wood; pallets, box pallets and other load boards, of wood; casks, barrels, vats, tubs and other coopers' products and parts thereof, of wood (including staves)": 317,
	"Other products of wood; articles of cork, plaiting materials and straw": 319,
	"Pulp, paper and paperboard": 321, "Books, in print": 322,
	"Newspapers and periodicals, daily, in print": 323,
	"Newspapers and periodicals, other than daily, in print": 324,
	"Printed maps; music, printed or in manuscript; postcards, greeting cards, pictures and plans": 325,
	"Stamps, cheque forms, banknotes, stock certificates, brochures and leaflets, advertising material and other printed matter": 326,
	"Registers, account books, notebooks, letter pads, diaries and similar articles, blotting-pads, binders, file covers, forms and other articles of stationery, of paper or paperboard": 327,
	"Composed type, prepared printing plates or cylinders, impressed lithographic stones or other impressed media for use in printing": 328,
	"Coke and semi-coke of coal, of lignite or of peat; retort carbon": 331,
	"Tar distilled from coal, from lignite or from peat, and other mineral tars": 332,
	"Petroleum oils and oils obtained from bituminous materials, other than crude; preparations n.e.c. containing by weight 70% or more of these oils, such oils being the basic constituents of the preparations": 333,
	"Petroleum gases and other gaseous hydrocarbons, except natural gas": 334,
	"Petroleum jelly; paraffin wax, micro- crystalline petroleum wax, slack wax, ozokerite, lignite wax, peat wax, other mineral waxes, and similar products; petroleum coke, petroleum bitumen and other residues of petroleum oils or of oils obtained from bitumi": 335,
	"Radioactive elements and isotopes and compounds; alloys, dispersions, ceramic products and mixtures containing these elements, isotopes or compounds; radioactive residues": 336,
	"Fuel elements (cartridges), for or of nuclear reactors": 337,
	"Basic organic chemicals": 341, "Basic inorganic chemicals n.e.c.": 342,
	"Tanning or dyeing extracts; tannins and their derivatives; colouring matter n.e.c.": 343,
	"Activated natural mineral products; animal black; tall oil; terpenic oils produced by the treatment of coniferous woods; crude dipentene; crude para-cymene; pine oil; rosin and resin acids, and derivatives thereof; rosin spirit and rosin oils; rum gums; w": 344,
	"Miscellaneous basic chemical products": 345,
	"Fertilizers and pesticides": 346, "Plastics in primary forms": 347,
	"Synthetic rubber and factice derived from oils, and mixtures thereof with natural rubber and similar natural gums, in primary forms or in plates, sheets or strip": 348,
	"Paints and varnishes and related products; artists' colours; ink": 351,
	"Pharmaceutical products": 352,
	"Soap, cleaning preparations, perfumes and toilet preparations": 353,
	"Chemical products n.e.c.": 354, "Man-made fibres": 355,
	"Rubber tyres and tubes": 361, "Other rubber products": 362,
	"Semi-manufactures of plastics": 363, "Packaging products of plastics": 364,
	"Other plastics products": 369, "Glass and glass products": 371,
	"Non-structural ceramic ware": 372,
	"Refractory products and structural non-refractory clay products": 373,
	"Plaster, lime and cement": 374,
	"Articles of concrete, cement and plaster": 375,
	"Monumental or building stone and articles thereof": 376,
	"Other non-metallic mineral products n.e.c.": 379, "Furniture": 381,
	"Jewellery and related articles": 382, "Musical instruments": 383,
	"Sports goods": 384, "Games and toys": 385,
	"Roundabouts, swings, shooting galleries and other fairground amusements": 386,
	"Prefabricated buildings": 387,
	"Other manufactured articles n.e.c.": 389,
	"Wastes from food and tobacco industry": 391, "Non-metal wastes or scraps": 392,
	"Metal wastes or scraps": 393, "Other wastes and scraps": 399,
	"Basic iron and steel": 411, "Products of iron or steel": 412,
	"Basic precious metals and metals clad with precious metals": 413,
	"Copper, nickel, aluminium, alumina, lead, zinc and tin, unwrought": 414,
	"Semi-finished products of copper, nickel, aluminium, lead, zinc and tin or their alloys": 415,
	"Other non-ferrous metals and articles thereof (including waste and scrap of some metals); cermets and articles thereof": 416,
	"Structural metal products and parts thereof": 421,
	"Tanks, reservoirs and containers of iron, steel or aluminium": 422,
	"Steam generators, (except central heating boilers) and parts thereof": 423,
	"Other fabricated metal products": 429, "Engines and turbines and parts thereof": 431,
	"Pumps, compressors, hydraulic and pneumatic power engines, and valves, and parts thereof": 432,
	"Bearings, gears, gearing and driving elements, and parts thereof": 433,
	"Ovens and furnace burners and parts thereof": 434,
	"Lifting and handling equipment and parts thereof": 435,
	"Other general-purpose machinery and parts thereof": 439,
	"Agricultural or forestry machinery and parts thereof": 441,
	"Machine-tools and parts and accessories thereof": 442,
	"Machinery for metallurgy and parts thereof": 443,
	"Machinery for mining, quarrying and construction, and parts thereof": 444,
	"Machinery for food, beverage and tobacco processing, and parts thereof": 445,
	"Machinery for textile, apparel and leather production, and parts thereof": 446,
	"Weapons and ammunition and parts thereof": 447,
	"Domestic appliances and parts thereof": 448,
	"Other special-purpose machinery and parts thereof": 449,
	"Office and accounting machinery, and parts and accessories thereof": 451,
	"Computing machinery and parts and accessories thereof": 452,
	"Electric motors, generators and transformers, and parts thereof": 461,
	"Electricity distribution and control apparatus, and parts thereof": 462,
	"Insulated wire and cable; optical fibre cables": 463,
	"Accumulators, primary cells and primary batteries, and parts thereof": 464,
	"Electric filament or discharge lamps; arc lamps; lighting equipment; parts thereof": 465,
	"Other electrical equipment and parts thereof": 469,
	"Electronic valves and tubes; electronic components; parts thereof": 471,
	"Television and radio transmitters; television, video and digital cameras; telephone sets": 472,
	"Radio broadcast and television receivers; apparatus for sound and video recording and reproducing; microphones, loudspeakers, amplifiers, etc.": 473,
	"Parts for the goods of classes 4721 to 4733 and 4822": 474,
	"Disks, tapes, solid-state non-volatile storage devices and other media, not recorded": 475,
	"Audio, video and other disks, tapes and other physical media, recorded": 476,
	"Packaged software": 478,
	"Cards with magnetic strips or chip": 479,
	"Medical and surgical equipment and orthopaedic appliances": 481,
	"Instruments and appliances for measuring, checking, testing, navigating and other purposes, except optical instruments; industrial process control equipment; parts and accessories thereof": 482,
	"Optical instruments and photographic equipment, and parts and accessories thereof": 483,
	"Watches and clocks, and parts thereof": 484,
	"Motor vehicles, trailers and semi-trailers; parts and accessories thereof": 491,
	"Bodies (coachwork) for motor vehicles; trailers and semi-trailers; parts and accessories thereof": 492,
	"Ships": 493, "Pleasure and sporting boats": 494,
	"Railway and tramway locomotives and rolling stock, and parts thereof": 495,
	"Aircraft and spacecraft, and parts thereof": 496,
	"Other transport equipment and parts thereof": 499, "Buildings": 531,
	"Civil engineering works": 532,
	"General construction services of buildings": 541,
	"General construction services of civil engineering works": 542,
	"Site preparation services": 543,
	"Assembly and erection of prefabricated constructions": 544,
	"Special trade construction services": 545, "Installation services": 546,
	"Building completion and finishing services": 547,
	"Wholesale trade services, except on a fee or contract basis": 611,
	"Wholesale trade services on a fee or contract basis": 612,
	"Non-specialized store retail trade services": 621,
	"Specialized store retail trade services": 622,
	"Mail order or Internet retail trade services": 623,
	"Other non-store retail trade services": 624,
	"Retail trade services on a fee or contract basis": 625,
	"Accommodation services for visitors": 631,
	"Other accommodation services for visitors and others": 632,
	"Food serving services": 633, "Beverage serving services": 634,
	"Local transport and sightseeing transportation services of passengers": 641,
	"Long-distance transport services of passengers": 642,
	"Land transport services of freight": 651,
	"Water transport services of freight": 652,
	"Air and space transport services of freight": 653,
	"Rental services of transport vehicles with operators": 660,
	"Cargo handling services": 671, "Storage and warehousing services": 672,
	"Supporting services for railway transport": 673,
	"Supporting services for road transport": 674,
	"Supporting services for water transport": 675,
	"Supporting services for air or space transport": 676,
	"Other supporting transport services": 679,
	"Postal and courier services": 680,
	"Electricity and gas distribution (on own account)": 691,
	"Water distribution (on own account)": 692,
	"Financial services, except investment banking, insurance services and pension services": 711,
	"Investment banking services": 712,
	"Insurance and pension services (excluding reinsurance services), except compulsory social security services": 713,
	"Reinsurance services": 714,
	"Services auxiliary to financial services other than to insurance and pensions": 715,
	"Services auxiliary to insurance and pensions": 716,
	"Services of holding financial assets": 717,
	"Real estate services involving own or leased property": 721,
	"Real estate services on a fee or contract basis": 722,
	"Leasing or rental services concerning machinery and equipment without operator": 731,
	"Leasing or rental services concerning other goods": 732,
	"Licensing services for the right to use intellectual property and similar products": 733,
	"Research and experimental development services in natural sciences and engineering": 811,
	"Research and experimental development services in social sciences and humanities": 812,
	"Interdisciplinary research and experimental development services": 813,
	"Research and development originals": 814, "Legal services": 821,
	"Accounting, auditing and bookkeeping services": 822,
	"Tax consultancy and preparation services": 823,
	"Insolvency and receivership services": 824,
	"Management consulting and management services; information technology services": 831,
	"Architectural services, urban and land planning and landscape architectural services": 832,
	"Engineering services": 833, "Scientific and other technical services": 834,
	"Veterinary services": 835,
	"Advertising services and provision of advertising space or time": 836,
	"Market research and public opinion polling services": 837,
	"Photography services and photographic processing services": 838,
	"Other professional, technical and business services": 839,
	"Telephony and other telecommunications services": 841,
	"Internet telecommunications services": 842, "On-line content": 843,
	"News agency services": 844, "Library and archive services": 845,
	"Broadcasting, programming and programme distribution services": 846,
	"Employment services": 851, "Investigation and security services": 852,
	"Cleaning services": 853, "Packaging services": 854,
	"Travel arrangement, tour operator and related services": 855,
	"Other support services": 859,
	"Support and operation services to agriculture, hunting, forestry and fishing": 861,
	"Support and operation services to mining": 862,
	"Support and operation services to electricity, gas and water distribution": 863,
	"Maintenance and repair services of fabricated metal products, machinery and equipment": 871,
	"Repair services of other goods": 872,
	"Installation services (other than construction)": 873,
	"Food, beverage and tobacco manufacturing services": 881,
	"Textile, wearing apparel and leather manufacturing services": 882,
	"Wood and paper manufacturing services": 883,
	"Petroleum, chemical and pharmaceutical product manufacturing services": 884,
	"Rubber, plastic and other non-metallic mineral product manufacturing services": 885,
	"Basic metal manufacturing services": 886,
	"Fabricated metal product, machinery and equipment manufacturing services": 887,
	"Transport equipment manufacturing services": 888,
	"Other manufacturing services": 889,
	"Publishing, printing and reproduction services": 891,
	"Moulding, pressing, stamping, extruding and similar plastic manufacturing services": 892,
	"Casting, forging, stamping and similar metal manufacturing services": 893,
	"Materials recovery (recycling) services, on a fee or contract basis": 894,
	"Administrative services of the government": 911,
	"Public administrative services provided to the community as a whole": 912,
	"Administrative services related to compulsory social security schemes": 913,
	"Pre-primary education services": 921, "Primary education services": 922,
	"Secondary education services": 923,
	"Post-secondary non-tertiary education services": 924,
	"Tertiary education services": 925,
	"Other education and training services and educational support services": 929,
	"Human health services": 931,
	"Residential care services for the elderly and disabled": 932,
	"Other social services with accommodation": 933,
	"Social services without accommodation for the elderly and disabled": 934,
	"Other social services without accommodation": 935,
	"Sewerage, sewage treatment and septic tank cleaning services": 941,
	"Waste collection services": 942,
	"Waste treatment and disposal services": 943, "Remediation services": 944,
	"Sanitation and similar services": 945,
	"Other environmental protection services n.e.c.": 949,
	"Services furnished by business, employers and professional organizations": 951,
	"Services furnished by trade unions": 952,
	"Services furnished by other membership organizations": 959,
	"Audiovisual and related services": 961,
	"Performing arts and other live entertainment event presentation and promotion services": 962,
	"Services of performing and other artists": 963,
	"Museum and preservation services": 964,
	"Sports and recreational sports services": 965,
	"Services of athletes and related support services": 966,
	"Other amusement and recreational services": 969,
	"Washing, cleaning and dyeing services": 971,
	"Beauty and physical well-being services": 972,
	"Funeral, cremation and undertaking services": 973,
	"Other miscellaneous services": 979, "Domestic services": 980,
	"Services provided by extraterritorial organizations and bodies": 990,
	"ALL": 1000, "NONE": 1001,
}

# Reverse mapping for formatting
SECTOR_ID_TO_NAME = {v: k for k, v in SECTOR_NAME_TO_ID.items()}

# Hierarchical sector level2 groupings
SECTOR_LEVEL2_GROUPS = {
	1: list(range(11, 20)),  # Crops
	2: [21, 22, 23, 24, 29],  # Livestock products
	3: [31, 32],  # Forestry products
	4: [41, 42, 43, 44, 45, 49],  # Aquatic products
	11: [110],  # Coal and peat
	12: [120],  # Crude petroleum and natural gas
	13: [130],  # Uranium and thorium
	14: [141, 142],  # Metal ores
	15: [151, 152, 153, 154],  # Stone and minerals
	16: [161, 162, 163],  # Chemical minerals
	17: [171, 172, 173, 174],  # Energy products
	18: [180],  # Natural water
	21: [211, 212, 213, 214, 215, 216, 217, 218, 219],  # Processed foods
	22: [221, 222, 223],  # Dairy and eggs
	23: [231, 232, 233, 234, 235, 236, 237, 239],  # Food products
	24: [241, 242, 243, 244],  # Beverages
	25: [250],  # Tobacco
	26: [261, 262, 263, 264, 265, 266, 267, 268],  # Textiles
	27: [271, 272, 273, 279],  # Textile articles
	28: [281, 282, 283],  # Apparel
	29: [291, 292, 293, 294, 295, 296],  # Leather and footwear
	31: [311, 312, 313, 314, 315, 316, 317, 319],  # Wood products
	32: [321, 322, 323, 324, 325, 326, 327, 328],  # Paper products
	33: [331, 332, 333, 334, 335, 336, 337],  # Petroleum products
	34: [341, 342, 343, 344, 345, 346, 347, 348],  # Chemicals
	35: [351, 352, 353, 354, 355],  # Chemical products
	36: [361, 362, 363, 364, 369],  # Rubber and plastics
	37: [371, 372, 373, 374, 375, 376, 379],  # Non-metallic minerals
	38: [381, 382, 383, 384, 385, 386, 387, 389],  # Miscellaneous manufacturing
	39: [391, 392, 393, 399],  # Wastes
	41: [411, 412, 413, 414, 415, 416],  # Metals
	42: [421, 422, 423, 429],  # Metal products
	43: [431, 432, 433, 434, 435, 439],  # General machinery
	44: [441, 442, 443, 444, 445, 446, 447, 448, 449],  # Special machinery
	45: [451, 452],  # Computing equipment
	46: [461, 462, 463, 464, 465, 469],  # Electrical equipment
	47: [471, 472, 473, 474, 475, 476, 478, 479],  # Electronics
	48: [481, 482, 483, 484],  # Precision instruments
	49: [491, 492, 493, 494, 495, 496, 499],  # Transport equipment
	53: [531, 532],  # Construction
	54: [541, 542, 543, 544, 545, 546, 547],  # Construction services
	61: [611, 612],  # Wholesale trade
	62: [621, 622, 623, 624, 625],  # Retail trade
	63: [631, 632, 633, 634],  # Accommodation and food
	64: [641, 642],  # Passenger transport
	65: [651, 652, 653],  # Freight transport
	66: [660],  # Rental with operator
	67: [671, 672, 673, 674, 675, 676, 679],  # Transport support
	68: [680],  # Postal
	69: [691, 692],  # Distribution services
	71: [711, 712, 713, 714, 715, 716, 717],  # Financial services
	72: [721, 722],  # Real estate
	73: [731, 732, 733],  # Rental and licensing
	81: [811, 812, 813, 814],  # R&D
	82: [821, 822, 823, 824],  # Legal and accounting
	83: [831, 832, 833, 834, 835, 836, 837, 838, 839],  # Professional services
	84: [841, 842, 843, 844, 845, 846],  # Telecommunications
	85: [851, 852, 853, 854, 855, 859],  # Support services
	86: [861, 862, 863],  # Operational support
	87: [871, 872, 873],  # Maintenance and repair
	88: [881, 882, 883, 884, 885, 886, 887, 888, 889],  # Manufacturing services
	89: [891, 892, 893, 894],  # Other manufacturing
	91: [911, 912, 913],  # Public administration
	92: [921, 922, 923, 924, 925, 929],  # Education
	93: [931, 932, 933, 934, 935],  # Health and social
	94: [941, 942, 943, 944, 945, 949],  # Environmental
	95: [951, 952, 959],  # Membership organizations
	96: [961, 962, 963, 964, 965, 966, 969],  # Entertainment
	97: [971, 972, 973, 979],  # Personal services
	98: [980],  # Domestic services
	99: [990],  # Extraterritorial
	100: [1000],  # ALL
	101: [1001],  # NONE
}


class GTAAPIClient:
    """Client for interacting with the GTA API."""
    
    BASE_URL = "https://api.globaltradealert.org"
    
    def __init__(self, api_key: str):
        """Initialize the GTA API client.
        
        Args:
            api_key: The GTA API key for authentication
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"APIKey {api_key}",
            "Content-Type": "application/json"
        }
    
    async def search_interventions(
        self,
        filters: Dict[str, Any],
        limit: int = 50,
        offset: int = 0,
        sorting: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for interventions using GTA Data V2 endpoint.

        Args:
            filters: Dictionary of filter parameters
            limit: Maximum number of results to return
            offset: Number of results to skip
            sorting: Sort order string, e.g., "-date_announced" for newest first,
                    "date_announced" for oldest first. If None, uses API default.
                    Valid fields: date_announced, date_published, date_implemented,
                    date_removed, intervention_id. Prefix with '-' for descending.

        Returns:
            List of intervention data

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        endpoint = f"{self.BASE_URL}/api/v2/gta/data/"

        # Build request body with request_data wrapper
        body = {
            "limit": limit,
            "offset": offset,
            "request_data": filters
        }

        # Add sorting if specified
        if sorting:
            body["sorting"] = sorting

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint,
                json=body,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_intervention(self, intervention_id: int) -> Dict[str, Any]:
        """Get a specific intervention by ID.

        Args:
            intervention_id: The intervention ID to fetch

        Returns:
            Intervention data dictionary

        Raises:
            httpx.HTTPStatusError: If API request fails
            ValueError: If intervention not found
        """
        endpoint = f"{self.BASE_URL}/api/v2/gta/data/"

        body = {
            "limit": 1,
            "offset": 0,
            "request_data": {
                "intervention_id": [intervention_id],
                "announcement_period": ["1900-01-01", "2099-12-31"]
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint,
                json=body,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()

            if not data or len(data) == 0:
                raise ValueError(f"Intervention {intervention_id} not found")

            return data[0]
    
    async def get_ticker_updates(
        self,
        filters: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get ticker updates for interventions.

        Args:
            filters: Dictionary of filter parameters
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            API response with ticker data

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        endpoint = f"{self.BASE_URL}/api/v1/gta/ticker/"

        body = {
            "limit": limit,
            "offset": offset,
            "request_data": filters
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint,
                json=body,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_impact_chains(
        self,
        granularity: str,
        filters: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get impact chains at product or sector granularity.

        Args:
            granularity: Either 'product' or 'sector'
            filters: Dictionary of filter parameters
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            API response with impact chain data

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        endpoint = f"{self.BASE_URL}/api/v1/gta/impact-chains/{granularity}/"

        body = {
            "limit": limit,
            "offset": offset,
            "request_data": filters
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint,
                json=body,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()


def convert_intervention_types(type_names: List[Any]) -> List[int]:
    """Convert intervention type names to IDs.

    Supports:
    - Integer IDs (passed through)
    - Exact name matches
    - Case-insensitive partial matches

    Args:
        type_names: List of intervention type names or IDs

    Returns:
        List of intervention type IDs (integers)

    Raises:
        ValueError: If a type name cannot be matched
    """
    type_ids = []

    for type_input in type_names:
        # If already an integer, pass through
        if isinstance(type_input, int):
            type_ids.append(type_input)
            continue

        # Try exact match first
        if type_input in INTERVENTION_TYPE_TO_ID:
            type_ids.append(INTERVENTION_TYPE_TO_ID[type_input])
            continue

        # Try case-insensitive match
        type_lower = type_input.lower()
        found = False
        for name, type_id in INTERVENTION_TYPE_TO_ID.items():
            if name.lower() == type_lower:
                type_ids.append(type_id)
                found = True
                break

        if found:
            continue

        # Try partial match (contains)
        matches = []
        for name, type_id in INTERVENTION_TYPE_TO_ID.items():
            if type_lower in name.lower() or name.lower() in type_lower:
                matches.append((name, type_id))

        if len(matches) == 1:
            type_ids.append(matches[0][1])
        elif len(matches) > 1:
            match_names = [m[0] for m in matches[:5]]
            raise ValueError(
                f"Ambiguous intervention type '{type_input}'. Multiple matches found: "
                f"{', '.join(match_names)}. Please be more specific."
            )
        else:
            raise ValueError(
                f"Unknown intervention type: '{type_input}'. "
                f"Use gta://reference/intervention-types-list resource to see available types."
            )

    return type_ids


def convert_iso_to_un_codes(iso_codes: List[str]) -> List[int]:
    """Convert ISO country codes to UN country codes.

    Args:
        iso_codes: List of ISO 3-letter country codes

    Returns:
        List of UN country codes (integers)

    Raises:
        ValueError: If an ISO code is not found in mapping
    """
    un_codes = []
    for iso in iso_codes:
        iso_upper = iso.upper()
        if iso_upper not in ISO_TO_UN_CODE:
            raise ValueError(
                f"Unknown ISO country code: {iso}. "
                f"Please use standard ISO 3-letter codes (e.g., USA, CHN, DEU)."
            )
        un_codes.append(ISO_TO_UN_CODE[iso_upper])
    return un_codes


def convert_mast_chapters(mast_input: List[str]) -> List[int]:
    """Convert MAST chapter identifiers to API integer IDs.

    Accepts either:
    - Single letters A-P (converted to IDs)
    - Integer IDs 1-20 (passed through)
    - Special category names (e.g., "Capital control measures")

    Args:
        mast_input: List of MAST chapters (letters, IDs, or names)

    Returns:
        List of MAST chapter IDs (integers 1-20)

    Raises:
        ValueError: If a MAST chapter identifier is not recognized
    """
    mast_ids = []
    for item in mast_input:
        # Handle string input
        if isinstance(item, str):
            item_upper = item.upper().strip()

            # Try letter mapping (A-P)
            if item_upper in MAST_CHAPTER_TO_ID:
                mast_ids.append(MAST_CHAPTER_TO_ID[item_upper])
            # Try special category names
            elif item in MAST_SPECIAL_CATEGORIES:
                mast_ids.append(MAST_SPECIAL_CATEGORIES[item])
            # Try parsing as integer
            else:
                try:
                    mast_id = int(item)
                    if 1 <= mast_id <= 20:
                        mast_ids.append(mast_id)
                    else:
                        raise ValueError(f"MAST chapter ID must be between 1-20, got {mast_id}")
                except ValueError:
                    raise ValueError(
                        f"Unknown MAST chapter: '{item}'. "
                        f"Use letters A-P, IDs 1-20, or special categories like 'Capital control measures'."
                    )
        # Handle integer input
        elif isinstance(item, int):
            if 1 <= item <= 20:
                mast_ids.append(item)
            else:
                raise ValueError(f"MAST chapter ID must be between 1-20, got {item}")
        else:
            raise ValueError(f"Invalid MAST chapter type: {type(item)}")

    return mast_ids


# Service keyword detection for CPC sector auto-selection
SERVICE_KEYWORDS = {
	"financial", "finance", "banking", "insurance", "pension", "investment",
	"reinsurance", "loan", "credit", "mortgage",
	"real estate", "property", "leasing", "rental", "licensing",
	"legal", "accounting", "audit", "tax", "consultancy", "consulting",
	"management", "advisory", "professional", "technical",
	"architectural", "engineering", "scientific", "veterinary",
	"advertising", "market research", "photography",
	"telecommunications", "telecom", "internet", "broadcasting",
	"employment", "security", "cleaning", "packaging", "travel",
	"transport services", "freight services", "passenger transport",
	"cargo", "warehousing", "postal", "courier",
	"wholesale trade", "retail trade", "distribution",
	"accommodation", "hotel", "restaurant", "food serving", "beverage serving",
	"education", "teaching", "training", "school", "university",
	"health", "medical", "hospital", "care services", "social services",
	"environmental", "waste", "sewerage", "sanitation", "remediation",
	"entertainment", "cultural", "sports", "recreation", "museum",
	"repair", "maintenance", "installation",
	"construction services", "building services",
	"government", "administration", "public services"
}

# Broad category keywords that suggest using CPC sectors over HS codes
BROAD_CATEGORY_KEYWORDS = {
	"agricultural", "agriculture", "farming", "crops",
	"livestock", "animal products", "dairy",
	"forestry", "wood products", "timber",
	"fishing", "aquatic", "seafood",
	"mining", "minerals", "ores", "coal", "petroleum",
	"energy", "electricity", "gas",
	"textiles", "fabric", "apparel", "clothing", "footwear",
	"chemicals", "pharmaceuticals", "plastics", "rubber",
	"metals", "steel", "iron", "aluminium", "copper",
	"machinery", "equipment", "appliances",
	"electronics", "electrical", "computing",
	"vehicles", "automotive", "transport equipment", "aircraft", "ships",
	"food products", "beverages", "tobacco"
}


def analyze_query_intent(query: Optional[str], affected_products: Optional[List], affected_sectors: Optional[List]) -> Dict[str, Any]:
	"""Analyze user intent to determine whether to use HS codes or CPC sectors.

	Args:
		query: Optional text query string
		affected_products: List of HS codes if provided
		affected_sectors: List of CPC sectors if provided

	Returns:
		Dictionary with recommendation and analysis:
		- recommendation: 'use_cpc_sectors', 'use_hs_codes', 'use_both', or 'unclear'
		- detected_services: Boolean indicating if service keywords found
		- detected_broad_category: Boolean indicating if broad category keywords found
		- suggestions: List of suggested CPC sector IDs if applicable
		- message: Human-readable explanation
	"""
	result = {
		"recommendation": "unclear",
		"detected_services": False,
		"detected_broad_category": False,
		"suggestions": [],
		"message": ""
	}

	# If both explicitly provided, use both
	if affected_products and affected_sectors:
		result["recommendation"] = "use_both"
		result["message"] = "Using both HS codes and CPC sectors as specified."
		return result

	# If HS codes explicitly provided and no sectors, use HS codes
	if affected_products and not affected_sectors:
		result["recommendation"] = "use_hs_codes"
		result["message"] = "Using HS codes as specified."
		return result

	# If sectors explicitly provided, use sectors
	if affected_sectors and not affected_products:
		result["recommendation"] = "use_cpc_sectors"
		result["message"] = "Using CPC sectors as specified."
		return result

	# Analyze query text if provided
	if query:
		query_lower = query.lower()

		# Check for service keywords
		for keyword in SERVICE_KEYWORDS:
			if keyword in query_lower:
				result["detected_services"] = True
				result["recommendation"] = "use_cpc_sectors"
				result["message"] = f"Detected service-related query (keyword: '{keyword}'). Services are classified using CPC sectors (ID >= 500), not HS codes."
				return result

		# Check for broad category keywords
		for keyword in BROAD_CATEGORY_KEYWORDS:
			if keyword in query_lower:
				result["detected_broad_category"] = True
				result["recommendation"] = "use_cpc_sectors"
				result["message"] = f"Detected broad category query (keyword: '{keyword}'). CPC sectors provide broader product range coverage than specific HS codes."
				return result

	# If no clear intent detected, leave it unclear
	result["message"] = "No specific product classification detected. Provide HS codes for specific goods or CPC sectors for broader categories/services."
	return result


def convert_sectors(sector_inputs: List[Any]) -> Tuple[List[int], List[str]]:
	"""Convert sector names/IDs to CPC sector IDs with fuzzy matching.

	Supports:
	- Integer IDs (passed through if valid)
	- Exact sector name matches
	- Fuzzy matches with similarity threshold of 80%
	- Returns all matching sectors for ambiguous terms

	Args:
		sector_inputs: List of sector names or IDs (can be mixed)

	Returns:
		Tuple of (sector_ids, messages) where:
		- sector_ids: List of CPC sector IDs (integers)
		- messages: List of informational messages about matches

	Raises:
		ValueError: If a sector cannot be matched or is invalid
	"""
	sector_ids = []
	messages = []

	for sector_input in sector_inputs:
		# If already an integer, validate and pass through
		if isinstance(sector_input, int):
			if sector_input in SECTOR_ID_TO_NAME:
				sector_ids.append(sector_input)
			else:
				raise ValueError(
					f"Unknown sector ID: {sector_input}. "
					f"Use gta://reference/sectors-list resource to see available sectors."
				)
			continue

		# Handle string input
		sector_str = str(sector_input).strip()

		# Try exact match first (case-insensitive)
		exact_match = None
		for name, sid in SECTOR_NAME_TO_ID.items():
			if name.lower() == sector_str.lower():
				exact_match = (name, sid)
				break

		if exact_match:
			sector_ids.append(exact_match[1])
			if exact_match[0] != sector_str:
				messages.append(f"Matched '{sector_str}' to sector: {exact_match[0]} (ID: {exact_match[1]})")
			continue

		# Try parsing as integer string
		try:
			sector_id = int(sector_str)
			if sector_id in SECTOR_ID_TO_NAME:
				sector_ids.append(sector_id)
				continue
			else:
				raise ValueError(f"Unknown sector ID: {sector_id}")
		except ValueError:
			pass  # Not an integer, continue with fuzzy matching

		# Fuzzy matching with RapidFuzz
		matches = []
		threshold = 80

		for name, sid in SECTOR_NAME_TO_ID.items():
			similarity = fuzz.ratio(sector_str.lower(), name.lower())
			if similarity >= threshold:
				matches.append((similarity, name, sid))

		# Sort by similarity score (highest first)
		matches.sort(reverse=True, key=lambda x: x[0])

		if len(matches) == 0:
			raise ValueError(
				f"No matching sector found for '{sector_str}'. "
				f"Use gta://reference/sectors-list resource to see available sectors, "
				f"or try broader search terms."
			)
		elif len(matches) == 1:
			sector_ids.append(matches[0][2])
			if matches[0][1].lower() != sector_str.lower():
				messages.append(f"Fuzzy matched '{sector_str}' to: {matches[0][1]} (ID: {matches[0][2]}, similarity: {matches[0][0]}%)")
		else:
			# Return all matches for ambiguous terms
			matched_ids = [m[2] for m in matches]
			sector_ids.extend(matched_ids)
			match_list = [f"{m[1]} (ID: {m[2]})" for m in matches[:5]]  # Show top 5
			messages.append(
				f"Multiple sectors matched '{sector_str}'. Including all {len(matches)} matches. "
				f"Top matches: {', '.join(match_list)}"
			)

	# Remove duplicates while preserving order
	seen = set()
	unique_sector_ids = []
	for sid in sector_ids:
		if sid not in seen:
			seen.add(sid)
			unique_sector_ids.append(sid)

	return unique_sector_ids, messages


def build_filters(params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Build API filter dictionary from input parameters.

    Converts user-friendly parameters to GTA API format:
    - ISO codes to UN country codes
    - Date ranges to announcement_period/implementation_period arrays
    - CPC sector names to sector IDs (with fuzzy matching)
    - Field name mappings
    - Intelligent product/sector selection based on query intent

    Args:
        params: Input parameters from Pydantic model

    Returns:
        Tuple of (filters dict for API request_data, list of informational messages)
    """
    filters = {}
    messages = []

    # Convert implementing jurisdictions (ISO -> UN codes)
    if params.get('implementing_jurisdictions'):
        filters['implementer'] = convert_iso_to_un_codes(params['implementing_jurisdictions'])

    # Convert affected jurisdictions (ISO -> UN codes)
    if params.get('affected_jurisdictions'):
        filters['affected'] = convert_iso_to_un_codes(params['affected_jurisdictions'])

    # Analyze query intent for intelligent product/sector selection
    intent_analysis = analyze_query_intent(
        query=params.get('query'),
        affected_products=params.get('affected_products'),
        affected_sectors=params.get('affected_sectors')
    )

    # Add intent analysis message if relevant
    if intent_analysis['message'] and (intent_analysis['detected_services'] or intent_analysis['detected_broad_category']):
        messages.append(f"Query Analysis: {intent_analysis['message']}")

    # Handle affected sectors (CPC classification) - convert names to IDs
    if params.get('affected_sectors'):
        sector_ids, sector_messages = convert_sectors(params['affected_sectors'])
        filters['affected_sectors'] = sector_ids
        messages.extend(sector_messages)

        # Inform if sectors include services
        service_sectors = [sid for sid in sector_ids if sid >= 500]
        if service_sectors:
            messages.append(f"Note: {len(service_sectors)} service sector(s) included (CPC sectors with ID >= 500).")

    # Handle affected products (HS codes)
    # Only include if not overridden by service detection
    if params.get('affected_products'):
        if intent_analysis['recommendation'] == 'use_cpc_sectors' and intent_analysis['detected_services']:
            messages.append(
                "Warning: HS codes cannot be used for services. "
                "Services must be queried using CPC sectors (ID >= 500). "
                "HS codes have been ignored for this service-related query."
            )
        else:
            filters['affected_products'] = params['affected_products']

    # Intervention types - convert names to IDs
    if params.get('intervention_types'):
        filters['intervention_types'] = convert_intervention_types(params['intervention_types'])

    # GTA evaluation - pass through
    if params.get('gta_evaluation'):
        filters['gta_evaluation'] = params['gta_evaluation']

    # Handle announcement period dates
    date_announced_gte = params.get('date_announced_gte')
    date_announced_lte = params.get('date_announced_lte')
    if date_announced_gte or date_announced_lte:
        filters['announcement_period'] = [
            date_announced_gte or "1900-01-01",
            date_announced_lte or "2099-12-31"
        ]
    else:
        # Always provide announcement_period to avoid API error
        filters['announcement_period'] = ["1900-01-01", "2099-12-31"]

    # Handle implementation period dates
    date_implemented_gte = params.get('date_implemented_gte')
    date_implemented_lte = params.get('date_implemented_lte')
    if date_implemented_gte or date_implemented_lte:
        filters['implementation_period'] = [
            date_implemented_gte or "1900-01-01",
            date_implemented_lte or "2099-12-31"
        ]

    # Is in force - convert to in_force_on_date
    if params.get('is_in_force') is not None:
        from datetime import date
        filters['in_force_on_date'] = date.today().isoformat()
        filters['keep_in_force_on_date'] = params['is_in_force']

    # Query parameter - text search (pass through as-is)
    if params.get('query'):
        filters['query'] = params['query']

    # MAST chapters - convert letters to IDs
    if params.get('mast_chapters'):
        filters['mast_chapters'] = convert_mast_chapters(params['mast_chapters'])

    # Date modified (for ticker)
    if params.get('date_modified_gte'):
        # This is used by ticker endpoint, not main data endpoint
        pass

    return filters, messages
