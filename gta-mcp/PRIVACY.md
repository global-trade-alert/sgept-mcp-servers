# Privacy Policy — GTA MCP Server

**Effective date:** 18 February 2026
**Last updated:** 18 February 2026
**Data controller:** St Gallen Endowment for Prosperity through Trade (SGEPT)

This policy explains how the GTA MCP server (`sgept-gta-mcp`) handles data
when you use it to query the Global Trade Alert database.

## What this server does

The GTA MCP server is a local tool that runs on your machine. It receives
your search parameters (country codes, product codes, date filters, keywords),
forwards them to the GTA API backend, and returns the results. It does not
store, cache, or log any of your queries locally.

## What data is collected

### By the MCP server (on your machine)
None. The server processes your queries in memory and discards them after
each request. No logs are written. No data is cached between sessions.

### By the GTA API backend
When your query is forwarded to the GTA API at `api.globaltradealert.org`,
the backend records standard web server access logs:

- Timestamp of the request
- API endpoint called
- HTTP status code (success/error)
- Response time

**The content of your query (search filters, keywords, country selections)
is not logged by the backend.** Query parameters are processed in real time
and not retained.

Access logs are retained for 90 days for operational monitoring and
debugging, then automatically deleted.

### What is NOT collected
- Your identity (the server does not know who you are)
- Your IP address (the server does not forward IP headers)
- Your conversation history with Claude
- Your local files or Claude memory
- Any data beyond the search parameters you provide

## How your data is used

Query parameters are used exclusively to retrieve matching trade policy
records from the GTA database. There is no secondary use:

- No analytics or profiling
- No advertising or marketing
- No training of AI models
- No sharing with third parties

## Third-party services

The GTA MCP server connects to one external service only:

| Service | Purpose | Data sent | Operator |
|---------|---------|-----------|----------|
| GTA API (`api.globaltradealert.org`) | Query processing | Search filters + API key | SGEPT |

SGEPT operates both the MCP server and the GTA API backend. No data is
shared with third parties.

## Data security

- All communication with the GTA API uses HTTPS (TLS encryption in transit)
- API authentication uses a key provided by you, stored only in your local
  environment variables
- The MCP server runs locally on your machine — your queries do not pass
  through any intermediary

## Your rights

You may contact us at any time to:

- **Request information** about what data we hold (which, given the above,
  is limited to access logs containing no query content)
- **Request deletion** of access log entries associated with your API key
- **Withdraw access** by revoking your API key

If you are in the EU/EEA, you have additional rights under the GDPR
including the right to lodge a complaint with your local supervisory
authority.

## Children

This service is designed for professional trade policy research and is not
directed at children under 18.

## Changes to this policy

We will update this page if our data practices change. Material changes
will be noted in the CHANGELOG.

## Contact

**Data controller:** St Gallen Endowment for Prosperity through Trade (SGEPT)
**Email:** privacy@sgept.org
**General support:** support@sgept.org
**Website:** https://www.sgept.org
