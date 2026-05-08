"""CLI front-end for scrapling-mnt — same cascade, no MCP transport.

Usage:
    python -m scrapling_mnt.cli scrape-url <url> [--strategy auto|static|stealth|js|pdf]
    python -m scrapling_mnt.cli scrape-batch <urls-file> [--strategy ...]
    python -m scrapling_mnt.cli status

Exit codes:
    0  success
    1  fetch failed (network, parse, or all strategies returned thin content)
    2  URL rejected by allowlist
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from . import fetcher
from .allowlist import URLRejected


def _print_result(result: fetcher.FetchResult, *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"# {result.url}", file=sys.stderr)
        print(f"# strategy: {result.strategy_used}  status: {result.status}  cache: {result.from_cache}",
              file=sys.stderr)
        if result.error:
            print(f"# error: {result.error}", file=sys.stderr)
        print(result.content)


async def _cmd_scrape_url(args: argparse.Namespace) -> int:
    try:
        result = await fetcher.scrape_url(
            args.url,
            strategy=args.strategy,
            timeout=args.timeout,
            use_cache=not args.no_cache,
        )
    except URLRejected as exc:
        print(f"URL rejected: {exc}", file=sys.stderr)
        return 2
    _print_result(result, json_output=args.json)
    if not result.content and result.error:
        return 1
    return 0


async def _cmd_scrape_batch(args: argparse.Namespace) -> int:
    urls = [
        line.strip()
        for line in Path(args.urls_file).read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    failures = 0
    for url in urls:
        try:
            result = await fetcher.scrape_url(
                url, strategy=args.strategy, timeout=args.timeout,
                use_cache=not args.no_cache,
            )
        except URLRejected as exc:
            print(json.dumps({"url": url, "error": f"rejected: {exc}"}))
            failures += 1
            continue
        if not result.content:
            failures += 1
        print(json.dumps(result.to_dict()))
    print(f"# {len(urls) - failures}/{len(urls)} ok", file=sys.stderr)
    return 0 if failures == 0 else 1


def _cmd_status(_args: argparse.Namespace) -> int:
    print(json.dumps(fetcher.status_snapshot(), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scrapling-mnt")
    sub = p.add_subparsers(dest="cmd", required=True)

    su = sub.add_parser("scrape-url", help="Fetch a single URL")
    su.add_argument("url")
    su.add_argument("--strategy", default="auto",
                    choices=["auto", "static", "stealth", "js", "pdf"])
    su.add_argument("--timeout", type=int, default=30)
    su.add_argument("--no-cache", action="store_true")
    su.add_argument("--json", action="store_true",
                    help="Emit full FetchResult as JSON instead of body to stdout")
    su.set_defaults(func=_cmd_scrape_url, is_async=True)

    sb = sub.add_parser("scrape-batch", help="Fetch URLs listed in a file (one per line)")
    sb.add_argument("urls_file")
    sb.add_argument("--strategy", default="auto",
                    choices=["auto", "static", "stealth", "js", "pdf"])
    sb.add_argument("--timeout", type=int, default=30)
    sb.add_argument("--no-cache", action="store_true")
    sb.set_defaults(func=_cmd_scrape_batch, is_async=True)

    st = sub.add_parser("status", help="Print server status snapshot")
    st.set_defaults(func=_cmd_status, is_async=False)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "is_async", False):
        return asyncio.run(args.func(args))
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
