"""Constants for dpa_mnt server.

Two distinct automated users operate in this server:

- **Buzessa Claudini** (ID 9902): REVIEWER. Authors review comments, sets review
  status, tags reviewed interventions. Used by quality review tools.
  NEVER used for entry creation.

- **Buzetta Claudini** (ID 9903): AUTHOR. Creates new events, interventions,
  and all associated data (sources, relations, etc.).
  NEVER used for review operations.

This separation is a hard constraint. Mixing the two corrupts the audit trail —
a reviewer must never appear as the author of the entry they might later review.
"""

import os
from pathlib import Path

# Buzessa Claudini — REVIEWER only (comments, status changes, issue tags)
BUZESSA_REVIEWER_ID = 9902
SANCHO_USER_ID = BUZESSA_REVIEWER_ID  # Backwards compat for existing review tools

# Buzetta Claudini — AUTHOR only (entry creation: events, interventions, relationships)
BUZETTA_AUTHOR_ID = 9903

# Issue ID for "BC review" in lux_issue_list
# Applied to the INTERVENTION (not the event) when at least one event has been reviewed.
# This replaces the framework tag mechanism (framework ID 496 is deprecated for new reviews).
BC_REVIEW_ISSUE_ID = 83

# Framework ID — DEPRECATED for new reviews; kept for backwards compat / checking old reviews
DPA_FRAMEWORK_ID = 496

# User display names (for audit trail messages)
REVIEWER_NAME = "Buzessa Claudini"
AUTHOR_NAME = "Buzetta Claudini"

# Valid DPA event status IDs (lux_event_status_list).
# Source: evidence from dpa_mnt.api.py queries (status_id=1,2,7 referenced) and
# server.py SetStatusInput docstring (status_id=3,4,5 documented as review outcomes).
# Any value outside this set is rejected by the SetStatusInput validator.
VALID_STATUS_IDS = {1, 2, 3, 4, 5, 7}

# Human-readable names for the valid status set (used in validator error messages).
STATUS_ID_NAMES = {
    1: "In Progress",
    2: "Step 1 Review (AT)",
    3: "Publishable (PASS)",
    4: "Concern (CONDITIONAL / ESCALATION)",
    5: "Under Revision (FAIL)",
    7: "Published",
}

# Review artifact storage path. Each intervention gets a folder with per-event
# source files, comments, and review logs. Override per environment:
#   export DPA_MNT_REVIEW_STORAGE_PATH=/path/to/bc-reviews
# Production deployments should point this at the persistent volume mounted by
# the enclosing deployment unit (historically: /home/deploy/jf-private/...).
REVIEW_STORAGE_PATH = os.getenv(
    "DPA_MNT_REVIEW_STORAGE_PATH",
    str(Path.home() / ".dpa-mnt" / "bc-reviews"),
)
