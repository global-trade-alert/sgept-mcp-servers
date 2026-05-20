"""CLI front-end for scrapling-mnt — same tools as the MCP server, no MCP transport.

Usage:
    python -m scrapling_mnt.cli scrape-url <url> [--strategy auto|static|stealth|js|pdf]
    python -m scrapling_mnt.cli scrape-batch <urls-file> [--strategy ...]

Exit codes:
    0  success
    1  fetch failed (empty content or error from bastiat)
    2  configuration error (missing GTA_API_KEY)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from .bastiat_client import BastiatScraper


def _build_scraper() -> BastiatScraper | None:
    api_key = os.environ.get("GTA_API_KEY")
    if not api_key:
        print("GTA_API_KEY environment variable is required", file=sys.stderr)
        return None
    return BastiatScraper(
        api_key=api_key,
        base_url=os.environ.get("BASTIAT_BASE_URL") or None,
        default_profile=os.environ.get("BASTIAT_PROFILE", "mcp_thorough"),
        verify_tls=os.environ.get("BASTIAT_VERIFY_TLS", "true").lower() != "false",
    )


def _print_result(result: dict, *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"# {result.get('url')}", file=sys.stderr)
        print(
            f"# strategy: {result.get('strategy_used')}  "
            f"status: {result.get('status')}  "
            f"cache: {result.get('from_cache')}",
            file=sys.stderr,
        )
        if result.get("error"):
            print(f"# error: {result['error']}", file=sys.stderr)
        print(result.get("content", ""))


async def _cmd_scrape_url(args: argparse.Namespace) -> int:
    scraper = _build_scraper()
    if scraper is None:
        return 2
    results = await scraper.scrape(
        [args.url],
        strategy=args.strategy,
        timeout=args.timeout,
        max_wait_s=args.max_wait_s,
    )
    result = results[0]
    _print_result(result, json_output=args.json)
    if not result.get("content") and result.get("error"):
        return 1
    return 0


async def _cmd_scrape_batch(args: argparse.Namespace) -> int:
    scraper = _build_scraper()
    if scraper is None:
        return 2
    urls = [
        line.strip()
        for line in Path(args.urls_file).read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    results = await scraper.scrape(
        urls,
        strategy=args.strategy,
        timeout=args.timeout,
        max_wait_s=args.max_wait_s,
    )
    failures = 0
    for r in results:
        if not r.get("content"):
            failures += 1
        print(json.dumps(r))
    print(f"# {len(results) - failures}/{len(results)} ok", file=sys.stderr)
    return 0 if failures == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scrapling-mnt")
    sub = p.add_subparsers(dest="cmd", required=True)

    su = sub.add_parser("scrape-url", help="Fetch a single URL")
    su.add_argument("url")
    su.add_argument("--strategy", default="auto",
                    choices=["auto", "static", "stealth", "js", "pdf"])
    su.add_argument("--timeout", type=int, default=30)
    su.add_argument("--max-wait-s", type=int, default=600, dest="max_wait_s")
    su.add_argument("--json", action="store_true",
                    help="Emit full FetchResult as JSON instead of body to stdout")
    su.set_defaults(func=_cmd_scrape_url)

    sb = sub.add_parser("scrape-batch", help="Fetch URLs listed in a file (one per line)")
    sb.add_argument("urls_file")
    sb.add_argument("--strategy", default="auto",
                    choices=["auto", "static", "stealth", "js", "pdf"])
    sb.add_argument("--timeout", type=int, default=30)
    sb.add_argument("--max-wait-s", type=int, default=600, dest="max_wait_s")
    sb.set_defaults(func=_cmd_scrape_batch)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return asyncio.run(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
