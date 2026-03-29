"""Constants for gta_mnt server.

Two distinct automated users operate in this server:

- **Sancho Claudino** (ID 9900): REVIEWER. Authors review comments, sets review
  status, attaches review framework tags. Used by quality review tools.
  NEVER used for entry creation.

- **Sancho Claudito** (ID 9901): AUTHOR. Creates new state acts, interventions,
  and all associated data (IJ, products, sectors, firms, sources, etc.).
  NEVER used for review operations.

This separation is a hard constraint. Mixing the two corrupts the audit trail —
a reviewer must never appear as the author of the entry they might later review.
"""

# Sancho Claudino — REVIEWER only (comments, status changes, framework tags)
SANCHO_REVIEWER_ID = 9900
SANCHO_USER_ID = SANCHO_REVIEWER_ID  # Backwards compat for existing review tools

# Sancho Claudito — AUTHOR only (entry creation: state acts, interventions, relationships)
SANCHO_AUTHOR_ID = 9901

# Framework ID for "sancho claudino review" framework
# This framework tracks which measures have been reviewed by Sancho Claudino
SANCHO_FRAMEWORK_ID = 495

# Framework ID for "sancho claudito reported" framework
# This framework tracks which measures were first-drafted by Sancho Claudito
SANCHO_CLAUDITO_FRAMEWORK_ID = 500

# Map framework names to IDs for dynamic lookup
FRAMEWORK_IDS = {
    "sancho claudino review": SANCHO_FRAMEWORK_ID,
    "sancho claudito reported": SANCHO_CLAUDITO_FRAMEWORK_ID,
}

# Review artifact storage path
# Each state act gets a folder with source files, comments, and review log
REVIEW_STORAGE_PATH = "/home/deploy/jf-private/jf-thought/sgept-monitoring/gta/sc-reviews"

# Lookup table mapping for gta_mnt_lookup tool
# Maps short names to (table_name, id_column, name_column)
LOOKUP_TABLES = {
    'jurisdiction': ('api_jurisdiction_list', 'jurisdiction_id', 'jurisdiction_name'),
    'product': ('api_product_list', 'product_id', 'product_description'),
    'sector': ('api_sector_list', 'sector_id', 'sector_name'),
    'rationale': ('api_rationale_list', 'rationale_id', 'rationale_name'),
    'unit': ('api_unit_list', 'id', 'name'),
    'firm': ('mtz_firm_log', 'firm_id', 'firm_name'),
    'intervention_type': ('api_intervention_type_list', 'intervention_type_id', 'intervention_type_name'),
    'mast_chapter': ('api_mast_chapter_list', 'chapter_id', 'chapter_name'),
    'mast_subchapter': ('api_mast_subchapter_list', 'subchapter_id', 'subchapter_name'),
    'evaluation': ('api_gta_evaluation_list', 'gta_evaluation_id', 'gta_evaluation_name'),
    'affected_flow': ('api_affected_flow_list', 'affected_flow_id', 'affected_flow_name'),
    'eligible_firm': ('api_eligible_firm_list', 'eligible_firm_id', 'eligible_firm_name'),
    'implementation_level': ('api_implementation_level_list', 'implementation_level_id', 'implementation_level_name'),
    'intervention_area': ('api_intervention_area_list', 'intervention_area_id', 'intervention_area_name'),
    'firm_role': ('mtz_firm_role', 'id', 'name'),
    'level_type': ('api_level_type_list', 'id', 'name'),
}
