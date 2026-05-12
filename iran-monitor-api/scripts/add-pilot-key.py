#!/usr/bin/env python3
"""Add (or revoke / list) pilot API keys for the Iran Monitor API.

Keys live in a JSON file at the path given by `IRAN_API_API_KEYS_FILE`
(default: keys/api-keys.json). On Metis production this file is decrypted
from SOPS into a tmpfs-mounted location before the service starts.

Usage:

    # Mint a new key for an org
    python scripts/add-pilot-key.py add acme-capital
    # Prints the new key — capture it; we do not store the plaintext anywhere
    # else than the keys file. Deliver it to the buyer out-of-band.

    # List existing keys (masked)
    python scripts/add-pilot-key.py list

    # Revoke a key
    python scripts/add-pilot-key.py revoke <api-key>
    python scripts/add-pilot-key.py revoke-org acme-capital

After every mutation, restart the api service:
    sudo systemctl restart iran-monitor-api iran-monitor-worker
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_KEYS_FILE = Path(os.environ.get("IRAN_API_API_KEYS_FILE", "keys/api-keys.json"))


def _load(p: Path) -> dict:
    if not p.exists():
        return {"keys": []}
    return json.loads(p.read_text())


def _save(p: Path, data: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True))
    tmp.replace(p)
    p.chmod(0o600)


def _mint_key() -> str:
    # 32 bytes urlsafe ≈ 43 chars. Prefix `imk-` for grep-ability.
    return "imk-" + secrets.token_urlsafe(32)


def _mask(k: str) -> str:
    return k[:8] + "…" + k[-4:] if len(k) > 16 else k


def cmd_add(args, data: dict) -> int:
    org_id = args.org_id.strip()
    if not org_id:
        print("ERROR: empty org_id", file=sys.stderr); return 2
    key = _mint_key()
    entry = {
        "key": key,
        "org_id": org_id,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "status": "active",
    }
    data["keys"].append(entry)
    _save(args.keys_file, data)
    print(f"Org:     {org_id}")
    print(f"Key:     {key}")
    print(f"Created: {entry['created_at']}")
    print()
    print("Deliver the key out-of-band (encrypted attachment / 1Password vault link).")
    print("Restart the service:  sudo systemctl restart iran-monitor-api iran-monitor-worker")
    return 0


def cmd_list(args, data: dict) -> int:
    if not data["keys"]:
        print("(no keys)")
        return 0
    print(f"{'org_id':24s}  {'status':8s}  {'key':52s}  created_at")
    print("-" * 110)
    for e in sorted(data["keys"], key=lambda x: x.get("created_at", "")):
        print(f"{e['org_id']:24s}  {e.get('status', 'active'):8s}  {_mask(e['key']):52s}  {e.get('created_at', '?')}")
    return 0


def cmd_revoke(args, data: dict) -> int:
    n = 0
    for e in data["keys"]:
        if e["key"] == args.key:
            e["status"] = "revoked"
            e["revoked_at"] = datetime.now(tz=timezone.utc).isoformat()
            n += 1
    if n == 0:
        print(f"no key matched {args.key[:12]}…", file=sys.stderr)
        return 1
    _save(args.keys_file, data)
    print(f"revoked {n} key(s)")
    print("Restart the service:  sudo systemctl restart iran-monitor-api iran-monitor-worker")
    return 0


def cmd_revoke_org(args, data: dict) -> int:
    n = 0
    for e in data["keys"]:
        if e["org_id"] == args.org_id and e.get("status") != "revoked":
            e["status"] = "revoked"
            e["revoked_at"] = datetime.now(tz=timezone.utc).isoformat()
            n += 1
    if n == 0:
        print(f"no active keys for org {args.org_id}", file=sys.stderr)
        return 1
    _save(args.keys_file, data)
    print(f"revoked {n} key(s) for org {args.org_id}")
    print("Restart the service:  sudo systemctl restart iran-monitor-api iran-monitor-worker")
    return 0


def cmd_export_env(args, data: dict) -> int:
    """Print IRAN_API_API_KEYS_JSON line for .env from the active keys."""
    active = {e["key"]: e["org_id"] for e in data["keys"] if e.get("status") == "active"}
    print("IRAN_API_API_KEYS_JSON=" + json.dumps(active))
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--keys-file", type=Path, default=DEFAULT_KEYS_FILE,
                   help=f"JSON file storing keys (default: {DEFAULT_KEYS_FILE})")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("add", help="mint a new key for an org")
    sp.add_argument("org_id")
    sp.set_defaults(func=cmd_add)

    sp = sub.add_parser("list", help="list keys (masked)")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("revoke", help="revoke a specific key by value")
    sp.add_argument("key")
    sp.set_defaults(func=cmd_revoke)

    sp = sub.add_parser("revoke-org", help="revoke all keys for an org")
    sp.add_argument("org_id")
    sp.set_defaults(func=cmd_revoke_org)

    sp = sub.add_parser("export-env", help="print the IRAN_API_API_KEYS_JSON env line")
    sp.set_defaults(func=cmd_export_env)

    args = p.parse_args()
    data = _load(args.keys_file)
    sys.exit(args.func(args, data))


if __name__ == "__main__":
    main()
