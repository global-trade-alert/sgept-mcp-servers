"""Resource-loading utilities for gta-mnt MCP resources.

Resources live as markdown files under `resources/` at the project root and are
served to the MCP host under the `gta-mnt://` URI scheme.

Loaded content is cached per-process; the files are small enough that a single
read at first request is cheaper than dealing with reload invalidation.
"""

from pathlib import Path
from typing import Dict


_CACHE: Dict[str, str] = {}


def get_resources_dir() -> Path:
    """Locate the `resources/` directory.

    Supports two layouts:
    - Development: src/gta_mnt/resources_loader.py → <project root>/resources/
    - Installed (uv build): gta_mnt/resources_loader.py → gta_mnt/resources/ (sibling)
    """
    current_file = Path(__file__)

    installed = current_file.parent / "resources"
    if installed.is_dir():
        return installed

    dev = current_file.parent.parent.parent / "resources"
    return dev


def load_resource(name: str) -> str:
    """Return the content of `resources/<name>.md`.

    Raises FileNotFoundError if the file doesn't exist — that is a deployment
    bug, not a runtime condition to handle. Let it surface.
    """
    if name in _CACHE:
        return _CACHE[name]

    path = get_resources_dir() / f"{name}.md"
    text = path.read_text(encoding="utf-8")
    _CACHE[name] = text
    return text


# Stable list of MCP resources exposed under `gta-mnt://`. The key is the
# suffix the MCP host will request; the value is the markdown filename stem.
RESOURCE_MANIFEST: Dict[str, str] = {
    "review-criteria": "review_criteria",
    "status-id-decision-tree": "status_id_decision_tree",
    "comment-templates": "comment_templates",
    "framework-ids": "framework_ids",
    "source-extraction-notes": "source_extraction_notes",
}
