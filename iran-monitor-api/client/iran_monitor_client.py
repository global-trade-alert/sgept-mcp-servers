"""Minimal Python client for the Iran Monitor Inference API.

Usage:

    from iran_monitor_client import Client

    client = Client(
        api_key=os.environ["IRAN_MONITOR_API_KEY"],
        base_url="https://api.iran-monitor.sgept.org",
    )

    query = client.submit(
        scenario="Iran launches a cyber attack on German critical infrastructure...",
        horizon="30d",
        tier="premium",
        deliver_to="risk-desk@your-fund.com",  # optional — email on completion
    )

    # Synchronous wait (polls every 30s)
    result = client.wait(query.query_id, timeout_seconds=3600)

    print(f"P = {result.p_point:.3f} ({result.p_interval[0]:.3f}-{result.p_interval[1]:.3f})")
    print(f"Major disagreements: {len(result.major_disagreements)}")
    for ev in result.high_elasticity_events:
        print(f"  - {ev.shift_direction} {ev.magnitude_pp}: {ev.event}")

    # Verify signed audit before trusting the number
    assert client.verify_audit(result)

Single-file dependency: stdlib + httpx + pynacl. Drop into your project or
publish as `iran-monitor-client` on PyPI from here.
"""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

import httpx
from nacl import signing
from nacl.encoding import RawEncoder


__version__ = "0.1.0"

Tier = Literal["standard", "premium"]
Horizon = Literal["7d", "14d", "30d", "60d", "90d"]


# ── Result shapes (mirror the server's Pydantic models, but as dataclasses
#    so the client has no Pydantic dependency) ─────────────────────────────


@dataclass
class PerspectiveOutput:
    name: str
    p_point: float
    p_interval: tuple[float, float] | None
    key_reasoning: str
    evidence_urls: list[str]
    divergence_from_consensus_pp: float | None


@dataclass
class MajorDisagreement:
    topic: str
    spread_pp: float
    high_side: list[str]
    low_side: list[str]
    narrative: str


@dataclass
class HighElasticityEvent:
    event: str
    shift_direction: str  # "up" | "down"
    magnitude_pp: str
    monitor: str


@dataclass
class QueryResult:
    query_id: UUID
    status: str
    partial: bool
    failed_perspectives: list[str]
    p_point: float
    p_interval: tuple[float, float]
    divergence_flag: bool
    consensus_summary: str
    perspectives: list[PerspectiveOutput]
    major_disagreements: list[MajorDisagreement]
    high_elasticity_events: list[HighElasticityEvent]
    briefing_markdown: str
    audit_record: dict
    audit_signature: str

    @classmethod
    def from_response(cls, data: dict) -> "QueryResult":
        r = data["result"]
        return cls(
            query_id=UUID(data["query_id"]),
            status=data["status"],
            partial=data.get("partial", False),
            failed_perspectives=data.get("failed_perspectives", []),
            p_point=r["p_point"],
            p_interval=tuple(r["p_interval"]),
            divergence_flag=r["divergence_flag"],
            consensus_summary=r["consensus_summary"],
            perspectives=[
                PerspectiveOutput(
                    name=p["name"],
                    p_point=p["p_point"],
                    p_interval=tuple(p["p_interval"]) if p.get("p_interval") else None,
                    key_reasoning=p["key_reasoning"],
                    evidence_urls=p.get("evidence_urls", []),
                    divergence_from_consensus_pp=p.get("divergence_from_consensus_pp"),
                )
                for p in r.get("perspectives", [])
            ],
            major_disagreements=[
                MajorDisagreement(**d) for d in r.get("major_disagreements", [])
            ],
            high_elasticity_events=[
                HighElasticityEvent(**e) for e in r.get("high_elasticity_events", [])
            ],
            briefing_markdown=r.get("briefing_markdown", ""),
            audit_record=data["audit_record"],
            audit_signature=data["audit_signature"],
        )


@dataclass
class PendingQuery:
    query_id: UUID
    status: str
    tier: Tier
    submitted_at_utc: str
    estimated_completion_utc: str


