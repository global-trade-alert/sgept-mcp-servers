"""Apollo.io API client — async httpx wrapper with known-bug workarounds."""

from typing import Any

import httpx


class ApolloClient:
    """Thin async client for Apollo.io REST API.

    Known API quirks:
    - Organization name search requires `q_organization_name` (q_ prefix)
    - `organization_domains` filter in people search is broken —
      always resolve to org IDs first via org search
    - Company search returns TWO arrays: `accounts` (major/parent companies)
      and `organizations` (subsidiaries/smaller entities). Always check
      accounts first — the parent company is almost never in organizations.
    - People search endpoint was migrated from mixed_people/search to
      mixed_people/api_search (the old endpoint returns 422)
    - People search accepts `q_organization_name` as a direct filter —
      useful as fallback when org ID resolution fails
    - People search returns obfuscated last names (`last_name_obfuscated`)
      and boolean flags (`has_email`, `has_city`, etc.) — enrich to get full data
    - Enrich accepts Apollo person `id` directly — more reliable than name matching
    """

    BASE_URL = "https://api.apollo.io"
    PEOPLE_SEARCH_URL = "/api/v1/mixed_people/api_search"
    ORG_SEARCH_URL = "/api/v1/mixed_companies/search"
    ENRICH_URL = "/api/v1/people/match"

    def __init__(self, api_key: str) -> None:
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "X-Api-Key": api_key,
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "accept": "application/json",
            },
            timeout=15.0,
        )

    async def search_organizations(
        self,
        *,
        organization_name: str = "",
        organization_domains: list[str] | None = None,
        per_page: int = 5,
        page: int = 1,
    ) -> dict[str, Any]:
        """Search for organizations. Free, no credits consumed."""
        payload: dict[str, Any] = {
            "per_page": min(per_page, 100),
            "page": page,
        }
        if organization_name:
            payload["q_organization_name"] = organization_name
        if organization_domains:
            payload["organization_domains"] = organization_domains

        response = await self.client.post(self.ORG_SEARCH_URL, json=payload)
        response.raise_for_status()
        return response.json()

    async def resolve_org_ids(
        self,
        *,
        organization_domains: list[str] | None = None,
        organization_names: list[str] | None = None,
    ) -> list[str]:
        """Resolve company domains/names to Apollo organization IDs.

        This is the workaround for the broken organization_domains filter
        in the people search endpoint.

        NOTE: Apollo returns major/parent companies in `accounts` and
        smaller entities/subsidiaries in `organizations`. We check both,
        preferring accounts (which contain the parent company).
        """
        org_ids: list[str] = []

        if organization_domains:
            for domain in organization_domains:
                result = await self.search_organizations(
                    organization_domains=[domain], per_page=1
                )
                for acct in result.get("accounts", []):
                    if acct.get("id"):
                        org_ids.append(acct["id"])
                if not org_ids:
                    for org in result.get("organizations", []):
                        if org.get("id"):
                            org_ids.append(org["id"])

        if organization_names:
            for name in organization_names:
                result = await self.search_organizations(
                    organization_name=name, per_page=1
                )
                ids_before = len(org_ids)
                for acct in result.get("accounts", []):
                    if acct.get("id"):
                        org_ids.append(acct["id"])
                if len(org_ids) == ids_before:
                    for org in result.get("organizations", []):
                        if org.get("id"):
                            org_ids.append(org["id"])

        return org_ids

    async def search_people(
        self,
        *,
        person_titles: list[str] | None = None,
        person_seniorities: list[str] | None = None,
        person_locations: list[str] | None = None,
        organization_ids: list[str] | None = None,
        organization_name: str | None = None,
        keywords: str = "",
        per_page: int = 25,
        page: int = 1,
    ) -> dict[str, Any]:
        """Search for people. Free, no credits consumed.

        Returns obfuscated results (partial last names, no emails).
        Use enrich_person() with the returned `id` to get full details.

        NOTE: Do NOT pass organization_domains here — it's broken.
        Use resolve_org_ids() first, then pass organization_ids.
        Fallback: pass organization_name for q_organization_name filter.
        """
        payload: dict[str, Any] = {
            "per_page": min(per_page, 100),
            "page": page,
        }
        if person_titles:
            payload["person_titles"] = person_titles
        if person_seniorities:
            payload["person_seniorities"] = person_seniorities
        if person_locations:
            payload["person_locations"] = person_locations
        if organization_ids:
            payload["organization_ids"] = organization_ids
        if organization_name:
            payload["q_organization_name"] = organization_name
        if keywords:
            payload["q_keywords"] = keywords

        response = await self.client.post(self.PEOPLE_SEARCH_URL, json=payload)
        response.raise_for_status()
        return response.json()

    async def enrich_person(
        self,
        *,
        apollo_id: str = "",
        first_name: str = "",
        last_name: str = "",
        domain: str = "",
        organization_name: str = "",
        linkedin_url: str = "",
    ) -> dict[str, Any]:
        """Enrich a person to get their email. Costs 1 Apollo credit.

        Preferred: pass `apollo_id` from search results for exact matching.
        Alternative: pass first_name + last_name + domain for fuzzy matching.
        """
        payload: dict[str, Any] = {}
        if apollo_id:
            payload["id"] = apollo_id
        else:
            if first_name:
                payload["first_name"] = first_name
            if last_name:
                payload["last_name"] = last_name
        if domain:
            payload["domain"] = domain
        if organization_name:
            payload["organization_name"] = organization_name
        if linkedin_url:
            payload["linkedin_url"] = linkedin_url

        response = await self.client.post(self.ENRICH_URL, json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()
