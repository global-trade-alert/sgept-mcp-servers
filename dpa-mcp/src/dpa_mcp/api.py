"""DPA API client for making authenticated requests."""

import json
from typing import Dict, Any, Optional, List
import httpx

# ISO to DPA jurisdiction ID mapping (based on dpa_jurisdictions.md)
ISO_TO_DPA_ID = {
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
	"VEN": 862, "WLF": 876, "WSM": 882, "YEM": 887, "ZMB": 894, "XXK": 999
}

# Economic activity name to ID mapping (based on dpa_economic_activity_list.md)
ECONOMIC_ACTIVITY_TO_ID = {
	"cross-cutting": 1,
	"infrastructure provider: internet and telecom services": 2,
	"online advertising provider": 4,
	"digital payment provider (incl. cryptocurrencies)": 5,
	"platform intermediary: user-generated content": 6,
	"streaming service provider": 7,
	"platform intermediary: e-commerce": 8,
	"ML and AI development": 9,
	"other service provider": 10,
	"unspecified": 11,
	"technological consumer goods": 12,
	"semiconductors": 13,
	"software provider: app stores": 14,
	"DLT development": 15,
	"search service provider": 16,
	"software provider: other software": 17,
	"messaging service provider": 18,
	"platform intermediary: other": 19,
	"infrastructure provider: cloud computing, storage and databases": 20,
	"infrastructure provider: network hardware and equipment": 21,
	"infrastructure provider: other": 22
}

# Policy area name to ID mapping (based on dpa_policy_area_list.md)
POLICY_AREA_TO_ID = {
	"International trade": 1,
	"Competition": 2,
	"Content moderation": 3,
	"Data governance": 4,
	"Subsidies and industrial policy": 5,
	"Instrument unspecified": 6,
	"Other operating conditions": 8,
	"Other operating condition": 8,  # Alias
	"Public procurement": 9,
	"Authorisation, registration and licensing": 10,
	"Taxation": 11,
	"Foreign direct investment": 12,
	"Labour law": 13,
	"Intellectual property": 14,
	"Consumer protection": 15,
	"Design and testing standards": 16,
	"Regulatory Compliance and Transparency": 17
}

# Event type name to ID mapping (based on dpa_event_type_list.md)
EVENT_TYPE_TO_ID = {
	"order": 1,
	"outline": 2,
	"inquiry": 3,
	"decision": 4,
	"law": 5,
	"treaty": 6,
	"public lawsuit": 8,
	"investigation": 9,
	"declaration": 10,
	"civil lawsuit": 11
}

# Government branch mapping
GOVERNMENT_BRANCH_TO_ID = {
	"legislature": 1,
	"executive": 2,
	"judiciary": 3
}

# DPA implementation level mapping
DPA_IMPLEMENTATION_LEVEL_TO_ID = {
	"national": 1,
	"supranational": 2,
	"subnational": 3,
	"bi- or plurilateral agreement": 4,
	"multilateral agreement": 5,
	"other": 6
}


