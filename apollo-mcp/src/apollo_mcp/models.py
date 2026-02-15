"""Pydantic input models for Apollo MCP tools."""

from pydantic import BaseModel, Field


class PeopleSearchInput(BaseModel):
    """Input for searching people on Apollo.io. Free, no credits consumed."""

    person_titles: list[str] = Field(
        default_factory=list,
        description="Job titles to search (e.g., ['VP Government Affairs', 'Head of Trade Compliance'])",
    )
    person_seniorities: list[str] = Field(
        default_factory=list,
        description="Seniority levels: cxo, vp, director, head, senior_manager, manager",
    )
    person_locations: list[str] = Field(
        default_factory=list,
        description="Locations in English (e.g., ['Germany', 'United States'])",
    )
    organization_domains: list[str] = Field(
        default_factory=list,
        description="Company domains (e.g., ['siemens.com']). Uses org-ID workaround internally.",
    )
    organization_names: list[str] = Field(
        default_factory=list,
        description="Company names (e.g., ['Siemens']). Resolved to org IDs internally.",
    )
    keywords: str = Field(
        default="",
        description="Additional keyword filter for free-text search",
    )
    per_page: int = Field(default=25, ge=1, le=100, description="Results per page (1-100)")
    page: int = Field(default=1, ge=1, description="Page number")


class CompanySearchInput(BaseModel):
    """Input for searching companies on Apollo.io. Free, no credits consumed."""

    company_name: str = Field(default="", description="Company name to search")
    company_domain: str = Field(default="", description="Company domain (more precise)")
    per_page: int = Field(default=5, ge=1, le=10, description="Results (1-10)")


class EnrichContactInput(BaseModel):
    """Input for enriching a contact to get their email. Costs 1 Apollo credit."""

    apollo_id: str = Field(default="", description="Apollo person ID from search results (preferred, most reliable)")
    first_name: str = Field(default="", description="Person's first name (use with last_name + domain)")
    last_name: str = Field(default="", description="Person's last name")
    domain: str = Field(default="", description="Company domain (improves matching)")
    organization_name: str = Field(default="", description="Company name (optional)")
    linkedin_url: str = Field(default="", description="LinkedIn profile URL (most precise alternative)")


class FindContactEmailInput(BaseModel):
    """Input for the convenience find-and-enrich tool. Costs 1 Apollo credit."""

    company_name: str = Field(default="", description="Company name")
    company_domain: str = Field(default="", description="Company domain")
    job_title: str = Field(default="", description="Target job title (e.g., 'VP Government Affairs')")
    person_name: str = Field(default="", description="Person's name if already known")
    seniority: str = Field(default="", description="Seniority level (cxo, vp, director, etc.)")
    location: str = Field(default="", description="Location filter")
