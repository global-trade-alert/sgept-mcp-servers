# Iran Monitor API — Public Access Surface Proposal

**Generated:** 2026-05-12
**Status:** AWAITING CEO DECISION
**Related:** JCC-958 (Phase 1 scaffold), JCC-961 (spike PASS), JCC-956 (buyer call)
**Decision needed:** Which access-surface archetype to build, with what scope.

---

## What "access surface" means

For an external buyer to actually use the iran-monitor-api, five dimensions need answers:

| Dimension | Question |
|---|---|
| **Discovery** | How does a potential buyer find out this exists? |
| **Evaluation** | What does a prospect see before deciding to commit? |
| **Onboarding** | What happens after a commitment to use it? |
| **Steady-state** | What does day-to-day use look like? |
| **Renewal/expansion** | How does the relationship grow over time? |

Different archetypes bundle different choices across these dimensions. The right archetype depends on (a) whether the goal right now is *validating the wedge* or *scaling distribution*, and (b) whether buyers are humans operating curl/SDK calls or backend systems that consume the API directly.

---

## Five archetypes

### Archetype A — **Concierge B2B (dark-mode pilot)**

The minimum viable shape. **No public marketing.** CEO emails the named buyer with their API key, a 2-page onboarding PDF, and a curl recipe. The service lives at `api.iran-monitor.sgept.org` over TLS, but the URL is not discoverable. Pricing is bespoke per pilot.

| Dimension | Detail |
|---|---|
| Discovery | CEO outreach + word-of-mouth only |
| Evaluation | Live demo on a Zoom call, walking through one real query |
| Onboarding | Single email with key + PDF + offer of pairing session |
| Steady-state | Buyer calls REST endpoint from their backend; daily/intraday cadence |
| Renewal/expansion | CEO renegotiates annually; new seats added by request |

**Effort to ship:** 1–2 days of operational work on Metis (Caddy + DNS + key issuance + onboarding PDF). Zero new code beyond what's already committed.

**Right when:** You're validating the wedge with one specific buyer and want to learn before investing in discovery infra. Matches the design doc's "first paying pilot in 90 days" target.

**Wrong when:** You expect inbound demand from prospects who'd find a landing page; or when the buyer is themselves a team that wants to evaluate before committing budget; or when sales scales beyond what CEO time can support.

### Archetype B — **Gated developer portal**

A public landing page at `iran-monitor.sgept.org` that explains what the service is, shows a sample query/response, and routes prospects to a "request access" form (mailto or Typeform). CEO still mints keys manually after a qualification conversation. API surface unchanged from A. Documentation lives at `docs.iran-monitor.sgept.org` with curl examples, the audit-record schema, error taxonomy, and a sample Python SDK.

| Dimension | Detail |
|---|---|
| Discovery | Landing page picked up by inbound traffic (LinkedIn posts, podcast mentions, conference traffic, search) |
| Evaluation | Landing page sample query → "request access" → CEO qualification call → optionally a 7-day eval key |
| Onboarding | Self-serve docs + sample SDK; CEO issues production key after eval |
| Steady-state | Same as A but documented properly |
| Renewal/expansion | CEO still owns enterprise renewals; eval keys auto-expire |

**Effort to ship:** 4–6 days. Landing page + docs site + sample Python SDK + key-issuance script + signup form wiring. Code-wise: a one-page static site, a Python client package, and a small ops script. No changes to the API service itself.

**Right when:** The wedge is validated by ≥1 paying pilot and you want to capture inbound interest without rushing into self-serve billing. Lets you test discovery messaging cheaply.

**Wrong when:** You haven't yet validated even one pilot (premature marketing surface invites unqualified leads); or when self-serve adoption is the actual goal.

### Archetype C — **Self-serve paid API (Stripe + auto-provisioning)**

Public marketing surface + Stripe checkout that auto-mints keys + usage-metered billing + dunning + invoicing. Tiers: free (1 Standard query/month), Pro (£2k/month, 30 Standard + 5 Premium), Enterprise (£10–20k/month, custom limits, SOC2 docs, DPA). Full developer documentation. Optionally a status page.

| Dimension | Detail |
|---|---|
| Discovery | Same as B + organic + paid acquisition |
| Evaluation | Self-serve free tier (1 query/month) hands-on |
| Onboarding | Automatic on Stripe checkout |
| Steady-state | Buyer integrates from backend; usage tracked + invoiced monthly |
| Renewal/expansion | Auto-renewal; upgrade self-serve |

**Effort to ship:** 2–4 weeks. Stripe webhook plumbing, metering at query time, dunning email automation, invoice generation, customer portal, dispute handling. Plus everything in B.

**Right when:** You've validated the wedge across 2–3 pilots AND you're confident the product surface is stable enough to support self-serve users without high-touch onboarding. Long-term steady-state.

**Wrong when:** You're still iterating on the product; you don't have ops bandwidth for billing edge cases; or your buyers will all be procurement-heavy enterprise contracts that won't go through Stripe.

### Archetype D — **Human-first chat surface (web UI)**

A simple authenticated web page where a logged-in analyst types a scenario description into a textarea, sees a status indicator while the query runs, then sees a rendered result card with probability, perspective breakdown, and links to download the signed audit record. No raw REST/MCP surface for buyers — they get a URL and a username/password (or SSO).

| Dimension | Detail |
|---|---|
| Discovery | Same as A or B (gated or public landing as preferred) |
| Evaluation | Demo URL with a sample query already pre-filled |
| Onboarding | Email a magic-link or shared SSO config |
| Steady-state | Analyst opens browser, types scenario, polls |
| Renewal/expansion | More seats = more accounts |

