"""Runtime config from env. Keep it small — defaults match local dev."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="IRAN_API_", env_file=".env", extra="ignore")

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path("data"))
    iran_monitor_repo: Path = Field(
        default_factory=lambda: Path.home()
        / "Documents/GitHub/jf-private/jf-thought/sgept-analytics/iran-monitor"
    )

    # Signing
    signing_key_path: Path = Field(default_factory=lambda: Path("keys/signing-key.bin"))
    signing_pub_key_path: Path = Field(default_factory=lambda: Path("keys/signing-key.pub"))

    # API
    host: str = "127.0.0.1"
    port: int = 8080

    # API keys: a dict of {api_key -> org_id} loaded from env IRAN_API_KEYS_JSON
    # In production this lands from SOPS-encrypted env.
    api_keys_json: str = '{"dev-key-local": "dev-org"}'

    # Rate limits (per org, per hour)
    rate_limit_standard_per_hr: int = 30
    rate_limit_premium_per_hr: int = 10

    # Latency budgets (seconds, p99 hard cutoff)
    standard_ceiling_seconds: int = 30 * 60
    premium_ceiling_seconds: int = 60 * 60

    # Cost budgets (USD) — soft target, enforced as token cap
    standard_token_budget: int = 600_000
    premium_token_budget: int = 1_500_000

    # Subagent invocation
    claude_bin: str = "claude"
    claude_model_default: str = "sonnet"
    subagent_timeout_seconds: int = 600

    # Premium GATHER bounds
    gather_max_queries: int = 20
    gather_max_fetches: int = 60

    # Quorum threshold (computed in models.quorum_required; this is a clamp)
    min_perspectives: int = 3

    # Data retention
    audit_retention_months: int = 24
    query_delta_retention_days: int = 90

    @property
    def db_path(self) -> Path:
        return self.base_dir / "queries.sqlite"

    @property
    def query_outputs_dir(self) -> Path:
        return self.base_dir / "query-outputs"

    @property
    def query_deltas_dir(self) -> Path:
        return self.base_dir / "query-deltas"

    @property
    def intel_base_hash_file(self) -> Path:
        return self.iran_monitor_repo / "data" / ".intel-base-hash"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.base_dir.mkdir(parents=True, exist_ok=True)
        _settings.query_outputs_dir.mkdir(parents=True, exist_ok=True)
        _settings.query_deltas_dir.mkdir(parents=True, exist_ok=True)
    return _settings


def reset_settings_for_tests() -> None:
    global _settings
    _settings = None