# ── Errors ────────────────────────────────────────────────────────────────


class IranMonitorError(Exception):
    """Base class for SDK errors."""


class HTTPError(IranMonitorError):
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"HTTP {status_code}: {payload.get('error')}: {payload.get('message')}")


class QueryFailedError(IranMonitorError):
    def __init__(self, payload: dict):
        self.payload = payload
        super().__init__(
            f"query failed: {payload.get('failed_perspectives')}; "
            f"audit available at audit_record."
        )


class QueryTimeoutError(IranMonitorError):
    pass


class SignatureVerificationError(IranMonitorError):
    pass


# ── Client ────────────────────────────────────────────────────────────────


class Client:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.iran-monitor.sgept.org",
        timeout: float = 60.0,
    ):
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        self._verify_key: signing.VerifyKey | None = None

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    # ── Endpoints ─────────────────────────────────────────────────────────

    def submit(
        self,
        scenario: str,
        horizon: Horizon = "30d",
        tier: Tier = "standard",
        perspectives: list[str] | None = None,
        deliver_to: str | None = None,
    ) -> PendingQuery:
        """POST /v1/queries → returns PendingQuery with query_id."""
        body: dict[str, Any] = {
            "scenario": scenario,
            "horizon": horizon,
            "tier": tier,
        }
        if perspectives:
            body["perspectives"] = perspectives
        if deliver_to:
            body["deliver_to"] = deliver_to
        r = self._http.post("/v1/queries", json=body)
        if r.status_code != 202:
            self._raise_http(r)
        data = r.json()
        return PendingQuery(
            query_id=UUID(data["query_id"]),
            status=data["status"],
            tier=data["tier"],
            submitted_at_utc=data["submitted_at_utc"],
            estimated_completion_utc=data["estimated_completion_utc"],
        )

    def get(self, query_id: UUID | str) -> dict:
        """GET /v1/queries/{id} → raw response dict (status-shaped)."""
        r = self._http.get(f"/v1/queries/{query_id}")
        if r.status_code not in (200, 503):
            self._raise_http(r)
        return r.json()

    def wait(
        self,
        query_id: UUID | str,
        poll_seconds: int = 30,
        timeout_seconds: int = 3600,
    ) -> QueryResult:
        """Poll until completed | partial | failed. Returns QueryResult."""
        deadline = time.monotonic() + timeout_seconds
        while True:
            data = self.get(query_id)
            status = data.get("status")
            if status in ("completed", "partial"):
                return QueryResult.from_response(data)
            if status == "failed":
                raise QueryFailedError(data)
            if time.monotonic() > deadline:
                raise QueryTimeoutError(
                    f"query {query_id} did not complete within {timeout_seconds}s "
                    f"(last status: {status})"
                )
            time.sleep(poll_seconds)

    # ── Signature verification ───────────────────────────────────────────

    @property
    def public_key(self) -> signing.VerifyKey:
        """Fetch /.well-known/iran-monitor-signing-key.pub once and cache."""
        if self._verify_key is None:
            r = self._http.get("/.well-known/iran-monitor-signing-key.pub")
            if r.status_code != 200:
                self._raise_http(r)
            self._verify_key = signing.VerifyKey(r.content, encoder=RawEncoder)
        return self._verify_key

    def verify_audit(self, result: QueryResult) -> bool:
        """Verify the Ed25519 signature over the audit record."""
        msg = self._canonicalize(result.audit_record)
        try:
            self.public_key.verify(msg, base64.b64decode(result.audit_signature))
            return True
        except Exception:
            return False

    # ── Internals ─────────────────────────────────────────────────────────

    @staticmethod
    def _canonicalize(obj: dict) -> bytes:
        """Matches the server's canonical JSON: sorted keys, no whitespace, UTF-8."""
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )

    @staticmethod
    def _raise_http(r: httpx.Response) -> None:
        try:
            payload = r.json()
        except Exception:
            payload = {"error": "non-json-response", "message": r.text[:300]}
        raise HTTPError(r.status_code, payload)