**Effort to ship:** 5–7 days. A small Next.js/SvelteKit frontend + auth layer + use the REST API as backend. Plus the existing REST surface stays available for buyers who want both.

**Right when:** The named buyer's actual users are humans (analysts, portfolio risk officers) who don't have a backend integration in mind. Or when you want a UI for sales demos that doesn't require Postman/curl.

**Wrong when:** The buyer's value is in backend automation (alerts, workflow integration). Or when adding UI maintenance cost is too much.

### Archetype E — **MCP-first (agent-to-agent native)**

Ship a stdio MCP server that wraps the REST API. List it on Anthropic's MCP server registry and modelcontextprotocol.io. Buyers' AI agents (Claude Desktop, Cursor, etc.) discover it and invoke it natively.

| Dimension | Detail |
|---|---|
| Discovery | MCP registries; "AI for agentic finance" thought leadership |
| Evaluation | Add to local MCP config; immediately usable from an agent |
| Onboarding | Pass API key in MCP server env |
| Steady-state | Agent invokes our tool as one option among many |
| Renewal/expansion | Per-agent or per-org licensing |

**Effort to ship:** 2–3 days for the stdio MCP wrapper (pattern exists in cc-os mcp-servers). Plus discovery and evangelism effort.

**Right when:** The buyer's workflow is "their LLM agent calls our API as a tool" — which is the exact phrasing from the office-hours buyer ask. Strategic positioning bet that AI-agent ecosystems will be a meaningful B2B distribution channel.

**Wrong when:** The named buyer (institutional risk desk) doesn't actually run MCP-native agents yet. Probably no risk desk does in May 2026.

---

## My recommendation: **A + a thin slice of B** (hybrid)

Pure concierge for the actual paying pilot. **Plus** a single-page landing site with the marketing pitch and a "request access" mailto so inbound interest from peers / press / future prospects isn't lost. No self-serve, no chat UI, no MCP wrapper in this phase.

Why:

1. **The wedge isn't validated yet.** Without ≥1 paying pilot, every hour invested in scale-out infra (Stripe, chat UI, MCP wrapper) is speculative. Concierge is the fastest path to learning whether the buyer actually pays.
2. **The named buyer's workflow is "their agent calls our API"** (verbatim from the office hours). That's a REST/curl integration from their backend. No chat UI needed; no MCP wrapper needed (unless they explicitly ask).
3. **A landing page is cheap and load-bearing as marketing.** Premise #5 of the design doc says the public website stays as top-of-funnel. A one-page site at `iran-monitor.sgept.org` is the minimum-viable execution of that premise. Even if nobody uses the "request access" form for the first 90 days, the page itself gives credibility on sales calls ("here, look at the public-facing description").
4. **A + thin B keeps optionality open.** If the named buyer integrates and starts using it heavily, you can layer D (chat UI for analyst-side users at the same buyer), C (self-serve for follow-on prospects), or E (MCP wrapper if the buyer's agent stack changes) as separate Phase-2 cards. None of these foreclose each other.
5. **Effort is bounded.** ~3 days of work end-to-end, mostly already-built scaffolding. Won't blow the 7–10 week Phase 1 budget.

What this means concretely if you pick A + thin B:

| Day | Build |
|---|---|
| 1 | Caddy reverse proxy + DNS + Let's Encrypt on `api.iran-monitor.sgept.org`. Generate production Ed25519 signing key (in SOPS-encrypted env). Issue first pilot API key. Run install-on-metis.sh. |
| 2 | ONBOARDING.md (2 pages, curl + Python examples + signature verification snippet + escalation contact). Python SDK package (one file, ~100 LOC). curl recipe sheet. |
| 3 | Single-page landing at `iran-monitor.sgept.org` — what it is, sample query/response, "request access" mailto. Hosted as a static page from Caddy. |

Plus operational scripts:

- `scripts/add-pilot-key.py` — append a new `(api-key, org_id)` to the SOPS-encrypted env. CLI: `add-pilot-key.py acme-capital → emits key + org_id`.
- `scripts/rotate-signing-key.py` — for the annual rotation in the design doc.

What stays explicitly OUT of this phase:

- No self-serve signup (no Stripe).
- No chat UI.
- No MCP stdio wrapper (deferred to Phase 2; let the buyer call confirm whether they want it).
- No status page (UptimeRobot ping is sufficient for the pilot).
- No public documentation site beyond the ONBOARDING.md sent to the pilot directly.
- No free tier.

---

## Alternative: if A + thin B feels too narrow

If your read is that the JCC-956 buyer call returns something different — e.g. they say their agent stack IS MCP-native, or they say their *users* are humans not backends — pivot to E or D respectively. The buyer call is the single biggest input to which archetype is right.

**If A+B feels too aggressive**: pure A (no landing page). Acceptable if you want to delay any public signal until the wedge is paid for at least once.

**If A+B feels too narrow**: A + B + E (concierge + landing + MCP wrapper). The MCP wrapper is 2–3 days extra and hedges on the agent-ecosystem play. Defensible if you want to test "do AI agents try to integrate our tool" as a discovery signal in parallel.

---

## Decision needed from CEO

Pick one of:

- **A only** (pure concierge, no public surface)
- **A + thin B** ← my recommendation
- **A + B + E** (add MCP wrapper as a hedge)
- **D** (chat UI instead of API as primary surface)
- **C** (full self-serve — explicit "scale-out before validation" choice)
- **Custom** (mix-and-match different pieces)

Once chosen, I'll implement against that scope. The technical building blocks are mostly already in the repo or trivially extendable from it; the choice is product/sales strategy, not engineering.
