"""Apollo MCP Server — Contact discovery and email enrichment via Apollo.io."""

import os
import sys

from mcp.server.fastmcp import FastMCP

from .api import ApolloClient
from .models import (
    PeopleSearchInput,
    CompanySearchInput,
    EnrichContactInput,
    FindContactEmailInput,
)
from .formatters import (
    format_people_results,
    format_company_results,
    format_enrichment_result,
    format_find_contact_result,
)


mcp = FastMCP("apollo_mcp")


def get_api_client() -> ApolloClient:
    """Get initialized Apollo API client with key from environment."""
    api_key = os.getenv("APOLLO_API_KEY")
    if not api_key:
        raise ValueError(
            "APOLLO_API_KEY environment variable not set. "
            "Please set your API key: export APOLLO_API_KEY='your-key-here'"
        )
    return ApolloClient(api_key)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def apollo_search_people(
    person_titles: list[str] | None = None,
    person_seniorities: list[str] | None = None,
    person_locations: list[str] | None = None,
    organization_domains: list[str] | None = None,
    organization_names: list[str] | None = None,
    keywords: str = "",
    per_page: int = 25,
    page: int = 1,
) -> str:
    """Search for contacts by company, job title, seniority, and location.

    FREE — no Apollo credits consumed. Returns obfuscated results (partial last
    names, no emails). Use apollo_enrich_contact with the returned Apollo ID to
    reveal full name and email.

    Args:
        person_titles: Job titles (e.g., ["VP Government Affairs", "Head of Trade Compliance"])
        person_seniorities: Levels: cxo, vp, director, head, senior_manager, manager
        person_locations: Locations in English (e.g., ["Germany", "United States"])
        organization_domains: Company domains (e.g., ["siemens.com"])
        organization_names: Company names (e.g., ["Siemens"])
        keywords: Free-text keyword filter
        per_page: Results per page (1-100, default 25)
        page: Page number (default 1)
    """
    params = PeopleSearchInput(
        person_titles=person_titles or [],
        person_seniorities=person_seniorities or [],
        person_locations=person_locations or [],
        organization_domains=organization_domains or [],
        organization_names=organization_names or [],
        keywords=keywords,
        per_page=per_page,
        page=page,
    )

    client = get_api_client()
    try:
        # Name-based search: pass q_organization_name directly to people search
        # (more reliable than resolving to org IDs, which misses accounts)
        # Domain-based search: resolve to org IDs first (workaround for broken
        # organization_domains filter in people search)
        org_ids: list[str] = []
        org_name_filter: str | None = None

        if params.organization_names:
            org_name_filter = params.organization_names[0]
        if params.organization_domains:
            org_ids = await client.resolve_org_ids(
                organization_domains=params.organization_domains or None,
            )
            if not org_ids:
                return ("## People Search Results\n\n"
                        "No matching organizations found for the provided domains. "
                        "Try searching by company name instead, or use "
                        "`apollo_search_company` to verify the domain.")

        result = await client.search_people(
            person_titles=params.person_titles or None,
            person_seniorities=params.person_seniorities or None,
            person_locations=params.person_locations or None,
            organization_ids=org_ids or None,
            organization_name=org_name_filter,
            keywords=params.keywords,
            per_page=params.per_page,
            page=params.page,
        )
        return format_people_results(result)
    finally:
        await client.close()


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def apollo_search_company(
    company_name: str = "",
    company_domain: str = "",
    per_page: int = 5,
) -> str:
    """Look up a company to get its Apollo org ID, domain, and metadata.

    FREE — no Apollo credits consumed.

    Args:
        company_name: Company name to search
        company_domain: Company domain (optional, more precise)
        per_page: Number of results (1-10, default 5)
    """
    params = CompanySearchInput(
        company_name=company_name,
        company_domain=company_domain,
        per_page=per_page,
    )

    if not params.company_name and not params.company_domain:
        return "Error: Provide at least one of `company_name` or `company_domain`."

    client = get_api_client()
    try:
        result = await client.search_organizations(
            organization_name=params.company_name,
            organization_domains=[params.company_domain] if params.company_domain else None,
            per_page=params.per_page,
        )
        return format_company_results(result)
    finally:
        await client.close()


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def apollo_enrich_contact(
    apollo_id: str = "",
    first_name: str = "",
    last_name: str = "",
    domain: str = "",
    organization_name: str = "",
    linkedin_url: str = "",
) -> str:
    """Get a person's email address. COSTS 1 APOLLO CREDIT per call.

    Preferred: pass apollo_id from search results (most reliable).
    Alternative: pass first_name + last_name + domain, or linkedin_url alone.

    Args:
        apollo_id: Apollo person ID from search results (preferred)
        first_name: Person's first name
        last_name: Person's last name
        domain: Company domain (required for name-based matching)
        organization_name: Company name (optional, improves matching)
        linkedin_url: LinkedIn profile URL (precise alternative to name+domain)
    """
    params = EnrichContactInput(
        apollo_id=apollo_id,
        first_name=first_name,
        last_name=last_name,
        domain=domain,
        organization_name=organization_name,
        linkedin_url=linkedin_url,
    )

    if not params.apollo_id and not params.linkedin_url and not (params.first_name and params.domain):
        return ("Error: Provide one of:\n"
                "- `apollo_id` from search results (preferred)\n"
                "- `first_name` + `last_name` + `domain`\n"
                "- `linkedin_url`")

    client = get_api_client()
    try:
        result = await client.enrich_person(
            apollo_id=params.apollo_id,
            first_name=params.first_name,
            last_name=params.last_name,
            domain=params.domain,
            organization_name=params.organization_name,
            linkedin_url=params.linkedin_url,
        )
        return format_enrichment_result(result)
    finally:
        await client.close()


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def apollo_find_contact_email(
    company_name: str = "",
    company_domain: str = "",
    job_title: str = "",
    person_name: str = "",
    seniority: str = "",
    location: str = "",
) -> str:
    """Find a person at a company and get their email in one step.
    COSTS 1 APOLLO CREDIT (search is free, enrichment costs 1 credit).

    Searches company -> finds matching person -> enriches for email.

    Args:
        company_name: Company name (at least one of company_name/company_domain required)
        company_domain: Company domain (more precise than name)
        job_title: Target job title (e.g., "VP Government Affairs")
        person_name: Person's name if already known
        seniority: Seniority level (cxo, vp, director, head, senior_manager, manager)
        location: Location filter (e.g., "Germany")
    """
    params = FindContactEmailInput(
        company_name=company_name,
        company_domain=company_domain,
        job_title=job_title,
        person_name=person_name,
        seniority=seniority,
        location=location,
    )

    if not params.company_name and not params.company_domain:
        return "Error: Provide at least one of `company_name` or `company_domain`."

    client = get_api_client()
    try:
        # Step 1: Resolve company to org ID (domain) or use name directly
        org_ids: list[str] = []
        if params.company_domain:
            org_ids = await client.resolve_org_ids(
                organization_domains=[params.company_domain],
            )

        # Step 2: Search for people at that org
        search_kwargs: dict = {
            "per_page": 10,
            "page": 1,
        }
        if org_ids:
            search_kwargs["organization_ids"] = org_ids
        elif params.company_name:
            search_kwargs["organization_name"] = params.company_name
        else:
            return ("## Find Contact Email\n\n"
                    f"Could not find organization for "
                    f"'{params.company_domain}'. "
                    "Try `apollo_search_company` to verify the company domain.\n\n"
                    "No credits were consumed.")
        if params.job_title:
            search_kwargs["person_titles"] = [params.job_title]
        if params.seniority:
            search_kwargs["person_seniorities"] = [params.seniority]
        if params.location:
            search_kwargs["person_locations"] = [params.location]
        if params.person_name:
            search_kwargs["keywords"] = params.person_name

        result = await client.search_people(**search_kwargs)
        people = result.get("people", [])
        total = result.get("total_entries", len(people))

        if not people:
            return ("## Find Contact Email\n\n"
                    "No matching contacts found at this organization. "
                    "Try broadening your search (remove title/seniority filters).\n\n"
                    "No credits were consumed (search is free).")

        # Step 3: Pick best match and enrich by Apollo ID
        best = people[0]
        apollo_id = best.get("id", "")

        enrichment = await client.enrich_person(apollo_id=apollo_id)

        return format_find_contact_result(best, enrichment, total)
    finally:
        await client.close()


def main() -> None:
    """Entry point for the Apollo MCP server."""
    api_key = os.getenv("APOLLO_API_KEY")
    if not api_key:
        print(
            "Error: APOLLO_API_KEY environment variable not set.\n"
            "Set it with: export APOLLO_API_KEY='your-key-here'",
            file=sys.stderr,
        )
        sys.exit(1)

    mcp.run()


if __name__ == "__main__":
    main()
