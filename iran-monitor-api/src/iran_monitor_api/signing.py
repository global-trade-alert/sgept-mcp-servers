"""Ed25519 signing for audit records.

Key material lives in SOPS-encrypted env in production. For dev,
`iran-monitor-generate-key` writes a fresh keypair to keys/.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

from nacl import signing
from nacl.encoding import RawEncoder

from .config import get_settings


def canonicalize(obj: dict) -> bytes:
    """JCS-ish: sorted keys, no whitespace, UTF-8. Adequate for our schema."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def generate_keypair() -> tuple[bytes, bytes]:
    sk = signing.SigningKey.generate()
    return bytes(sk), bytes(sk.verify_key)


def write_keys(private_b: bytes, public_b: bytes, *, private_path: Path, public_path: Path) -> None:
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_bytes(private_b)
    private_path.chmod(0o600)
    public_path.write_bytes(public_b)
    public_path.chmod(0o644)


def load_signing_key(path: Path | None = None) -> signing.SigningKey:
    settings = get_settings()
    p = path or settings.signing_key_path
    if not p.exists():
        raise FileNotFoundError(
            f"signing key not found at {p}. Run `iran-monitor-generate-key` "
            f"or set IRAN_API_SIGNING_KEY_PATH."
        )
    return signing.SigningKey(p.read_bytes(), encoder=RawEncoder)


def load_verify_key(path: Path | None = None) -> signing.VerifyKey:
    settings = get_settings()
    p = path or settings.signing_pub_key_path
    return signing.VerifyKey(p.read_bytes(), encoder=RawEncoder)


def sign_audit_record(audit_dict: dict, *, key: signing.SigningKey | None = None) -> str:
    """Detached Ed25519 signature over canonical JSON. Returns base64."""
    sk = key or load_signing_key()
    msg = canonicalize(audit_dict)
    sig = sk.sign(msg).signature
    return base64.b64encode(sig).decode("ascii")


def verify_audit_record(
    audit_dict: dict, signature_b64: str, *, key: signing.VerifyKey | None = None
) -> bool:
    vk = key or load_verify_key()
    try:
        vk.verify(canonicalize(audit_dict), base64.b64decode(signature_b64))
        return True
    except Exception:
        return False


# ── CLI ───────────────────────────────────────────────────────────────────────


def generate_cli() -> None:
    settings = get_settings()
    if settings.signing_key_path.exists():
        print(f"REFUSING: {settings.signing_key_path} already exists.", file=sys.stderr)
        print("Delete it explicitly before regenerating.", file=sys.stderr)
        sys.exit(1)
    priv, pub = generate_keypair()
    write_keys(
        priv, pub,
        private_path=settings.signing_key_path,
        public_path=settings.signing_pub_key_path,
    )
    print(f"Wrote signing key to {settings.signing_key_path}")
    print(f"Wrote verify key to {settings.signing_pub_key_path}")
    print(f"Verify key (base64): {base64.b64encode(pub).decode()}")
