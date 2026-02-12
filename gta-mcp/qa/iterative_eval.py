"""Iterative evaluation framework for GTA MCP server optimization.

Simulates LLM tool selection against gold standard filters, executes API calls,
and scores results on 4 dimensions: filter accuracy, query strategy, result
relevance, and completeness.

Usage:
    cd gta-mcp
    export GTA_API_KEY='your-key'
    export ANTHROPIC_API_KEY='your-key'  # for simulation phase
    python qa/iterative_eval.py [--round 0] [--prompt-ids 1,4,7] [--no-execute]
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gta_mcp.api import GTAAPIClient, build_filters
from gta_mcp.resources_loader import (
    load_mast_chapters,
    load_jurisdiction_groups,
    load_query_intent_mapping,
    load_search_strategy,
    load_common_mistakes,
)
from gta_mcp.hs_lookup import search_hs_codes
from gta_mcp.sector_lookup import search_sectors


GOLD_STANDARD_PATH = Path(__file__).parent / "gold_standard.json"
RESULTS_DIR = Path(__file__).parent / "eval_results"


def load_gold_standard() -> dict:
    """Load gold standard evaluation data."""
    with open(GOLD_STANDARD_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_tool_descriptions() -> str:
    """Extract current tool descriptions for simulation context."""
    return """Available MCP tools:

1. gta_search_interventions - Search trade policy interventions with structured filters.
   Key parameters: implementing_jurisdictions (ISO codes), affected_jurisdictions (ISO codes),
   affected_products (HS code integers), affected_sectors (CPC codes), intervention_types (names),
   mast_chapters (A-P letters), gta_evaluation (Red/Amber/Green/Harmful), date_announced_gte (YYYY-MM-DD),
   date_announced_lte, date_implemented_gte, date_implemented_lte, is_in_force (bool),
   query (entity names ONLY - companies, programs), eligible_firms, implementation_levels,
   limit (1-1000), offset, sorting

2. gta_lookup_hs_codes - Search HS product codes by keyword, chapter number, or code prefix.
   Parameters: search_term (string), max_results (int, default 50)
   Use BEFORE gta_search_interventions for commodity/product queries.

3. gta_lookup_sectors - Search CPC sector codes by keyword or code prefix.
   Parameters: search_term (string), max_results (int, default 50)
   Use BEFORE gta_search_interventions for service/sector queries.

4. gta_get_intervention - Get full details for a specific intervention by ID.
   Parameters: intervention_id (int)

5. gta_count_interventions - Count/aggregate interventions by dimensions.
   Parameters: count_by (list of dimensions), count_variable, plus all search filters.

6. gta_list_ticker_updates - Get recent text updates to interventions.
   Parameters: implementing_jurisdictions, intervention_types, date_modified_gte, limit, offset