class DPAAPIClient:
	"""Client for interacting with the DPA API."""

	BASE_URL = "https://api.globaltradealert.org"

	def __init__(self, api_key: str):
		"""Initialize the DPA API client.

		Args:
			api_key: The DPA API key for authentication
		"""
		self.api_key = api_key
		self.headers = {
			"Authorization": f"APIKey {api_key}",
			"Content-Type": "application/json"
		}

	async def search_events(
		self,
		filters: Dict[str, Any],
		limit: int = 50,
		offset: int = 0,
		sorting: Optional[str] = None
	) -> List[Dict[str, Any]]:
		"""Search for digital policy events using DPA Events endpoint.

		Args:
			filters: Dictionary of filter parameters
			limit: Maximum number of results to return
			offset: Number of results to skip
			sorting: Sort order string (e.g., "-id" for newest first)

		Returns:
			List of event data

		Raises:
			httpx.HTTPStatusError: If API request fails
		"""
		endpoint = f"{self.BASE_URL}/api/v1/dpa/events/"

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
			data = response.json()

			# DPA API returns paginated response
			if isinstance(data, dict) and "results" in data:
				return data["results"]
			elif isinstance(data, list):
				return data
			else:
				return []

	async def get_event(self, event_id: int) -> Dict[str, Any]:
		"""Get a specific event by ID.

		Args:
			event_id: The event ID to fetch

		Returns:
			Event data dictionary

		Raises:
			httpx.HTTPStatusError: If API request fails
			ValueError: If event not found
		"""
		endpoint = f"{self.BASE_URL}/api/v1/dpa/events/"

		# Search for specific event ID
		body = {
			"limit": 1,
			"offset": 0,
			"request_data": {
				"event_period": ["2000-01-01", "2099-12-31"]
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

			# Extract results
			results = data.get("results", []) if isinstance(data, dict) else data

			# Find matching event by ID
			for event in results:
				if event.get("id") == event_id:
					return event

			# If not found in first batch, try filtering by ID if API supports it
			# For now, raise not found error
			raise ValueError(f"Event {event_id} not found")


def convert_economic_activities(activity_names: List[Any]) -> List[int]:
	"""Convert economic activity names to IDs.

	Supports:
	- Integer IDs (passed through)
	- Exact name matches
	- Case-insensitive partial matches

	Args:
		activity_names: List of economic activity names or IDs

	Returns:
		List of economic activity IDs (integers)

	Raises:
		ValueError: If an activity name cannot be matched
	"""
	activity_ids = []

	for activity_input in activity_names:
		# If already an integer, pass through
		if isinstance(activity_input, int):
			activity_ids.append(activity_input)
			continue

		# Try exact match first
		if activity_input in ECONOMIC_ACTIVITY_TO_ID:
			activity_ids.append(ECONOMIC_ACTIVITY_TO_ID[activity_input])
			continue

		# Try case-insensitive match
		activity_lower = activity_input.lower()
		found = False
		for name, activity_id in ECONOMIC_ACTIVITY_TO_ID.items():
			if name.lower() == activity_lower:
				activity_ids.append(activity_id)
				found = True
				break

		if found:
			continue

		# Try partial match (contains)
		matches = []
		for name, activity_id in ECONOMIC_ACTIVITY_TO_ID.items():
			if activity_lower in name.lower() or name.lower() in activity_lower:
				matches.append((name, activity_id))

		if len(matches) == 1:
			activity_ids.append(matches[0][1])
		elif len(matches) > 1:
			match_names = [m[0] for m in matches[:5]]
			raise ValueError(
				f"Ambiguous economic activity '{activity_input}'. Multiple matches found: "
				f"{', '.join(match_names)}. Please be more specific."
			)
		else:
			raise ValueError(
				f"Unknown economic activity: '{activity_input}'. "
				f"Use dpa://reference/economic-activities resource to see available activities."
			)

	return activity_ids


def convert_policy_areas(policy_area_names: List[Any]) -> List[int]:
	"""Convert policy area names to IDs.

	Args:
		policy_area_names: List of policy area names or IDs

	Returns:
		List of policy area IDs (integers)

	Raises:
		ValueError: If a policy area name cannot be matched
	"""
	policy_ids = []

	for policy_input in policy_area_names:
		# If already an integer, pass through
		if isinstance(policy_input, int):
			policy_ids.append(policy_input)
			continue

		# Try exact match first
		if policy_input in POLICY_AREA_TO_ID:
			policy_ids.append(POLICY_AREA_TO_ID[policy_input])
			continue

		# Try case-insensitive match
		policy_lower = policy_input.lower()
		found = False
		for name, policy_id in POLICY_AREA_TO_ID.items():
			if name.lower() == policy_lower:
				policy_ids.append(policy_id)
				found = True
				break

		if not found:
			raise ValueError(
				f"Unknown policy area: '{policy_input}'. "
				f"Use dpa://reference/policy-areas resource to see available policy areas."
			)

	return policy_ids


def convert_event_types(event_type_names: List[Any]) -> List[int]:
	"""Convert event type names to IDs.

	Args:
		event_type_names: List of event type names or IDs

	Returns:
		List of event type IDs (integers)

	Raises:
		ValueError: If an event type name cannot be matched
	"""
	event_ids = []

	for event_input in event_type_names:
		# If already an integer, pass through
		if isinstance(event_input, int):
			event_ids.append(event_input)
			continue

		# Try exact match first (case-insensitive)
		event_lower = event_input.lower()
		found = False
		for name, event_id in EVENT_TYPE_TO_ID.items():
			if name.lower() == event_lower:
				event_ids.append(event_id)
				found = True
				break

		if not found:
			raise ValueError(
				f"Unknown event type: '{event_input}'. "
				f"Use dpa://reference/event-types resource to see available event types."
			)

	return event_ids


def convert_iso_to_dpa_ids(iso_codes: List[str]) -> List[int]:
	"""Convert ISO country codes to DPA jurisdiction IDs.

	Args:
		iso_codes: List of ISO 3-letter country codes

	Returns:
		List of DPA jurisdiction IDs (integers)

	Raises:
		ValueError: If an ISO code is not found in mapping
	"""
	dpa_ids = []
	for iso in iso_codes:
		iso_upper = iso.upper()
		if iso_upper not in ISO_TO_DPA_ID:
			raise ValueError(
				f"Unknown ISO country code: {iso}. "
				f"Please use standard ISO 3-letter codes (e.g., USA, CHN, DEU)."
			)
		dpa_ids.append(ISO_TO_DPA_ID[iso_upper])
	return dpa_ids


def build_filters(params: Dict[str, Any]) -> Dict[str, Any]:
	"""Build API filter dictionary from input parameters.

	Converts user-friendly parameters to DPA API format:
	- ISO codes to DPA jurisdiction IDs
	- Economic activity names to IDs
	- Policy area names to IDs
	- Event type names to IDs
	- Date ranges to event_period arrays
	- Field name mappings

	Args:
		params: Input parameters from Pydantic model

	Returns:
		Dictionary of filters for API request_data
	"""
	filters = {}

	# Convert implementing jurisdictions (ISO -> DPA IDs)
	if params.get('implementing_jurisdictions'):
		filters['implementing_jurisdiction'] = convert_iso_to_dpa_ids(
			params['implementing_jurisdictions']
		)

	# Convert economic activities
	if params.get('economic_activities'):
		filters['economic_activity'] = convert_economic_activities(
			params['economic_activities']
		)

	# Convert policy areas
	if params.get('policy_areas'):
		filters['policy_area'] = convert_policy_areas(params['policy_areas'])

	# Convert event types
	if params.get('event_types'):
		filters['event_type'] = convert_event_types(params['event_types'])

	# Convert government branch
	if params.get('government_branch'):
		branch_ids = []
		for branch in params['government_branch']:
			branch_lower = branch.lower()
			if branch_lower in GOVERNMENT_BRANCH_TO_ID:
				branch_ids.append(GOVERNMENT_BRANCH_TO_ID[branch_lower])
		if branch_ids:
			filters['government_branch'] = branch_ids

	# Convert DPA implementation level
	if params.get('dpa_implementation_level'):
		level_ids = []
		for level in params['dpa_implementation_level']:
			level_lower = level.lower()
			if level_lower in DPA_IMPLEMENTATION_LEVEL_TO_ID:
				level_ids.append(DPA_IMPLEMENTATION_LEVEL_TO_ID[level_lower])
		if level_ids:
			filters['dpa_implementation_level'] = level_ids

	# Handle event period dates
	event_period_start = params.get('event_period_start')
	event_period_end = params.get('event_period_end')
	if event_period_start or event_period_end:
		filters['event_period'] = [
			event_period_start or "2000-01-01",
			event_period_end or "2099-12-31"
		]
	else:
		# Always provide event_period to avoid API error
		filters['event_period'] = ["2000-01-01", "2099-12-31"]

	return filters
