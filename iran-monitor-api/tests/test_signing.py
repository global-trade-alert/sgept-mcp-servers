"""Ed25519 signing round-trip + canonicalization determinism."""

from __future__ import annotations

import base64

from iran_monitor_api.signing import (
    canonicalize,
    generate_keypair,
    sign_audit_record,
    verify_audit_record,
    write_keys,
)
from iran_monitor_api.config import get_settings


def test_canonicalize_is_deterministic_under_key_reordering():
    a = {"b": 1, "a": [3, 1, 2], "c": {"y": 1, "x": 2}}
    b = {"c": {"x": 2, "y": 1}, "a": [3, 1, 2], "b": 1}
    assert canonicalize(a) == canonicalize(b)


def test_canonicalize_preserves_array_order():
    a = {"items": [3, 1, 2]}
    b = {"items": [1, 2, 3]}
    assert canonicalize(a) != canonicalize(b)


def test_sign_and_verify_roundtrip(tmp_path):
    settings = get_settings()
    priv, pub = generate_keypair()
    write_keys(
        priv, pub,
        private_path=settings.signing_key_path,
        public_path=settings.signing_pub_key_path,
    )

    audit = {
        "query_id": "00000000-0000-0000-0000-000000000001",
        "scenario_text": "A scenario about Iran cyber capabilities",
        "horizon_days": 30,
        "tier": "premium",
        "intelligence_base_hash": "sha256:" + "a" * 64,
        "query_delta_hash": "sha256:" + "b" * 64,
        "perspectives_invoked": ["tetlock-forecaster", "schelling-bargaining"],
        "perspectives_completed": ["tetlock-forecaster", "schelling-bargaining"],
        "aggregation_method": "weighted_uniform_average_v1",
        "result_summary": {"p_point": 0.18, "divergence_flag": False},
        "evidence_urls": ["https://example.gov/release"],
        "started_at_utc": "2026-05-12T12:00:00+00:00",
        "runtime_seconds": 1400,
        "version": "1.0",
    }
    sig = sign_audit_record(audit)
    assert isinstance(sig, str) and len(base64.b64decode(sig)) == 64
    assert verify_audit_record(audit, sig) is True


def test_verify_fails_on_tampered_payload(tmp_path):
    settings = get_settings()
    priv, pub = generate_keypair()
    write_keys(
        priv, pub,
        private_path=settings.signing_key_path,
        public_path=settings.signing_pub_key_path,
    )

    audit = {"k": "v", "n": 1}
    sig = sign_audit_record(audit)
    audit_tampered = {**audit, "n": 2}
    assert verify_audit_record(audit_tampered, sig) is False
