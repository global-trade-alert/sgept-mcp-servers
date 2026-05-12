"""SQLite schema + queue DAL.

Tables:
- queries           : the queue + audit storage
- rate_limit_events : sliding-window event log for per-org rate limiting

Concurrency model: Phase 1 worker is single-threaded; FastAPI is multi-process-safe
because SQLite WAL + transactions handle the small fan-in from /queries POST.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator
from uuid import UUID

from .config import get_settings
from .models import Status, Tier, utc_now


SCHEMA = """
CREATE TABLE IF NOT EXISTS queries (
    query_id TEXT PRIMARY KEY,
    org_id   TEXT NOT NULL,
    api_key  TEXT NOT NULL,
    scenario TEXT NOT NULL,
    horizon  TEXT NOT NULL,
    tier     TEXT NOT NULL,
    perspectives_invoked TEXT NOT NULL,
    status   TEXT NOT NULL,
    intel_base_hash TEXT,
    query_delta_hash TEXT,
    result_json TEXT,
    audit_record_json TEXT,
    audit_signature TEXT,
    perspectives_completed TEXT,
    failed_perspectives TEXT,
    submitted_at_utc TEXT NOT NULL,
    started_at_utc   TEXT,
    completed_at_utc TEXT,
    error_code TEXT,
    runtime_seconds INTEGER
);

CREATE INDEX IF NOT EXISTS idx_queries_status ON queries(status);
CREATE INDEX IF NOT EXISTS idx_queries_org    ON queries(org_id, submitted_at_utc);

CREATE TABLE IF NOT EXISTS rate_limit_events (
    org_id TEXT NOT NULL,
    tier   TEXT NOT NULL,
    ts_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rl_org_tier_ts ON rate_limit_events(org_id, tier, ts_utc);
"""


_lock = threading.Lock()


@contextmanager
def get_conn(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    p = db_path or settings.db_path
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
    finally:
        conn.close()


def init_db(db_path: Path | None = None) -> None:
    with get_conn(db_path) as conn:
        conn.executescript(SCHEMA)


# ── Queue operations ──────────────────────────────────────────────────────────


def enqueue_query(
    *,
    query_id: UUID,
    org_id: str,
    api_key: str,
    scenario: str,
    horizon: str,
    tier: Tier,
    perspectives_invoked: list[str],
) -> None:
    with get_conn() as conn, _lock:
        conn.execute(
            """INSERT INTO queries (
                   query_id, org_id, api_key, scenario, horizon, tier,
                   perspectives_invoked, status, submitted_at_utc
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(query_id),
                org_id,
                api_key,
                scenario,
                horizon,
                tier.value,
                json.dumps(perspectives_invoked),
                Status.QUEUED.value,
                utc_now().isoformat(),
            ),
        )


def claim_next_query() -> dict | None:
    """Atomic claim of the next queued query. Returns row dict or None.

    The returned dict reflects the post-UPDATE state (status='running',
    started_at_utc set), so the caller sees what it just claimed.
    """
    with get_conn() as conn, _lock:
        cur = conn.execute(
            "SELECT * FROM queries WHERE status = ? ORDER BY submitted_at_utc LIMIT 1",
            (Status.QUEUED.value,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        now_iso = utc_now().isoformat()
        conn.execute(
            "UPDATE queries SET status = ?, started_at_utc = ? WHERE query_id = ?",
            (Status.RUNNING.value, now_iso, row["query_id"]),
        )
        d = dict(row)
        d["status"] = Status.RUNNING.value
        d["started_at_utc"] = now_iso
        return d


def mark_perspective_completed(query_id: UUID, perspective: str) -> None:
    """Append-style: read current list, append, write back. Lock protects."""
    with get_conn() as conn, _lock:
        cur = conn.execute(
            "SELECT perspectives_completed FROM queries WHERE query_id = ?",
            (str(query_id),),
        )
        row = cur.fetchone()
        if row is None:
            return
        completed = json.loads(row["perspectives_completed"] or "[]")
        if perspective not in completed:
            completed.append(perspective)
        conn.execute(
            "UPDATE queries SET perspectives_completed = ? WHERE query_id = ?",
            (json.dumps(completed), str(query_id)),
        )


def mark_perspective_failed(query_id: UUID, perspective: str) -> None:
    with get_conn() as conn, _lock:
        cur = conn.execute(
            "SELECT failed_perspectives FROM queries WHERE query_id = ?",
            (str(query_id),),
        )
        row = cur.fetchone()
        if row is None:
            return
        failed = json.loads(row["failed_perspectives"] or "[]")
        if perspective not in failed:
            failed.append(perspective)
        conn.execute(
            "UPDATE queries SET failed_perspectives = ? WHERE query_id = ?",
            (json.dumps(failed), str(query_id)),
        )


def complete_query(
    *,
    query_id: UUID,
    status: Status,
    intel_base_hash: str | None,
    query_delta_hash: str | None,
    result_json: str | None,
    audit_record_json: str,
    audit_signature: str,
    runtime_seconds: int,
    error_code: str | None = None,
) -> None:
    with get_conn() as conn, _lock:
        conn.execute(
            """UPDATE queries SET
                   status = ?,
                   intel_base_hash = ?,
                   query_delta_hash = ?,
                   result_json = ?,
                   audit_record_json = ?,
                   audit_signature = ?,
                   completed_at_utc = ?,
                   runtime_seconds = ?,
                   error_code = ?
               WHERE query_id = ?""",
            (
                status.value,
                intel_base_hash,
                query_delta_hash,
                result_json,
                audit_record_json,
                audit_signature,
                utc_now().isoformat(),
                runtime_seconds,
                error_code,
                str(query_id),
            ),
        )


def get_query(query_id: UUID) -> dict | None:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM queries WHERE query_id = ?", (str(query_id),))
        row = cur.fetchone()
        return dict(row) if row else None


def find_running_queries() -> list[dict]:
    """Used by the worker on startup for crash recovery."""
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM queries WHERE status = ?", (Status.RUNNING.value,))
        return [dict(r) for r in cur.fetchall()]


def reset_running_to_queued(query_id: UUID) -> None:
    with get_conn() as conn, _lock:
        conn.execute(
            "UPDATE queries SET status = ?, started_at_utc = NULL WHERE query_id = ? AND status = ?",
            (Status.QUEUED.value, str(query_id), Status.RUNNING.value),
        )


# ── Rate limits ───────────────────────────────────────────────────────────────


def record_rate_limit_event(org_id: str, tier: Tier, ts: datetime | None = None) -> None:
    ts = ts or utc_now()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO rate_limit_events (org_id, tier, ts_utc) VALUES (?, ?, ?)",
            (org_id, tier.value, ts.isoformat()),
        )


def count_rate_limit_events(org_id: str, tier: Tier, since_iso: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT COUNT(*) AS n FROM rate_limit_events WHERE org_id = ? AND tier = ? AND ts_utc >= ?",
            (org_id, tier.value, since_iso),
        )
        row = cur.fetchone()
        return int(row["n"]) if row else 0


def prune_rate_limit_events(older_than_iso: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM rate_limit_events WHERE ts_utc < ?", (older_than_iso,)
        )
        return cur.rowcount or 0
