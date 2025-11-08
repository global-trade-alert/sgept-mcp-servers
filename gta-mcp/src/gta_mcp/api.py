"""GTA API client for making authenticated requests."""

import json
from typing import Dict, Any, Optional, List
import httpx

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


def build_filters(params: Dict[str, Any]) -> Dict[str, Any]:
    """Build API filter dictionary from input parameters.

    Converts user-friendly parameters to GTA API format:
    - ISO codes to UN country codes
    - Date ranges to announcement_period/implementation_period arrays
    - Field name mappings

    Args:
        params: Input parameters from Pydantic model

    Returns:
        Dictionary of filters for API request_data
    """
    filters = {}

    # Convert implementing jurisdictions (ISO -> UN codes)
    if params.get('implementing_jurisdictions'):
        filters['implementer'] = convert_iso_to_un_codes(params['implementing_jurisdictions'])

    # Convert affected jurisdictions (ISO -> UN codes)
    if params.get('affected_jurisdictions'):
        filters['affected'] = convert_iso_to_un_codes(params['affected_jurisdictions'])

    # Affected products (HS codes - pass through)
    if params.get('affected_products'):
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

    # Date modified (for ticker)
    if params.get('date_modified_gte'):
        # This is used by ticker endpoint, not main data endpoint
        pass

    return filters
