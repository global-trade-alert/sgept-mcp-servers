"""JSON lines audit log with correlation IDs."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLog:
    """Append-only JSON lines audit log."""

    def __init__(self, audit_dir: str | Path | None = None):
        if audit_dir is None:
            audit_dir = os.environ.get(
                "METIS_AUDIT_DIR", os.path.expanduser("~/.metis/audit")
            )
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self.audit_dir / "metis-audit.jsonl"

    def log(
        self,
        event: str,
        correlation_id: str,
        instance_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Append an audit event."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
            "instance_id": instance_id,
            "event": event,
            "details": details or {},
        }
        with open(self._log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        """Read all audit entries (for testing)."""
        if not self._log_path.exists():
            return []
        entries = []
        with open(self._log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def clear(self) -> None:
        """Clear the audit log (for testing)."""
        if self._log_path.exists():
            self._log_path.unlink()
