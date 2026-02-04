"""CLI interface for gta_mnt - enables headless review via Claude Code."""

import asyncio
import json
import os
import sys
from pathlib import Path

from .auth import JWTAuthManager
from .api import GTAAPIClient
from .source_fetcher import SourceFetcher
from .storage import ReviewStorage


async def fetch_measure_and_source(state_act_id: int) -> dict:
    """Fetch measure details and source document for review.

    Returns structured data for Claude to analyze.
    """
    # Initialize auth
    email = os.getenv("GTA_AUTH_EMAIL")
    password = os.getenv("GTA_AUTH_PASSWORD")

    if not email or not password:
        return {
            "error": "Missing credentials",
            "message": "Set GTA_AUTH_EMAIL and GTA_AUTH_PASSWORD environment variables"
        }

    auth = JWTAuthManager(email=email, password=password)
    storage = ReviewStorage()
    api = GTAAPIClient(auth, storage)
    source_fetcher = SourceFetcher(auth, storage)

    result = {
        "state_act_id": state_act_id,
        "measure": None,
        "source": None,
        "errors": []
    }

    try:
        # Fetch measure details
        print(f"Fetching measure {state_act_id}...", file=sys.stderr)
        measure = await api.get_measure(state_act_id)
        result["measure"] = measure

        # Fetch source document
        print(f"Fetching source document...", file=sys.stderr)
        source = await source_fetcher.get_source(state_act_id)
        result["source"] = source

    except Exception as e:
        result["errors"].append(str(e))
    finally:
        await api.close()
        await source_fetcher.close()

    return result


async def post_comment(state_act_id: int, comment_text: str) -> dict:
    """Post a comment to a measure."""
    email = os.getenv("GTA_AUTH_EMAIL")
    password = os.getenv("GTA_AUTH_PASSWORD")

    if not email or not password:
        return {"error": "Missing credentials"}

    auth = JWTAuthManager(email=email, password=password)
    api = GTAAPIClient(auth)

    try:
        result = await api.add_comment(state_act_id, comment_text)
        return result
    finally:
        await api.close()


async def tag_framework(state_act_id: int) -> dict:
    """Tag measure with sancho-claudino-review framework."""
    email = os.getenv("GTA_AUTH_EMAIL")
    password = os.getenv("GTA_AUTH_PASSWORD")

    if not email or not password:
        return {"error": "Missing credentials"}

    auth = JWTAuthManager(email=email, password=password)
    api = GTAAPIClient(auth)

    try:
        result = await api.add_framework(state_act_id, "sancho claudino review")
        return result
    finally:
        await api.close()


async def set_status(state_act_id: int, status_id: int) -> dict:
    """Set measure status."""
    email = os.getenv("GTA_AUTH_EMAIL")
    password = os.getenv("GTA_AUTH_PASSWORD")

    if not email or not password:
        return {"error": "Missing credentials"}

    auth = JWTAuthManager(email=email, password=password)
    api = GTAAPIClient(auth)

    try:
        result = await api.set_status(state_act_id, status_id)
        return result
    finally:
        await api.close()


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: python -m gta_mnt.cli <command> <state_act_id> [args...]")
        print("")
        print("Commands:")
        print("  fetch <id>              Fetch measure and source for review")
        print("  comment <id> <text>     Post a comment")
        print("  tag <id>                Tag with sancho-claudino-review framework")
        print("  status <id> <status_id> Set measure status")
        sys.exit(1)

    command = sys.argv[1]
    state_act_id = int(sys.argv[2])

    if command == "fetch":
        result = asyncio.run(fetch_measure_and_source(state_act_id))
        print(json.dumps(result, indent=2, default=str))

    elif command == "comment":
        if len(sys.argv) < 4:
            print("Usage: python -m gta_mnt.cli comment <id> <text>")
            sys.exit(1)
        comment_text = sys.argv[3]
        result = asyncio.run(post_comment(state_act_id, comment_text))
        print(json.dumps(result, indent=2, default=str))

    elif command == "tag":
        result = asyncio.run(tag_framework(state_act_id))
        print(json.dumps(result, indent=2, default=str))

    elif command == "status":
        if len(sys.argv) < 4:
            print("Usage: python -m gta_mnt.cli status <id> <status_id>")
            sys.exit(1)
        status_id = int(sys.argv[3])
        result = asyncio.run(set_status(state_act_id, status_id))
        print(json.dumps(result, indent=2, default=str))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
