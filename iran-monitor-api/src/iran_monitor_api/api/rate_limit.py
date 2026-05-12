"""Per-org sliding-window rate limit.

Backed by rate_limit_events in SQLite. Rebuilds correctly after worker restart
(events persist). Cheap enough at expected pilot scale (≤10 orgs × ≤40 req/hr).
"""

from __future__ import annotations

from datetime import timedelta

from .. import db
from ..config import get_settings
from ..errors import APIError, ErrorCode
from ..models import Tier, utc_now


def check_and_record(org_id: str, tier: Tier) -> None:
    settings = get_settings()
    now = utc_now()
    window_start = (now - timedelta(hours=1)).isoformat()

    cap = {
        Tier.STANDARD: settings.rate_limit_standard_per_hr,
        Tier.PREMIUM: settings.rate_limit_premium_per_hr,
    }[tier]

    count = db.count_rate_limit_events(org_id, tier, window_start)
    if count >= cap:
        retry_after = 3600  # crude — could compute time-to-oldest-event-aging-out
        raise APIError(
            ErrorCode.RATE_LIMITED,
            f"rate limit reached: {cap} {tier.value} queries per hour",
            retry_after=retry_after,
        )

    db.record_rate_limit_event(org_id, tier, now)


def prune_old(older_than_hours: int = 24) -> int:
    older_than = (utc_now() - timedelta(hours=older_than_hours)).isoformat()
    return db.prune_rate_limit_events(older_than)