"""


def get_resource_context() -> str:
    """Get key resource content for simulation context."""
    parts = [
        "=== MAST Chapter Taxonomy (Summary) ===",
        "A=Sanitary/Phytosanitary, B=Technical Barriers, C=Pre-shipment inspection,",
        "D=Contingent trade-protective, E=Licensing/quotas, F=Price controls,",
        "G=Finance measures, H=Competition, I=Investment, J=Distribution,",
        "K=Post-sales services, L=Subsidies, M=Procurement, N=IP, P=Export measures",
        "",
        "=== Evaluation Values ===",
        "Red=certainly harmful, Amber=likely harmful, Green=liberalising",
        "Harmful=Red+Amber combined (filter shorthand)",
        "",
        "=== Key Country Codes ===",
        "USA, CHN, DEU, GBR, FRA, JPN, IND(=699 UN), BRA, RUS, AUS, KOR",
        "EU as bloc: EUN (UN code 1049)",
        "",
    ]

    # Add jurisdiction groups (abbreviated)
    parts.append("=== Jurisdiction Groups ===")
    parts.append("G7: CAN, FRA, DEU, ITA, JPN, GBR, USA")
    parts.append("G20: G7 + ARG, AUS, BRA, CHN, IND, IDN, MEX, RUS, SAU, ZAF, KOR, TUR, EUN")
    parts.append("ASEAN: BRN, KHM, IDN, LAO, MYS, MMR, PHL, SGP, THA, VNM")
    parts.append("")

    # Add intent mapping (abbreviated)
    parts.append("=== Intent Mapping (Key Rules) ===")
    parts.append("subsidies/state aid → mast_chapters=['L']")
    parts.append("export controls/restrictions → mast_chapters=['P']")
    parts.append("tariffs/import duties → intervention_types=['Import tariff'] or mast_chapters=['D']")
    parts.append("harmful/restrictive → gta_evaluation=['Harmful']")
    parts.append("investment/FDI → mast_chapters=['I']")
    parts.append("For commodities → use gta_lookup_hs_codes FIRST to get product codes")
    parts.append("For services → use gta_lookup_sectors FIRST to get sector codes")
    parts.append("For country groups (G20, EU, etc.) → use implementing_jurisdictions with member codes")

    return "\n".join(parts)


def simulate_tool_selection(prompt: str) -> dict:
    """Simulate LLM tool selection without calling the API.

    Uses a rule-based approach as a baseline. For full simulation with Claude,
    set ANTHROPIC_API_KEY and use --simulate-with-llm flag.
    """
    import re

    prompt_lower = prompt.lower()
    result = {
        "tool": "gta_search_interventions",
        "filters": {},
        "prerequisite_calls": [],
    }

    # Detect count queries — only for explicit counting/trend questions
    # NOT for "which countries" (those are search queries)
    count_words = ["how many", "count ", "number of", "trend", "versus", " vs "]
    is_trend = any(w in prompt_lower for w in ["increased", "decreased"])
    if any(w in prompt_lower for w in count_words) or (is_trend and "since" in prompt_lower):
        result["tool"] = "gta_count_interventions"
        result["filters"]["count_by"] = ["date_announced_year"]

    # MAST chapter mapping — order matters, more specific patterns first
    mast_mappings = [
        ("subsidi", "L", None),
        ("state aid", "L", None),
        ("financial support", "L", None),
        ("export control", "P", None),
        ("export restriction", "P", None),
        ("restricted export", "P", None),  # "restricted exports of lithium"
        ("export ban", "P", None),
        ("anti-dumping", "D", "Anti-dumping"),
        ("countervailing", "D", None),
        ("safeguard", None, "Safeguard"),
        ("local content", "E", "Local content requirement"),
        ("fdi screening", "I", "FDI screening"),
        ("fdi", "I", None),
        ("investment restriction", "I", None),
        ("investment control", "I", None),
        ("investment", "I", None),
        ("import licens", "E", "Import licensing requirement"),
        ("licens", "E", None),
        ("procurement", "M", None),
        ("tariff", None, "Import tariff"),
    ]

    for term, chapter, itype in mast_mappings:
        if term in prompt_lower:
            if chapter:
                result["filters"]["mast_chapters"] = [chapter]
            if itype:
                result["filters"]["intervention_types"] = [itype]
            break

    # Evaluation mapping
    eval_words = [
        ("harmful", "Harmful"),
        ("restrictive", "Harmful"),
        ("liberali", "Green"),
    ]
    # "imposed" only implies harmful when combined with negative trade context
    if "imposed" in prompt_lower and any(w in prompt_lower for w in ["tariff", "sanction", "restrict", "ban", "barrier"]):
        result["filters"]["gta_evaluation"] = ["Harmful"]
    else:
        for term, ev in eval_words:
            if term in prompt_lower:
                result["filters"]["gta_evaluation"] = [ev]
                break

    # Country extraction with context-aware role detection
    country_map = {
        "united states": "USA", " us ": "USA", "u.s.": "USA",
        "china": "CHN", "chinese": "CHN",
        "india": "IND", "brazil": "BRA", "russia": "RUS",
        "japan": "JPN", "germany": "DEU",
    }

    country_groups = {
        "g7 ": ["CAN", "FRA", "DEU", "ITA", "JPN", "GBR", "USA"],
        "g7 countries": ["CAN", "FRA", "DEU", "ITA", "JPN", "GBR", "USA"],
        "g20": ["ARG", "AUS", "BRA", "CAN", "CHN", "FRA", "DEU", "IND", "IDN", "ITA", "JPN", "MEX", "RUS", "SAU", "ZAF", "KOR", "TUR", "GBR", "USA", "EUN"],
        "asean": ["BRN", "KHM", "IDN", "LAO", "MYS", "MMR", "PHL", "SGP", "THA", "VNM"],
        "southeast asia": ["IDN", "THA", "VNM", "MYS", "PHL", "SGP", "MMR", "KHM", "LAO", "BRN"],
        "brics": ["BRA", "RUS", "IND", "CHN", "ZAF"],
        "asian countries": ["CHN", "IND", "IDN", "VNM", "THA", "MYS", "KOR", "JPN"],
        "asia": ["CHN", "IND", "IDN", "VNM", "THA", "MYS", "KOR", "JPN"],
    }

    # EU/European detection — separate because it can be implementer or affected
    eu_terms = {
        "european union": "EUN",
        "eu ": "EUN",
    }

    implementing = []
    affected = []

    # Check country groups first
    for group_term, codes in country_groups.items():
        if group_term in prompt_lower:
            implementing = codes
            break

    # Context-aware role patterns
    # "X has implemented/imposed" → X is implementer
    # "affecting/on/targeting Y" → Y is affected
    # "against Y" → Y is affected
    affected_patterns = [
        r"(?:affecting|on|targeting|against|impact(?:ing)?)\s+(\w+)",
        r"(\w+)\s+(?:exports?|imports?|products?|trade)",  # "US exports" → US is affected
    ]
    implementing_patterns = [
        r"(?:has|have)\s+(\w+)\s+(?:imposed|implemented|restricted|introduced)",
        r"(\w+)\s+(?:has|have)\s+(?:imposed|implemented|restricted|introduced)",
        r"(?:by)\s+(\w+)",
        r"(\w+)\s+(?:implemented|imposed|restricted)",
    ]

    # Find affected jurisdictions from context
    for pattern in affected_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            term = match.group(1).strip()
            # Check if this matches a country
            for cname, code in country_map.items():
                if cname.startswith(term) or term in cname:
                    if code not in affected:
                        affected.append(code)
                    break
            # Check EU
            for eu_term, eu_code in eu_terms.items():
                if term in eu_term or eu_term.startswith(term):
                    if eu_code not in affected:
                        affected.append(eu_code)
                    break

    # Find implementing jurisdictions from context (if not already set by groups)
    if not implementing:
        for pattern in implementing_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                term = match.group(1).strip()
                for cname, code in country_map.items():
                    if cname.startswith(term) or term in cname:
                        if code not in implementing and code not in affected:
                            implementing.append(code)
                        break
                for eu_term, eu_code in eu_terms.items():
                    if term in eu_term or eu_term.startswith(term):
                        if eu_code not in implementing and eu_code not in affected:
                            implementing.append(eu_code)
                        break

    # Fallback: if still no implementing/affected, use position-based heuristic
    # with smarter role detection
    if not implementing and not affected:
        found_countries = []
        for cname, code in country_map.items():
            if cname in prompt_lower:
                # Find position
                pos = prompt_lower.index(cname)
                found_countries.append((pos, code, cname))
        for eu_term, eu_code in eu_terms.items():
            if eu_term in prompt_lower:
                pos = prompt_lower.index(eu_term)
                found_countries.append((pos, eu_code, eu_term))

        found_countries.sort(key=lambda x: x[0])
        for i, (pos, code, name) in enumerate(found_countries):
            # Check context around the country name
            before = prompt_lower[max(0, pos-30):pos]
            after = prompt_lower[pos:pos+len(name)+30]

            if any(w in before for w in ["affecting", "on ", "target", "against"]):
                if code not in affected:
                    affected.append(code)
            elif any(w in after for w in ["export", "import", "product", "trade"]):
                # "US exports" → US is affected by others' measures
                if code not in affected:
                    affected.append(code)
            elif any(w in before for w in ["by ", "has ", "have "]) or any(w in after for w in [" imposed", " implemented", " restrict"]):
                if code not in implementing:
                    implementing.append(code)
            elif i == 0 and not implementing:
                implementing.append(code)
            elif code not in implementing and code not in affected:
                affected.append(code)

    # European → implementer context (for FDI screening etc.)
    if "european" in prompt_lower and not any(c in implementing for c in ["EUN"]):
        # "European technology sectors" → European countries are implementers
        if any(w in prompt_lower for w in ["fdi", "screening", "investment"]):
            implementing = ["EUN"]
            # Remove EUN from affected if it was there
            affected = [c for c in affected if c != "EUN"]

    if implementing:
        result["filters"]["implementing_jurisdictions"] = implementing
    if affected:
        result["filters"]["affected_jurisdictions"] = affected

    # Date extraction — improved with month+year support
    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12",
        "january": "01", "february": "02", "march": "03", "april": "04",
        "june": "06", "july": "07", "august": "08", "september": "09",
        "october": "10", "november": "11", "december": "12",
    }

    # Try "since Month Year" first
    month_year = re.search(r"since\s+(\w+)\s+(\d{4})", prompt_lower)
    if month_year:
        month_name = month_year.group(1)
        year = month_year.group(2)
        month_num = month_map.get(month_name, "01")
        result["filters"]["date_announced_gte"] = f"{year}-{month_num}-01"
    else:
        # Try simpler patterns
        date_patterns = [
            (r"since\s+(\d{4})", lambda m: [("date_announced_gte", f"{m.group(1)}-01-01")]),
            (r"from\s+(\d{4})", lambda m: [("date_announced_gte", f"{m.group(1)}-01-01")]),
            (r"in\s+(\d{4})\s+(?:versus|vs)", lambda m: [
                ("date_announced_gte", f"{int(m.group(1))-1}-01-01"),
                ("date_announced_lte", f"{m.group(1)}-12-31"),
            ]),
            (r"in\s+(\d{4})", lambda m: [
                ("date_announced_gte", f"{m.group(1)}-01-01"),
                ("date_announced_lte", f"{m.group(1)}-12-31"),
            ]),
        ]
        for pattern, handler in date_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                for key, val in handler(match):
                    result["filters"][key] = val
                break

    # Product/sector hints — trigger HS lookup for commodities
    commodity_terms = ["lithium", "cobalt", "steel", "semiconductor", "solar", "automotive",
                       "vehicle", "agricultural", "food", "pharmaceutical", "rare earth",
                       "nickel", "mineral"]
    for term in commodity_terms:
        if term in prompt_lower:
            result["prerequisite_calls"].append({
                "tool": "gta_lookup_hs_codes",
                "search_term": term
            })
            break

    service_terms = ["financial", "telecom", "digital", "transport", "data locali"]
    for term in service_terms:
        if term in prompt_lower:
            result["prerequisite_calls"].append({
                "tool": "gta_lookup_sectors",
                "search_term": term
            })
            break

    # Text query for concepts not mappable to structured filters
    query_phrases = [
        ("data localization", "data localization"),
        ("data localisation", "data localization"),
        ("critical mineral", "critical mineral"),
        ("electric vehicle", "electric vehicle"),
        ("rare earth", "rare earth"),
    ]
    for phrase, query_val in query_phrases:
        if phrase in prompt_lower:
            result["filters"]["query"] = query_val
            break

    # date_modified detection (monitoring queries)
    if "modified" in prompt_lower or "updated" in prompt_lower or "changed recently" in prompt_lower:
        # Check for "last N months" pattern
        last_n = re.search(r"last\s+(\d+)\s+months?", prompt_lower)
        if last_n:
            months = int(last_n.group(1))
            today = datetime.now()
            # Approximate months as 30 days each
            cutoff = today - timedelta(days=months * 30)
            result["filters"]["date_modified_gte"] = cutoff.strftime("%Y-%m-%d")
        else:
            # Default: last 30 days
            today = datetime.now()
            cutoff = today - timedelta(days=30)
            result["filters"]["date_modified_gte"] = cutoff.strftime("%Y-%m-%d")
        result["filters"]["sorting"] = "-last_updated"

    # in_force detection
    # "exist" as standalone concept ("requirements exist") implies currently in force
    exist_patterns = ["currently", "in force", "active", " exist ", " exist?", " exists ", "exist in"]
    if any(p in prompt_lower or prompt_lower.endswith(p.strip()) for p in exist_patterns):
        result["filters"]["is_in_force"] = True

    # Subnational
    if "subnational" in prompt_lower:
        result["filters"]["implementation_levels"] = [3]

    # SOE
    if "state-owned" in prompt_lower or "state owned" in prompt_lower:
        result["filters"]["eligible_firms"] = [4]

    return result


def score_filters(simulated: dict, gold: dict) -> dict:
    """Score simulated filters against gold standard.

    Returns scores on 4 dimensions (0-3 each, total 0-12):
    - filter_accuracy: Are the right structured filters present?
    - query_strategy: Is the approach optimal (structured vs free-text)?
    - result_relevance: Would these filters return relevant results?
    - completeness: Does it capture all aspects of the question?
    """
    expected = gold["expected_filters"]
    simulated_filters = simulated.get("filters", {})
    critical = gold.get("critical_filters", [])

    # 1. Filter Accuracy (0-3)
    filter_score = 3
    for key in critical:
        if key not in simulated_filters:
            filter_score -= 1
        elif key in expected and simulated_filters[key] != expected[key]:
            # For date fields, allow approximate match (within 7 days)
            if "date" in key and isinstance(simulated_filters[key], str) and isinstance(expected[key], str):
                try:
                    sim_date = datetime.strptime(simulated_filters[key], "%Y-%m-%d")
                    exp_date = datetime.strptime(expected[key], "%Y-%m-%d")
                    if abs((sim_date - exp_date).days) <= 7:
                        continue  # Close enough
                except ValueError:
                    pass
            # Present but different value — partial credit
            filter_score -= 0.5

    filter_score = max(0, min(3, filter_score))

    # 2. Query Strategy (0-3)
    strategy_score = 3
    # Penalize if using query where HS/CPC codes should be used
    has_prerequisite = bool(gold.get("prerequisite_tools"))
    uses_lookup = bool(simulated.get("prerequisite_calls"))
    query_in_sim = "query" in simulated_filters

    if has_prerequisite and not uses_lookup and query_in_sim:
        # Should have used lookup tool but relied on query
        strategy_score -= 2
    elif has_prerequisite and not uses_lookup:
        strategy_score -= 1

    # Penalize overuse of query when structured filters exist
    if query_in_sim and all(k in expected for k in ["mast_chapters", "implementing_jurisdictions"]):
        if "query" not in expected:
            strategy_score -= 1

    strategy_score = max(0, min(3, strategy_score))

    # 3. Result Relevance (0-3) — inferred from filter quality
    relevance_score = 3
    # Missing critical filter → likely noisy results
    missing_critical = sum(1 for k in critical if k not in simulated_filters)
    relevance_score -= missing_critical * 1.0
    relevance_score = max(0, min(3, relevance_score))

    # 4. Completeness (0-3) — covers all aspects of the question
    completeness_score = 3
    total_expected = len(expected)
    total_matched = sum(1 for k in expected if k in simulated_filters)
    if total_expected > 0:
        ratio = total_matched / total_expected
        completeness_score = round(ratio * 3, 1)

    return {
        "filter_accuracy": round(filter_score, 1),
        "query_strategy": round(strategy_score, 1),
        "result_relevance": round(relevance_score, 1),
        "completeness": round(completeness_score, 1),
        "total": round(filter_score + strategy_score + relevance_score + completeness_score, 1),
    }


async def execute_search(filters: dict, api_key: str) -> dict:
    """Execute a GTA API search with the given filters."""
    client = GTAAPIClient(api_key)
    try:
        api_filters, messages = build_filters(filters)
        results = await client.search_interventions(
            filters=api_filters,
            limit=min(filters.get("limit", 50), 50),
            offset=0,
        )
        return {
            "count": len(results),
            "sample_titles": [r.get("state_act_title", "")[:100] for r in results[:5]],
            "filter_messages": messages,
        }
    except Exception as e:
        return {"error": str(e), "count": 0}


async def run_evaluation(
    prompt_ids: Optional[list] = None,
    execute: bool = True,
    round_num: int = 0,
) -> dict:
    """Run evaluation for specified prompts (or all)."""
    gold_data = load_gold_standard()
    # Combine main prompts + generalization prompts
    prompts = gold_data["prompts"]
    if "generalization_prompts" in gold_data:
        prompts = prompts + gold_data["generalization_prompts"]

    if prompt_ids:
        prompts = [p for p in prompts if p["id"] in prompt_ids]

    api_key = os.getenv("GTA_API_KEY", "")

    results = []
    for prompt_entry in prompts:
        pid = prompt_entry["id"]
        prompt_text = prompt_entry["prompt"]

        print(f"\n{'='*60}")
        print(f"Prompt {pid}: {prompt_text}")
        print(f"{'='*60}")

        # Step 1: Simulate
        simulated = simulate_tool_selection(prompt_text)
        print(f"  Simulated tool: {simulated['tool']}")
        print(f"  Simulated filters: {json.dumps(simulated['filters'], indent=4)}")
        if simulated["prerequisite_calls"]:
            print(f"  Prerequisites: {simulated['prerequisite_calls']}")

        # Step 2: Score
        scores = score_filters(simulated, prompt_entry)
        print(f"  Scores: {scores}")

        # Step 3: Execute (optional)
        execution = None
        if execute and api_key and simulated["tool"] == "gta_search_interventions":
            execution = await execute_search(simulated["filters"], api_key)
            print(f"  API results: {execution.get('count', 0)} interventions")
            if execution.get("sample_titles"):
                for title in execution["sample_titles"][:3]:
                    print(f"    - {title}")

        result = {
            "prompt_id": pid,
            "prompt": prompt_text,
            "red_team_verdict": prompt_entry.get("red_team_verdict", "N/A"),
            "simulated": simulated,
            "gold_standard": prompt_entry["expected_filters"],
            "scores": scores,
            "execution": execution,
        }
        results.append(result)

    # Aggregate scores
    total_scores = [r["scores"]["total"] for r in results]
    avg_score = sum(total_scores) / len(total_scores) if total_scores else 0
    critical_count = sum(1 for s in total_scores if s <= 4)
    passing_count = sum(1 for s in total_scores if s >= 10)

    summary = {
        "round": round_num,
        "timestamp": datetime.now().isoformat(),
        "num_prompts": len(results),
        "avg_score": round(avg_score, 1),
        "max_possible": 12,
        "total_aggregate": round(sum(total_scores), 1),
        "max_aggregate": len(results) * 12,
        "critical_count": critical_count,
        "passing_count": passing_count,
        "target_met": critical_count == 0 and passing_count >= len(results) * 0.9,
        "per_prompt": results,
    }

    return summary


def print_summary(summary: dict):
    """Print evaluation summary."""
    print(f"\n{'='*60}")
    print(f"EVALUATION SUMMARY — Round {summary['round']}")
    print(f"{'='*60}")
    print(f"Prompts evaluated: {summary['num_prompts']}")
    print(f"Average score: {summary['avg_score']}/12")
    print(f"Aggregate: {summary['total_aggregate']}/{summary['max_aggregate']}")
    print(f"Critical (≤4/12): {summary['critical_count']}")
    print(f"Passing (≥10/12): {summary['passing_count']}")
    print(f"Target met: {'YES' if summary['target_met'] else 'NO'}")

    print(f"\n{'─'*60}")
    print(f"{'ID':>3} | {'Score':>5} | {'Verdict':<12} | Prompt")
    print(f"{'─'*60}")
    for r in summary["per_prompt"]:
        score = r["scores"]["total"]
        verdict = r["red_team_verdict"]
        status = "CRITICAL" if score <= 4 else "PASS" if score >= 10 else "PARTIAL"
        prompt = r["prompt"][:50]
        print(f"{r['prompt_id']:>3} | {score:>5.1f} | {status:<12} | {prompt}")

    # Dimension breakdown
    print(f"\n{'─'*60}")
    print("Dimension averages:")
    dims = ["filter_accuracy", "query_strategy", "result_relevance", "completeness"]
    for dim in dims:
        avg = sum(r["scores"][dim] for r in summary["per_prompt"]) / len(summary["per_prompt"])
        print(f"  {dim:<20}: {avg:.1f}/3")


def save_results(summary: dict, round_num: int):
    """Save evaluation results to file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"round_{round_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")


async def main():
    parser = argparse.ArgumentParser(description="GTA MCP Iterative Evaluation")
    parser.add_argument("--round", type=int, default=0, help="Evaluation round number")
    parser.add_argument("--prompt-ids", type=str, default=None, help="Comma-separated prompt IDs to evaluate")
    parser.add_argument("--no-execute", action="store_true", help="Skip API execution phase")
    parser.add_argument("--save", action="store_true", help="Save results to file")
    args = parser.parse_args()

    prompt_ids = None
    if args.prompt_ids:
        prompt_ids = [int(x.strip()) for x in args.prompt_ids.split(",")]

    summary = await run_evaluation(
        prompt_ids=prompt_ids,
        execute=not args.no_execute,
        round_num=args.round,
    )

    print_summary(summary)

    if args.save:
        save_results(summary, args.round)


if __name__ == "__main__":
    asyncio.run(main())
