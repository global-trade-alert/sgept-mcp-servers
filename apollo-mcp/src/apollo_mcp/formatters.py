"""Markdown response formatters for Apollo MCP tools."""

from typing import Any


def format_people_results(data: dict[str, Any]) -> str:
    """Format people search results as a markdown table.

    The new api_search endpoint returns obfuscated data:
    - `first_name` + `last_name_obfuscated` (partial last name like "He***t")
    - `has_email` boolean flag (whether email exists to enrich)
    - `id` for use with enrich endpoint
    """
    people = data.get("people", [])
    total = data.get("total_entries", len(people))

    if not people:
        return "## People Search Results\n\nNo results found. Try broadening your search criteria."

    lines = [
        f"## People Search Results ({total} total)",
        "",
        "| # | Name | Title | Company | Has Email | Apollo ID |",
        "|---|------|-------|---------|-----------|-----------|",
    ]

    for i, person in enumerate(people, start=1):
        first = person.get("first_name", "")  or ""
        last_obf = person.get("last_name_obfuscated", "") or ""
        name = f"{first} {last_obf}".strip() or "—"
        title = person.get("title", "—") or "—"
        org = person.get("organization", {}) or {}
        company = org.get("name", "—") or "—"
        has_email = person.get("has_email", False)
        email_indicator = "Yes" if has_email else "No"
        apollo_id = person.get("id", "—")
        lines.append(f"| {i} | {name} | {title} | {company} | {email_indicator} | {apollo_id} |")

    lines.append("")
    lines.append("*Last names are partially obfuscated in search results. "
                 "Use `apollo_enrich_contact` with the Apollo ID to reveal full name and email (costs 1 credit).*")

    return "\n".join(lines)


def format_company_results(data: dict[str, Any]) -> str:
    """Format organization search results as a markdown table."""
    orgs = data.get("organizations", [])

    if not orgs:
        return "## Company Search Results\n\nNo results found."

    lines = [
        f"## Company Search Results ({len(orgs)} found)",
        "",
        "| # | Company | Domain | Industry | Employees | Apollo Org ID |",
        "|---|---------|--------|----------|-----------|---------------|",
    ]

    for i, org in enumerate(orgs, start=1):
        name = org.get("name", "—")
        domain = org.get("primary_domain", "—") or org.get("domain", "—") or "—"
        industry = org.get("industry", "—") or "—"
        employees = org.get("estimated_num_employees", "—")
        if employees and employees != "—":
            employees = f"{employees:,}" if isinstance(employees, int) else str(employees)
        org_id = org.get("id", "—")
        lines.append(f"| {i} | {name} | {domain} | {industry} | {employees} | {org_id} |")

    return "\n".join(lines)


def format_enrichment_result(data: dict[str, Any]) -> str:
    """Format person enrichment result as a markdown table."""
    person = data.get("person", {}) or data

    if not person or not person.get("id"):
        return ("## Contact Enrichment Failed\n\n"
                "No match found for the provided details. "
                "Try using an Apollo ID from search results, or add a LinkedIn URL.\n\n"
                "**CREDIT USED: 1 Apollo credit was consumed for this lookup attempt.**")

    name = person.get("name", "—") or "—"
    title = person.get("title", "—") or "—"
    email = person.get("email", None)
    org = person.get("organization", {}) or {}
    company = org.get("name", person.get("organization_name", "—")) or "—"
    domain = org.get("primary_domain", "—") or "—"
    linkedin = person.get("linkedin_url", "—") or "—"

    email_display = email if email else "Not found (person matched but email not available)"

    lines = [
        "## Contact Enriched",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Name | {name} |",
        f"| Title | {title} |",
        f"| Company | {company} |",
        f"| Domain | {domain} |",
        f"| Email | {email_display} |",
        f"| LinkedIn | {linkedin} |",
        "",
        "**CREDIT USED: 1 Apollo credit consumed for this enrichment.**",
    ]

    return "\n".join(lines)


def format_find_contact_result(
    person: dict[str, Any] | None,
    enrichment: dict[str, Any] | None,
    search_total: int,
) -> str:
    """Format the combined find-contact-email result."""
    if not person:
        return ("## Find Contact Email\n\n"
                "No matching contacts found. Try different search criteria.\n\n"
                "No credits were consumed (search is free).")

    first = person.get("first_name", "") or ""
    last_obf = person.get("last_name_obfuscated", "") or ""
    search_name = f"{first} {last_obf}".strip() or "—"
    title = person.get("title", "—") or "—"
    org = person.get("organization", {}) or {}
    company = org.get("name", "—") or "—"

    if not enrichment:
        return (f"## Find Contact Email\n\n"
                f"Found **{search_name}** ({title} at {company}) but enrichment failed.\n\n"
                f"**CREDIT USED: 1 Apollo credit consumed for this enrichment attempt.**")

    enriched_person = enrichment.get("person", {}) or enrichment
    full_name = enriched_person.get("name", search_name) or search_name
    email = enriched_person.get("email", None)
    email_display = email if email else "Not found (person matched but email not available)"
    linkedin = enriched_person.get("linkedin_url", "—") or "—"
    enriched_org = enriched_person.get("organization", {}) or {}
    domain = enriched_org.get("primary_domain", "—") or "—"

    lines = [
        "## Contact Found & Enriched",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Name | {full_name} |",
        f"| Title | {title} |",
        f"| Company | {company} |",
        f"| Domain | {domain} |",
        f"| Email | {email_display} |",
        f"| LinkedIn | {linkedin} |",
        "",
        f"*Selected from {search_total} matching contacts.*",
        "",
        "**CREDIT USED: 1 Apollo credit consumed for this enrichment.**",
    ]

    return "\n".join(lines)
