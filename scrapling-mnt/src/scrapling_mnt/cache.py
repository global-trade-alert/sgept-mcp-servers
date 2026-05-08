"""SHA-keyed disk cache for fetched pages.

Mirrors the convention already used by cc-os/scripts/fetch-source.py:
- {sha}.{ext}        body
- {sha}.meta.json    metadata (url, fetched_at, strategy, status, content_type)

Default cache root: ~/.cache/scrapling-mnt (override via SCRAPLING_CACHE_DIR).
30-day TTL by default (override via SCRAPLING_CACHE_TTL_DAYS).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


_DEFAULT_CACHE_DIR = Path.home() / ".cache" / "scrapling-mnt"
_DEFAULT_TTL_DAYS = 30


def cache_root() -> Path:
    root = Path(os.environ.get("SCRAPLING_CACHE_DIR", str(_DEFAULT_CACHE_DIR)))
    root.mkdir(parents=True, exist_ok=True)
    return root


def cache_ttl_seconds() -> int:
    days = int(os.environ.get("SCRAPLING_CACHE_TTL_DAYS", _DEFAULT_TTL_DAYS))
    return days * 86400


def url_sha(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]


@dataclass
class CacheMeta:
    url: str
    fetched_at: float  # unix epoch
    strategy: str  # static | stealth | js | pdf | ocr
    status: int  # http status or 200 for synthetic
    content_type: str
    body_path: str  # relative to cache_root


def read(url: str, ext: str = "md") -> Optional[tuple[str, CacheMeta]]:
    """Return (body, meta) if a fresh cache entry exists, else None."""
    sha = url_sha(url)
    body_path = cache_root() / f"{sha}.{ext}"
    meta_path = cache_root() / f"{sha}.meta.json"
    if not body_path.exists() or not meta_path.exists():
        return None
    try:
        meta_dict = json.loads(meta_path.read_text())
        meta = CacheMeta(**meta_dict)
    except (json.JSONDecodeError, TypeError):
        return None
    if time.time() - meta.fetched_at > cache_ttl_seconds():
        return None
    return body_path.read_text(errors="replace"), meta


def write(url: str, body: str, *, strategy: str, status: int,
          content_type: str, ext: str = "md") -> CacheMeta:
    sha = url_sha(url)
    body_path = cache_root() / f"{sha}.{ext}"
    meta_path = cache_root() / f"{sha}.meta.json"
    body_path.write_text(body)
    meta = CacheMeta(
        url=url,
        fetched_at=time.time(),
        strategy=strategy,
        status=status,
        content_type=content_type,
        body_path=body_path.name,
    )
    meta_path.write_text(json.dumps(asdict(meta), indent=2))
    return meta


def write_bytes(url: str, body: bytes, *, strategy: str, status: int,
                content_type: str, ext: str = "pdf") -> CacheMeta:
    sha = url_sha(url)
    body_path = cache_root() / f"{sha}.{ext}"
    meta_path = cache_root() / f"{sha}.meta.json"
    body_path.write_bytes(body)
    meta = CacheMeta(
        url=url,
        fetched_at=time.time(),
        strategy=strategy,
        status=status,
        content_type=content_type,
        body_path=body_path.name,
    )
    meta_path.write_text(json.dumps(asdict(meta), indent=2))
    return meta
