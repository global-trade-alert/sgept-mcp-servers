"""Constants for dpa_mnt server.

Two distinct automated users operate in this server:

- **Buzessa Claudini** (ID 9902): REVIEWER. Authors review comments, sets review
  status, attaches review framework tags. Used by quality review tools.
  NEVER used for entry creation.

- **Buzetta Claudini** (ID 9903): AUTHOR. Creates new events, interventions,
  and all associated data (sources, relations, etc.).
  NEVER used for review operations.

This separation is a hard constraint. Mixing the two corrupts the audit trail —
a reviewer must never appear as the author of the entry they might later review.
"""

# Buzessa Claudini — REVIEWER only (comments, status changes, framework tags)
BUZESSA_REVIEWER_ID = 9902
SANCHO_USER_ID = BUZESSA_REVIEWER_ID  # Backwards compat for existing review tools

# Buzetta Claudini — AUTHOR only (entry creation: events, interventions, relationships)
BUZETTA_AUTHOR_ID = 9903

# Framework ID for "buzessa claudini dpa review" framework
# GTA uses 495 (sancho claudino); DPA uses 496 (buzessa claudini)
DPA_FRAMEWORK_ID = 496

# User display names (for audit trail messages)
REVIEWER_NAME = "Buzessa Claudini"
AUTHOR_NAME = "Buzetta Claudini"

# Review artifact storage path
# Each event gets a folder with source files, comments, and review log
REVIEW_STORAGE_PATH = "/Users/johannesfritz/Documents/GitHub/jf-private/jf-thought/sgept-monitoring/dpa/sc-reviews"
