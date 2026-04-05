"""METIS Capability Registry — loader, FTS5 indexer, query engine, staffing recommender.

Standalone module. Can be integrated into the metis-mcp FastMCP server via
register_registry_tools(), or used directly as a library.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

import yaml

from metis_mcp.registry_models import CapabilityEntry, StaffingMatch, StaffingPlan

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"skill", "agent", "workflow"}

# Common English stopwords to strip from FTS5 queries.
# FTS5 with porter tokenizer handles some, but quoting tokens bypasses this.
_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "this", "that", "as", "are",
    "was", "be", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "i", "we", "you", "they",
    "he", "she", "my", "our", "your", "their", "its",
})


class CapabilityRegistry:
    """Load YAML capability definitions, index them with SQLite FTS5, and query."""

    def __init__(self, registry_dir: str, index_path: str | None = None):
        """
        Args:
            registry_dir: Path to the directory containing YAML registry files
                          (may have subdirectories like skills/, agents/, workflows/).
            index_path: Optional path for a persistent SQLite database.
                        If None, uses an in-memory database.
        """
        self.registry_dir = Path(registry_dir)
        self.index_path = index_path
        self._entries: dict[str, CapabilityEntry] = {}
        self._conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Scan registry_dir for *.yaml files, parse into CapabilityEntry models,
        and (re)build the FTS5 index."""
        self._entries.clear()
        yaml_files = sorted(self.registry_dir.rglob("*.yaml"))

        for path in yaml_files:
            if path.name.startswith("_"):
                continue  # skip schema/meta files like _schema.yaml
            try:
                with open(path) as f:
                    data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    logger.warning("Skipping %s: not a YAML mapping", path)
                    continue
                entry = CapabilityEntry(**data)
                if entry.id in self._entries:
                    logger.warning(
                        "Duplicate capability ID '%s' in %s — skipping",
                        entry.id,
                        path,
                    )
                    continue
                self._entries[entry.id] = entry
            except Exception as exc:
                logger.warning("Skipping %s: %s", path, exc)

        self._build_index()
        logger.info("Loaded %d capabilities from %s", len(self._entries), self.registry_dir)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def list(
        self,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> list[CapabilityEntry]:
        """List capabilities, optionally filtered by category and/or tags.

        Args:
            category: If set, only return entries matching this category.
            tags: If set, only return entries that have ALL of the given tags.
        """
        results = list(self._entries.values())

        if category is not None:
            results = [e for e in results if e.category == category]

        if tags:
            tag_set = set(tags)
            results = [e for e in results if tag_set.issubset(set(e.tags))]

        return sorted(results, key=lambda e: e.id)

    def get(self, capability_id: str) -> CapabilityEntry | None:
        """Get a single capability by ID."""
        return self._entries.get(capability_id)

    def search(self, query: str) -> list[CapabilityEntry]:
        """Full-text search using SQLite FTS5. Returns results ranked by relevance."""
        if self._conn is None:
            return []

        # Sanitize query for FTS5: strip stopwords, wrap each remaining token
        # in double quotes to avoid syntax errors, join with spaces (implicit AND).
        tokens = [t for t in query.strip().split() if t.lower() not in _STOPWORDS]
        if not tokens:
            return []
        fts_query = " ".join(f'"{t}"' for t in tokens)

        try:
            cursor = self._conn.execute(
                "SELECT id FROM capabilities WHERE capabilities MATCH ? ORDER BY rank",
                (fts_query,),
            )
            ids = [row[0] for row in cursor.fetchall()]
            return [self._entries[cid] for cid in ids if cid in self._entries]
        except sqlite3.OperationalError as exc:
            logger.warning("FTS5 search failed for query '%s': %s", query, exc)
            return []

    # ------------------------------------------------------------------
    # Staffing recommender
    # ------------------------------------------------------------------

    def staff(self, requirements: list[str]) -> StaffingPlan:
        """Given requirement descriptions, propose a staffing plan.

        For each requirement, search the registry for the best-matching capability.
        Returns matched capabilities and identified gaps (requirements with no match).
        """
        matched: list[StaffingMatch] = []
        gaps: list[str] = []

        for req in requirements:
            results = self.search(req)
            if results:
                best = results[0]
                matched.append(
                    StaffingMatch(
                        capability_id=best.id,
                        capability_name=best.name,
                        match_reason=f"FTS5 top match for '{req}': {best.description[:120]}",
                    )
                )
            else:
                # Fallback: try substring matching on name/description
                fallback = self._substring_match(req)
                if fallback:
                    matched.append(
                        StaffingMatch(
                            capability_id=fallback.id,
                            capability_name=fallback.name,
                            match_reason=f"Substring match for '{req}': {fallback.description[:120]}",
                        )
                    )
                else:
                    gaps.append(req)

        return StaffingPlan(matched=matched, gaps=gaps)

    # ------------------------------------------------------------------
    # FTS5 index management
    # ------------------------------------------------------------------

    def _build_index(self) -> None:
        """Create or rebuild the SQLite FTS5 index from loaded entries."""
        if self._conn is not None:
            self._conn.close()

        if self.index_path:
            self._conn = sqlite3.connect(self.index_path)
        else:
            self._conn = sqlite3.connect(":memory:")

        self._conn.execute("DROP TABLE IF EXISTS capabilities")
        self._conn.execute(
            """CREATE VIRTUAL TABLE capabilities USING fts5(
                id,
                name,
                description,
                tags,
                category,
                tokenize='porter unicode61'
            )"""
        )

        for entry in self._entries.values():
            self._conn.execute(
                "INSERT INTO capabilities (id, name, description, tags, category) VALUES (?, ?, ?, ?, ?)",
                (
                    entry.id,
                    entry.name,
                    entry.description,
                    " ".join(entry.tags),
                    entry.category,
                ),
            )

        self._conn.commit()

    def _substring_match(self, query: str) -> CapabilityEntry | None:
        """Simple substring fallback when FTS5 returns nothing."""
        query_lower = query.lower()
        for entry in self._entries.values():
            searchable = f"{entry.name} {entry.description} {' '.join(entry.tags)}".lower()
            if query_lower in searchable:
                return entry
        return None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the SQLite connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __del__(self) -> None:
        self.close()


# ======================================================================
# MCP tool registration (called from server.py)
# ======================================================================


def register_registry_tools(mcp_server, registry: CapabilityRegistry) -> None:
    """Register all registry MCP tools on the given FastMCP server.

    Called from server.py after engine tools are registered.
    """

    @mcp_server.tool(name="metis_registry_list")
    async def registry_list(category: str = None, tags: str = None) -> str:
        """List registered capabilities, optionally filtered by category and/or tags.

        Args:
            category: Filter by category (skill, agent, workflow).
            tags: Comma-separated list of tags to filter by (AND logic).
        """
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        entries = registry.list(category=category, tags=tag_list)
        return json.dumps(
            [{"id": e.id, "category": e.category, "name": e.name, "description": e.description} for e in entries],
            indent=2,
        )

    @mcp_server.tool(name="metis_registry_get")
    async def registry_get(capability_id: str) -> str:
        """Get full details of a single capability by its ID."""
        entry = registry.get(capability_id)
        if entry is None:
            return json.dumps({"error": f"Capability '{capability_id}' not found"})
        return entry.model_dump_json(indent=2)

    @mcp_server.tool(name="metis_registry_search")
    async def registry_search(query: str) -> str:
        """Full-text search across all registered capabilities."""
        entries = registry.search(query)
        return json.dumps(
            [{"id": e.id, "category": e.category, "name": e.name, "description": e.description} for e in entries],
            indent=2,
        )

    @mcp_server.tool(name="metis_registry_staff")
    async def registry_staff(requirements: str) -> str:
        """Propose a staffing plan for a set of requirements.

        Args:
            requirements: JSON array of requirement description strings.
        """
        try:
            req_list = json.loads(requirements)
        except json.JSONDecodeError:
            return json.dumps({"error": "requirements must be a JSON array of strings"})

        if not isinstance(req_list, list):
            return json.dumps({"error": "requirements must be a JSON array of strings"})

        plan = registry.staff(req_list)
        return plan.model_dump_json(indent=2)
