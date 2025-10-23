"""Pydantic models for DPA MCP server input validation."""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ResponseFormat(str, Enum):
	"""Output format for tool responses."""
	MARKDOWN = "markdown"
	JSON = "json"


class DPASearchInput(BaseModel):
	"""Input model for searching DPA digital policy events."""

	model_config = ConfigDict(
		str_strip_whitespace=True,
		validate_assignment=True,
		extra='forbid'
	)

	implementing_jurisdictions: Optional[List[str]] = Field(
		default=None,
		description="List of implementing jurisdiction ISO codes (e.g., ['USA', 'CHN', 'DEU']). "
				   "Filter events by countries that implemented the digital policy."
	)

	economic_activities: Optional[List[str]] = Field(
		default=None,
		description="List of economic activity names (e.g., ['ML and AI development', 'platform intermediary: user-generated content']). "
				   "Filter events by affected digital economic sectors."
	)

	policy_areas: Optional[List[str]] = Field(
		default=None,
		description="List of policy area names (e.g., ['Data governance', 'Content moderation', 'Competition']). "
				   "Filter events by policy domain."
	)

	event_types: Optional[List[str]] = Field(
		default=None,
		description="List of event type names (e.g., ['law', 'order', 'decision', 'investigation']). "
				   "Filter by type of regulatory action."
	)

	government_branch: Optional[List[str]] = Field(
		default=None,
		description="List of government branches: 'legislature', 'executive', or 'judiciary'. "
				   "Filter by branch of government responsible for the policy."
	)

	dpa_implementation_level: Optional[List[str]] = Field(
		default=None,
		description="List of implementation levels: 'national', 'supranational', 'subnational', 'bi- or plurilateral agreement', 'multilateral agreement', 'other'. "
				   "Filter by scope of policy implementation."
	)

	event_period_start: Optional[str] = Field(
		default=None,
		description="Filter events occurring on or after this date (ISO format: YYYY-MM-DD, e.g., '2024-01-01')"
	)

	event_period_end: Optional[str] = Field(
		default=None,
		description="Filter events occurring on or before this date (ISO format: YYYY-MM-DD)"
	)

	limit: int = Field(
		default=50,
		description="Maximum number of events to return (1-1000)",
		ge=1,
		le=1000
	)

	offset: int = Field(
		default=0,
		description="Number of results to skip for pagination",
		ge=0
	)

	sorting: Optional[str] = Field(
		default="-id",
		description=(
			"Sort order for results. Common values:\n"
			"- '-id': Newest events first (RECOMMENDED for finding recent data)\n"
			"- 'id': Oldest events first\n"
			"- '-date': Events by date descending\n"
			"- 'date': Events by date ascending\n"
			"Use '-' prefix for descending order."
		)
	)

	response_format: ResponseFormat = Field(
		default=ResponseFormat.MARKDOWN,
		description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
	)

	@field_validator('implementing_jurisdictions')
	@classmethod
	def validate_iso_codes(cls, v: Optional[List[str]]) -> Optional[List[str]]:
		"""Ensure ISO codes are uppercase."""
		if v is not None:
			return [code.upper() for code in v]
		return v


class DPAGetEventInput(BaseModel):
	"""Input model for fetching a specific digital policy event."""

	model_config = ConfigDict(
		str_strip_whitespace=True,
		validate_assignment=True,
		extra='forbid'
	)

	event_id: int = Field(
		...,
		description="The unique DPA event ID (e.g., 20442)",
		gt=0
	)

	response_format: ResponseFormat = Field(
		default=ResponseFormat.MARKDOWN,
		description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
	)
