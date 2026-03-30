"""GTA API client for gta_mnt server - Direct Database Access.

Refactored to use direct MySQL connections instead of REST API endpoints.
Also includes BastiatAPIClient for AI-powered HS code guessing.
"""

import os
import re
import sys
from typing import Optional
from datetime import datetime, UTC

import httpx
import pymysql
import pymysql.cursors


def _slugify(text: str, max_length: int = 490) -> str:
    """Generate a URL-safe slug from text, matching Django AutoSlugField behaviour."""
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug[:max_length]

from .constants import SANCHO_USER_ID, SANCHO_AUTHOR_ID, SANCHO_FRAMEWORK_ID, FRAMEWORK_IDS, LOOKUP_TABLES
from .storage import ReviewStorage


class BastiatAPIClient:
    """Client for Bastiat API (AI-powered HS Code Guesser).

    Uses semantic understanding to match natural language product descriptions
    to HS codes, unlike gta_mnt_lookup which only does substring matching.
    """

    DEFAULT_BASE_URL = "https://bastiat-api.globaltradealert.org"

    def __init__(self, api_key: str, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.headers = {
            "Authorization": f"APIKey {api_key}",
            "Content-Type": "application/json",
        }

    async def guess_hs_codes(
        self,
        article_text: str,
        target_hs_levels: list[int] | None = None,
        initial_hs_codes: list[str] | None = None,
    ) -> dict:
        """Call Bastiat API to guess HS codes from product description text.

        Args:
            article_text: Natural language description of products/goods.
            target_hs_levels: HS digit levels to return (e.g. [2, 4, 6]).
            initial_hs_codes: Optional hint codes to guide the search.

        Returns:
            API response dict with guessed HS codes.
        """
        payload = {"article_text": article_text}
        if target_hs_levels:
            payload["target_hs_levels"] = target_hs_levels
        if initial_hs_codes:
            payload["initial_hs_codes"] = initial_hs_codes

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.base_url}/bastiat/howard/guess-hs-codes/",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()


class GTADatabaseClient:
    """Client for GTA database operations via direct MySQL access.

    Handles authenticated database connections for:
    - Measure queries (Step 1 queue)
    - Comment creation
    - Status updates
    - Framework tagging
    """

    def __init__(self, storage: Optional[ReviewStorage] = None):
        """Initialize with database credentials from environment."""
        self.host = os.getenv('GTA_DB_HOST', 'gtaapi.cp7esvs8xwum.eu-west-1.rds.amazonaws.com')
        self.database = os.getenv('GTA_DB_NAME', 'gtaapi')
        self.port = int(os.getenv('GTA_DB_PORT', '3306'))

        # Use write credentials for the review workflow
        self.user = os.getenv('GTA_DB_USER_WRITE', os.getenv('GTA_DB_USER', 'gtaapi'))
        self.password = os.getenv('GTA_DB_PASSWORD_WRITE', os.getenv('GTA_DB_PASSWORD', ''))

        self.storage = storage or ReviewStorage()
        self._conn: Optional[pymysql.Connection] = None

    def _get_connection(self) -> pymysql.Connection:
        """Get or create database connection."""
        if self._conn is None or not self._conn.open:
            self._conn = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
        return self._conn

    def close(self):
        """Close the database connection."""
        if self._conn and self._conn.open:
            self._conn.close()
            self._conn = None

    # ========================================================================
    # WS2: List Step 1 Queue
    # ========================================================================

    async def list_step1_queue(
        self,
        status_id: int = 2,
        limit: int = 20,
        offset: int = 0,
        implementing_jurisdictions: Optional[list[str]] = None,
        date_entered_review_gte: Optional[str] = None
    ) -> dict:
        """List measures awaiting review by status.

        Query uses api_state_act_log with api_state_act_status_log to get accurate
        status_time ordering (most recent first).

        Args:
            limit: Max measures to return (1-100)
            offset: Pagination offset
            implementing_jurisdictions: Filter by jurisdiction codes
            date_entered_review_gte: Filter by date entered review (YYYY-MM-DD)

        Returns:
            Dict with 'results' list and 'count' int
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build the query using api_state_act_log (the main state act table)
        query = '''
            SELECT DISTINCT
                sa.state_act_id as id,
                sa.title,
                sa.description,
                sa.status_id,
                sa.date_announced as announcement_date,
                sa.is_source_official,
                sl.status_time
            FROM api_state_act_log sa
            LEFT JOIN api_state_act_status_log sl
                ON sa.state_act_id = sl.state_act_id AND sl.state_act_status_id = sa.status_id
            WHERE sa.status_id = %s
        '''
        params = [status_id]

        # TODO: Jurisdiction filtering would require joining through interventions
        # For now, filter by jurisdiction is not supported in list view
        if implementing_jurisdictions:
            # Skip jurisdiction filter - would need complex subquery
            pass

        if date_entered_review_gte:
            query += ' AND sl.status_time >= %s'
            params.append(date_entered_review_gte)

        query += ' ORDER BY sl.status_time DESC'
        query += f' LIMIT %s OFFSET %s'
        params.extend([limit, offset])

        cursor.execute(query, params)
        results = cursor.fetchall()

        # Get total count
        count_query = '''
            SELECT COUNT(DISTINCT sa.state_act_id) as count
            FROM api_state_act_log sa
            WHERE sa.status_id = %s
        '''
        cursor.execute(count_query, (status_id,))
        count = cursor.fetchone()['count']

        return {
            'results': results,
            'count': count
        }

    # ========================================================================
    # WS3: Get Measure Detail
    # ========================================================================

    async def get_measure(
        self,
        state_act_id: int,
        include_interventions: bool = True,
        include_comments: bool = True
    ) -> dict:
        """Get complete StateAct details with interventions and comments.

        Args:
            state_act_id: StateAct ID
            include_interventions: Include nested intervention details
            include_comments: Include existing review comments

        Returns:
            Dict with StateAct details, interventions, comments, sources
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get measure - try multiple table names (gta_measure vs api_state_act_log)
        measure = None

        # Try 1: gta_measure (documented table name)
        try:
            cursor.execute('''
                SELECT
                    m.id,
                    m.title,
                    m.description,
                    m.source,
                    m.source_markdown,
                    m.is_source_official,
                    m.status_id,
                    m.announcement_date,
                    m.date_created as creation_date,
                    m.last_modified as last_update,
                    s.status_name,
                    m.author_id,
                    u.username as author_name
                FROM gta_measure m
                LEFT JOIN api_state_act_status_list s ON m.status_id = s.status_id
                LEFT JOIN auth_user u ON m.author_id = u.id
                WHERE m.id = %s
            ''', (state_act_id,))
            measure = cursor.fetchone()
        except Exception:
            pass

        # Try 2: api_state_act_log (alternate table name)
        if not measure:
            try:
                cursor.execute('''
                    SELECT
                        sa.state_act_id as id,
                        sa.title,
                        sa.description,
                        sa.source,
                        sa.source_markdown,
                        sa.source_text,
                        sa.is_source_official,
                        sa.status_id,
                        sa.date_announced as announcement_date,
                        sa.date_created as creation_date,
                        sa.last_modified as last_update,
                        s.status_name,
                        sa.author_id,
                        u.username as author_name
                    FROM api_state_act_log sa
                    LEFT JOIN api_state_act_status_list s ON sa.status_id = s.status_id
                    LEFT JOIN auth_user u ON sa.author_id = u.id
                    WHERE sa.state_act_id = %s
                ''', (state_act_id,))
                measure = cursor.fetchone()
            except Exception:
                # Fallback without source_text column
                cursor.execute('''
                    SELECT
                        sa.state_act_id as id,
                        sa.title,
                        sa.description,
                        sa.source,
                        sa.source_markdown,
                        sa.is_source_official,
                        sa.status_id,
                        sa.date_announced as announcement_date,
                        sa.date_created as creation_date,
                        sa.last_modified as last_update,
                        s.status_name,
                        sa.author_id,
                        u.username as author_name
                    FROM api_state_act_log sa
                    LEFT JOIN api_state_act_status_list s ON sa.status_id = s.status_id
                    LEFT JOIN auth_user u ON sa.author_id = u.id
                    WHERE sa.state_act_id = %s
                ''', (state_act_id,))
                measure = cursor.fetchone()

        if not measure:
            return {'error': f'Measure {state_act_id} not found'}

        # Get implementing jurisdictions (via api_intervention_ij)
        cursor.execute('''
            SELECT DISTINCT j.jurisdiction_id, j.jurisdiction_name, j.iso_code
            FROM api_intervention_log i
            JOIN api_intervention_ij ij ON i.intervention_id = ij.intervention_id
            JOIN api_jurisdiction_list j ON ij.jurisdiction_id = j.jurisdiction_id
            WHERE i.state_act_id = %s
        ''', (state_act_id,))
        measure['implementing_jurisdictions'] = cursor.fetchall()

        # Optionally fetch interventions from api_intervention_log
        if include_interventions:
            # Fetch interventions with implementation level and unit names
            cursor.execute('''
                SELECT
                    i.intervention_id as id,
                    i.state_act_id as measure_id,
                    i.description,
                    i.gta_evaluation_id as evaluation_id,
                    e.gta_evaluation_name as evaluation_name,
                    i.affected_flow_id,
                    af.affected_flow_name,
                    i.eligible_firm_id as eligible_firms_id,
                    ef.eligible_firm_name as eligible_firms_name,
                    i.intervention_type_id as measure_type_id,
                    t.intervention_type_name as type_name,
                    i.date_implemented as inception_date,
                    i.date_removed as removal_date,
                    i.implementation_level_id,
                    il.implementation_level_name,
                    i.unit_id,
                    u.name as unit_name,
                    i.announced_as_temporary,
                    i.is_horizontal,
                    i.chapter_id,
                    mc.chapter_name,
                    i.subchapter_id,
                    ms.subchapter_name
                FROM api_intervention_log i
                LEFT JOIN api_intervention_type_list t ON i.intervention_type_id = t.intervention_type_id
                LEFT JOIN api_gta_evaluation_list e ON i.gta_evaluation_id = e.gta_evaluation_id
                LEFT JOIN api_affected_flow_list af ON i.affected_flow_id = af.affected_flow_id
                LEFT JOIN api_eligible_firm_list ef ON i.eligible_firm_id = ef.eligible_firm_id
                LEFT JOIN api_implementation_level_list il ON i.implementation_level_id = il.implementation_level_id
                LEFT JOIN api_unit_list u ON i.unit_id = u.id
                LEFT JOIN api_mast_chapter_list mc ON i.chapter_id = mc.chapter_id
                LEFT JOIN api_mast_subchapter_list ms ON i.subchapter_id = ms.subchapter_id
                WHERE i.state_act_id = %s
            ''', (state_act_id,))
            measure['interventions'] = cursor.fetchall()

            # Get affected jurisdictions, distorted markets, firms, and levels for each intervention
            for intervention in measure['interventions']:
                # Affected jurisdictions with type (inferred/targeted/excluded/incidental)
                cursor.execute('''
                    SELECT
                        j.jurisdiction_id,
                        j.jurisdiction_name,
                        j.iso_code,
                        aj.aj_type as type_id,
                        jst.jurisdiction_selection_name as type_name
                    FROM api_intervention_aj aj
                    JOIN api_jurisdiction_list j ON aj.jurisdiction_id = j.jurisdiction_id
                    LEFT JOIN api_jurisdiction_selection_type_list jst ON aj.aj_type = jst.jurisdiction_selection_id
                    WHERE aj.intervention_id = %s
                ''', (intervention['id'],))
                intervention['affected_jurisdictions'] = cursor.fetchall()

                # Distorted markets with type (inferred/targeted/excluded/incidental)
                try:
                    cursor.execute('''
                        SELECT
                            j.jurisdiction_id,
                            j.jurisdiction_name,
                            j.iso_code,
                            dm.dm_type as type_id,
                            jst.jurisdiction_selection_name as type_name
                        FROM api_intervention_dm dm
                        JOIN api_jurisdiction_list j ON dm.jurisdiction_id = j.jurisdiction_id
                        LEFT JOIN api_jurisdiction_selection_type_list jst ON dm.dm_type = jst.jurisdiction_selection_id
                        WHERE dm.intervention_id = %s
                    ''', (intervention['id'],))
                    intervention['distorted_markets'] = cursor.fetchall()
                except Exception as e:
                    print(f"[gta-mnt] WARNING: DM query failed for intervention {intervention['id']}: {e}", file=sys.stderr)
                    intervention['distorted_markets'] = []

                # Firms with role (beneficiary/target/acting agency/etc.)
                try:
                    cursor.execute('''
                        SELECT
                            f.firm_id,
                            f.firm_name,
                            fi.role_id,
                            fr.name as role_name
                        FROM api_intervention_firm fi
                        JOIN mtz_firm_log f ON fi.firm_id = f.firm_id
                        LEFT JOIN mtz_firm_role fr ON fi.role_id = fr.id
                        WHERE fi.intervention_id = %s
                    ''', (intervention['id'],))
                    intervention['firms'] = list(cursor.fetchall())
                except Exception as e:
                    print(f"[gta-mnt] WARNING: Firms query failed for intervention {intervention['id']}: {e}", file=sys.stderr)
                    intervention['firms'] = []

                # Acting agencies from legacy table (api_acting_agency_log)
                # Stored separately from api_intervention_firm due to DB migration legacy.
                try:
                    cursor.execute('''
                        SELECT
                            aa.agency_id,
                            aa.agency_name,
                            aa.agency_name_original
                        FROM api_acting_agency_log aa
                        WHERE aa.intervention_id = %s
                    ''', (intervention['id'],))
                    acting_agencies = cursor.fetchall()
                    for aa in acting_agencies:
                        intervention['firms'].append({
                            'firm_id': aa['agency_id'],
                            'firm_name': aa['agency_name'],
                            'firm_name_original': aa.get('agency_name_original', ''),
                            'role_id': None,
                            'role_name': 'acting agency (legacy)'
                        })
                except Exception as e:
                    print(f"[gta-mnt] WARNING: Acting agency query failed for intervention {intervention['id']}: {e}", file=sys.stderr)

                # Levels from api_intervention_level (Fix 4: separate table, not api_intervention_log columns)
                try:
                    cursor.execute('''
                        SELECT
                            il.prior_level,
                            il.new_level,
                            il.tariff_peak,
                            il.intervention_unit_id as unit_id,
                            u.name as unit_name,
                            il.level_type_id,
                            lt.name as level_type_name
                        FROM api_intervention_level il
                        LEFT JOIN api_unit_list u ON il.intervention_unit_id = u.id
                        LEFT JOIN api_level_type_list lt ON il.level_type_id = lt.id
                        WHERE il.intervention_id = %s
                    ''', (intervention['id'],))
                    intervention['level_rows'] = cursor.fetchall()
                except Exception as e:
                    print(f"[gta-mnt] WARNING: Levels query failed for intervention {intervention['id']}: {e}", file=sys.stderr)
                    intervention['level_rows'] = []

                # Products (HS codes)
                try:
                    cursor.execute('''
                        SELECT
                            p.product_id,
                            p.product_description
                        FROM api_intervention_product ip
                        JOIN api_product_list p ON ip.product_id = p.product_id
                        WHERE ip.intervention_id = %s
                    ''', (intervention['id'],))
                    intervention['products'] = cursor.fetchall()
                except Exception as e:
                    print(f"[gta-mnt] WARNING: Products query failed for intervention {intervention['id']}: {e}", file=sys.stderr)
                    intervention['products'] = []

                # Sectors (CPC)
                try:
                    cursor.execute('''
                        SELECT
                            s.sector_id,
                            s.sector_name,
                            isec.type as sector_type
                        FROM api_intervention_sector isec
                        JOIN api_sector_list s ON isec.sector_id = s.sector_id
                        WHERE isec.intervention_id = %s
                    ''', (intervention['id'],))
                    intervention['sectors'] = cursor.fetchall()
                except Exception as e:
                    print(f"[gta-mnt] WARNING: Sectors query failed for intervention {intervention['id']}: {e}", file=sys.stderr)
                    intervention['sectors'] = []

                # Rationale tags
                try:
                    cursor.execute('''
                        SELECT
                            r.rationale_id,
                            r.rationale_name
                        FROM api_intervention_rationale ir
                        JOIN api_rationale_list r ON ir.rationale_id = r.rationale_id
                        WHERE ir.intervention_id = %s
                    ''', (intervention['id'],))
                    intervention['rationales'] = cursor.fetchall()
                except Exception as e:
                    print(f"[gta-mnt] WARNING: Rationales query failed for intervention {intervention['id']}: {e}", file=sys.stderr)
                    intervention['rationales'] = []

                # Locations (subnational taxonomy)
                try:
                    cursor.execute('''
                        SELECT
                            il.id as location_id,
                            il.location_name,
                            il.location_type_id,
                            lt.location_type_name
                        FROM api_intervention_location il
                        LEFT JOIN api_location_type_list lt ON il.location_type_id = lt.location_type_id
                        WHERE il.intervention_id = %s
                    ''', (intervention['id'],))
                    intervention['locations'] = cursor.fetchall()
                except Exception as e:
                    print(f"[gta-mnt] WARNING: Locations query failed for intervention {intervention['id']}: {e}", file=sys.stderr)
                    intervention['locations'] = []

        # Fetch motive quotes from gta_stated_motive_log
        try:
            cursor.execute('''
                SELECT
                    stated_motive_id,
                    stated_motive_name,
                    stated_motive_url
                FROM gta_stated_motive_log
                WHERE state_act_id = %s
            ''', (state_act_id,))
            measure['motive_quotes'] = cursor.fetchall()
        except Exception as e:
            print(f"[gta-mnt] WARNING: Motive quotes query failed: {e}", file=sys.stderr)
            measure['motive_quotes'] = []

        # Optionally fetch comments
        if include_comments:
            cursor.execute('''
                SELECT
                    c.id,
                    c.author_id,
                    u.username as author_name,
                    c.comment_value,
                    c.creation_time,
                    c.updated_at
                FROM api_comment_log c
                LEFT JOIN auth_user u ON c.author_id = u.id
                WHERE c.measure_id = %s
                ORDER BY c.creation_time DESC
            ''', (state_act_id,))
            measure['comments'] = cursor.fetchall()

        # Get source info from linked sources
        # Try multiple table names and schemas since GTA has evolved over time
        sources = []
        tables_tried = []

        # Always fetch source citation URLs from api_state_act_source + api_source_list
        # This is the authoritative source citation table (what the website displays).
        # The legacy gta_measure.source field is often stale/wrong.
        source_citations = []
        try:
            cursor.execute('''
                SELECT
                    sl.source_id,
                    sl.source_url
                FROM api_state_act_source sas
                JOIN api_source_list sl ON sas.source_id = sl.source_id
                WHERE sas.state_act_id = %s
                ORDER BY sas.id ASC
            ''', (state_act_id,))
            source_citations = cursor.fetchall()
            tables_tried.append(('api_state_act_source+api_source_list', len(source_citations)))
        except Exception as e:
            tables_tried.append(('api_state_act_source+api_source_list', f'error: {str(e)[:50]}'))

        measure['source_citations'] = source_citations

        # Try 1: api_files table (uploaded files with field_id = state_act_id)
        try:
            cursor.execute('''
                SELECT
                    af.id as source_id,
                    af.file_url as source_url,
                    af.file_name,
                    af.file_url as s3_url,
                    1 as is_file,
                    1 as is_collected
                FROM api_files af
                WHERE af.field_id = %s
                  AND af.is_deleted = 0
                ORDER BY af.id ASC
            ''', (state_act_id,))
            sources = cursor.fetchall()
            tables_tried.append(('api_files', len(sources)))
        except Exception as e:
            tables_tried.append(('api_files', f'error: {str(e)[:50]}'))

        # Try 2: api_state_act_source + api_source_list (linked sources — fallback for files)
        if not sources and source_citations:
            sources = list(source_citations)
            tables_tried.append(('reused_source_citations_as_sources', len(sources)))

        # Try 2: gta_state_act_source (older schema, direct URL storage)
        if not sources:
            try:
                # First try with state_act_id
                cursor.execute('''
                    SELECT *
                    FROM gta_state_act_source
                    WHERE state_act_id = %s
                    LIMIT 10
                ''', (state_act_id,))
                sources = cursor.fetchall()
                tables_tried.append(('gta_state_act_source(state_act_id)', len(sources)))
            except Exception as e:
                tables_tried.append(('gta_state_act_source(state_act_id)', f'error: {str(e)[:50]}'))

        # Try 2b: gta_state_act_source with measure_id
        if not sources:
            try:
                cursor.execute('''
                    SELECT *
                    FROM gta_state_act_source
                    WHERE measure_id = %s
                    LIMIT 10
                ''', (state_act_id,))
                sources = cursor.fetchall()
                tables_tried.append(('gta_state_act_source(measure_id)', len(sources)))
            except Exception as e:
                tables_tried.append(('gta_state_act_source(measure_id)', f'error: {str(e)[:50]}'))

        # Try 3: Look in api_state_act_file for uploaded files
        if not sources:
            try:
                cursor.execute('''
                    SELECT
                        id as source_id,
                        file_path as source_url,
                        s3_key,
                        1 as is_file,
                        1 as is_collected
                    FROM api_state_act_file
                    WHERE state_act_id = %s
                    ORDER BY id ASC
                ''', (state_act_id,))
                sources = cursor.fetchall()
                tables_tried.append(('api_state_act_file', len(sources)))
            except Exception as e:
                tables_tried.append(('api_state_act_file', f'error: {str(e)[:50]}'))

        # Debug: List columns in key tables
        try:
            cursor.execute('DESCRIBE gta_state_act_source')
            columns = [row['Field'] for row in cursor.fetchall()]
            tables_tried.append(('gta_state_act_source_cols', ', '.join(columns)))
        except Exception as e:
            tables_tried.append(('gta_state_act_source_cols', f'error'))

        try:
            cursor.execute('DESCRIBE api_source_list')
            columns = [row['Field'] for row in cursor.fetchall()]
            tables_tried.append(('api_source_list_cols', ', '.join(columns[:8])))
        except Exception as e:
            tables_tried.append(('api_source_list_cols', f'error'))

        # Try 5: gta_source table (might be junction with measure_id)
        if not sources:
            try:
                cursor.execute('''
                    SELECT
                        id as source_id,
                        url as source_url,
                        s3_key,
                        1 as is_file
                    FROM gta_source
                    WHERE measure_id = %s
                    ORDER BY id ASC
                ''', (state_act_id,))
                sources = cursor.fetchall()
                tables_tried.append(('gta_source', len(sources)))
            except Exception as e:
                tables_tried.append(('gta_source', f'error: {str(e)[:50]}'))

        # Try 5: Look for attached documents (some systems use this pattern)
        if not sources:
            try:
                cursor.execute('''
                    SELECT
                        id as source_id,
                        file_url as source_url,
                        s3_path as s3_key,
                        1 as is_file
                    FROM gta_attached_document
                    WHERE state_act_id = %s
                    ORDER BY id ASC
                ''', (state_act_id,))
                sources = cursor.fetchall()
                tables_tried.append(('gta_attached_document', len(sources)))
            except Exception as e:
                tables_tried.append(('gta_attached_document', f'error: {str(e)[:50]}'))

        # Try 6: Check gta_measure.source field directly for URL
        if not sources and measure.get('source'):
            source_field = measure.get('source', '')
            if source_field.startswith('http'):
                sources = [{
                    'source_id': None,
                    'source_url': source_field,
                    'is_file': False,
                    'is_collected': False,
                    'from_measure_field': True
                }]
                tables_tried.append(('measure.source_field', 1))

        # Store debug info about which tables were tried
        measure['_debug_tables_tried'] = tables_tried

        # If files are uploaded with naming convention (96351a.pdf, etc.), construct S3 paths
        # The GTA system stores uploaded files as {state_act_id}{letter}.pdf in S3
        s3_bucket = 'gta-source-files'  # Default bucket name
        for i, src in enumerate(sources):
            if src.get('is_file') and not src.get('collected_path') and not src.get('s3_key'):
                # Construct S3 path from naming convention: {state_act_id}{letter}.pdf
                letter = chr(ord('a') + i)  # a, b, c, d, ...
                src['s3_key'] = f"sources/{state_act_id}{letter}.pdf"
                src['s3_url'] = f"s3://{s3_bucket}/sources/{state_act_id}{letter}.pdf"

        measure['sources'] = sources

        # Fetch related state acts and their intervention-level levels
        try:
            cursor.execute('''
                SELECT rm.related_measure_id as id
                FROM gta_related_measures rm
                WHERE rm.measure_id = %s
            ''', (state_act_id,))
            related_ids = [r['id'] for r in cursor.fetchall()]

            # Also fetch reverse relationships
            cursor.execute('''
                SELECT rm.measure_id as id
                FROM gta_related_measures rm
                WHERE rm.related_measure_id = %s
            ''', (state_act_id,))
            related_ids += [r['id'] for r in cursor.fetchall()]
            related_ids = list(set(related_ids))

            related_state_acts = []
            for rel_id in related_ids[:5]:  # cap at 5
                cursor.execute('''
                    SELECT sa.state_act_id as id, sa.title, sa.date_announced as announcement_date
                    FROM api_state_act_log sa WHERE sa.state_act_id = %s
                ''', (rel_id,))
                rel_sa = cursor.fetchone()
                if rel_sa:
                    cursor.execute('''
                        SELECT i.intervention_id, i.prior_level, i.new_level,
                               i.unit_id, u.name as unit_name,
                               i.intervention_type_id, t.intervention_type_name as type_name,
                               i.date_implemented
                        FROM api_intervention_log i
                        LEFT JOIN api_unit_list u ON i.unit_id = u.id
                        LEFT JOIN api_intervention_type_list t ON i.intervention_type_id = t.intervention_type_id
                        WHERE i.state_act_id = %s
                    ''', (rel_id,))
                    rel_sa['interventions'] = cursor.fetchall()
                    related_state_acts.append(rel_sa)

            measure['related_state_acts'] = related_state_acts
        except Exception as e:
            print(f"[gta-mnt] WARNING: Related SAs query failed: {e}", file=sys.stderr)
            measure['related_state_acts'] = []

        # Extract URLs from various text fields
        import re
        url_pattern = r'https?://[^\s<>\"\'\)]+(?:\.[^\s<>\"\'\)]+)+'

        source_markdown = measure.get('source_markdown') or ''
        description = measure.get('description') or ''

        extracted_urls = []
        # Try source_markdown first
        if source_markdown:
            extracted_urls = list(set(re.findall(url_pattern, source_markdown)))
        # Also try description if no URLs in source_markdown
        if not extracted_urls and description:
            extracted_urls = list(set(re.findall(url_pattern, description)))

        # Combine database sources with extracted URLs
        all_sources = list(sources)  # Copy to avoid modifying original
        if not all_sources and extracted_urls:
            # No database sources but we found URLs in markdown
            for i, url in enumerate(extracted_urls):
                all_sources.append({
                    'source_id': None,
                    'source_url': url,
                    'is_collected': False,
                    'is_file': False,
                    'extracted_from_markdown': True
                })

        # Also include the direct source field
        measure['source_info'] = {
            'primary_source': measure.get('source') or measure.get('source_markdown'),
            'linked_sources': all_sources,
            'extracted_urls': extracted_urls
        }

        return measure

    # ========================================================================
    # WS6: Set Status
    # ========================================================================

    async def set_status(
        self,
        state_act_id: int,
        new_status_id: int,
        comment: Optional[str] = None
    ) -> dict:
        """Update StateAct status and create status log entry.

        Args:
            state_act_id: StateAct ID
            new_status_id: Status ID (2=Step1, 3=Publishable, 6=Under revision)
            comment: Optional reason for status change

        Returns:
            Dict with success status and message
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Update measure status in api_state_act_log
            cursor.execute(
                'UPDATE api_state_act_log SET status_id = %s WHERE state_act_id = %s',
                (new_status_id, state_act_id)
            )

            # Log the status change
            cursor.execute('''
                INSERT INTO api_state_act_status_log
                    (state_act_id, state_act_status_id, status_time)
                VALUES (%s, %s, %s)
            ''', (state_act_id, new_status_id, datetime.now(UTC)))

            conn.commit()

            return {
                'success': True,
                'state_act_id': state_act_id,
                'new_status_id': new_status_id,
                'message': f'Status updated to {new_status_id}'
            }

        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to update status: {e}'
            }

    # ========================================================================
    # WS5: Add Comment
    # ========================================================================

    async def add_comment(
        self,
        measure_id: int,
        comment_text: str,
        template_id: Optional[int] = None
    ) -> dict:
        """Add a comment to a StateAct.

        Args:
            measure_id: StateAct ID
            comment_text: Full comment text (structured markdown)
            template_id: Optional template ID for standardized comments

        Returns:
            Dict with comment_id, success status, and message
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            now = datetime.now(UTC)

            cursor.execute('''
                INSERT INTO api_comment_log
                    (author_id, measure_id, comment_value, creation_time, updated_at, comment_visible, comment_template_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (SANCHO_USER_ID, measure_id, comment_text, now, now, 1, template_id))

            conn.commit()
            comment_id = cursor.lastrowid

            # Save to persistent storage
            self.storage.save_comment(
                state_act_id=measure_id,
                comment_text=comment_text,
                comment_id=comment_id
            )

            return {
                'comment_id': comment_id,
                'success': True,
                'message': f'Comment added to StateAct {measure_id}'
            }

        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to add comment: {e}'
            }

    # ========================================================================
    # WS7: Add Framework
    # ========================================================================

    async def add_framework(
        self,
        state_act_id: int,
        framework_name: str = "sancho claudino review"
    ) -> dict:
        """Attach framework tag to a StateAct for tracking.

        Resolves framework_name to its ID via FRAMEWORK_IDS mapping,
        ensures the framework row exists in api_framework_log (INSERT IGNORE),
        then inserts the assignment in api_state_act_framework.

        Args:
            state_act_id: StateAct ID
            framework_name: Framework name (default: "sancho claudino review").
                Known frameworks: "sancho claudino review" (495),
                "sancho claudito reported" (500).

        Returns:
            Dict with success status and message
        """
        framework_id = FRAMEWORK_IDS.get(framework_name)
        if framework_id is None:
            return {
                'success': False,
                'error': f'Unknown framework: {framework_name}',
                'message': f"Unknown framework '{framework_name}'. Known: {list(FRAMEWORK_IDS.keys())}"
            }

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Ensure framework row exists (INSERT IGNORE — rows already exist in prod)
            cursor.execute(
                'INSERT IGNORE INTO api_framework_log (id, name, pinned) VALUES (%s, %s, 0)',
                (framework_id, framework_name)
            )

            # Attach framework to state act — check first to avoid duplicates
            # (api_state_act_framework has no unique constraint on (framework_id, state_act_id))
            cursor.execute(
                'SELECT id FROM api_state_act_framework WHERE framework_id = %s AND state_act_id = %s',
                (framework_id, state_act_id)
            )
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO api_state_act_framework (framework_id, state_act_id)
                    VALUES (%s, %s)
                ''', (framework_id, state_act_id))
            conn.commit()

            return {
                'state_act_id': state_act_id,
                'framework_id': framework_id,
                'success': True,
                'message': f"Framework '{framework_name}' (ID {framework_id}) attached to StateAct {state_act_id}"
            }

        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to add framework: {e}'
            }

    # ========================================================================
    # Entry Creation: Lookup
    # ========================================================================

    async def lookup(
        self,
        table: str,
        query: str,
        limit: int = 20
    ) -> dict:
        """Look up IDs in reference tables by search string.

        Args:
            table: Short name from LOOKUP_TABLES (e.g. 'jurisdiction', 'product')
            query: Search string (LIKE match with wildcards)
            limit: Max results

        Returns:
            Dict with 'results' list and 'table' name
        """
        if table not in LOOKUP_TABLES:
            return {
                'error': f"Unknown table '{table}'. Valid: {', '.join(sorted(LOOKUP_TABLES.keys()))}"
            }

        table_name, id_col, name_col = LOOKUP_TABLES[table]
        conn = self._get_connection()
        cursor = conn.cursor()

        search = f'%{query}%'
        cursor.execute(
            f'SELECT * FROM {table_name} WHERE {name_col} LIKE %s LIMIT %s',
            (search, limit)
        )
        results = cursor.fetchall()

        return {'results': results, 'table': table_name, 'id_column': id_col, 'name_column': name_col}

    # ========================================================================
    # Entry Creation: Create State Act
    # ========================================================================

    async def create_state_act(
        self,
        title: str,
        description: str,
        source_url: str,
        is_source_official: int,
        date_announced: str,
        evaluation_id: int,
        source_citation: Optional[str] = None,
        dry_run: bool = False
    ) -> dict:
        """Create a new state act (measure) in api_state_act_log.

        Always creates with status_id=1 (In progress).

        Args:
            title: State act title
            description: Announcement description text
            source_url: Primary source URL
            is_source_official: 1 if official source, 0 if not
            date_announced: YYYY-MM-DD
            evaluation_id: 1=Red, 2=Amber, 3=Green
            source_citation: Full GTA citation string (e.g. 'Author (Date). TITLE. Publisher (Retrieved): URL').
                           Stored in both source_markdown and source fields.
                           If omitted, source_url is used as fallback.
            dry_run: If True, return SQL without executing

        Returns:
            Dict with state_act_id and success status
        """
        now = datetime.now(UTC)
        status_id = 1  # In progress — never create in publishable or review state
        citation_text = source_citation or source_url

        # Convert plain text description to HTML (<p> wrapped) + store markdown copy
        description_html = ''.join(f'<p>{p.strip()}</p>' for p in description.split('\n\n') if p.strip()) if description else ''
        description_markdown = description  # Plain text version

        insert_sql = '''
            INSERT INTO api_state_act_log
                (title, description, description_markdown, source_markdown, source, date_announced,
                 is_source_official, status_id, evaluation_id,
                 author_id, date_created, last_modified,
                 is_migrated, is_validated_after_migration, submit_to_review_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        params = (
            title, description_html, description_markdown, citation_text, citation_text, date_announced,
            is_source_official, status_id, evaluation_id,
            SANCHO_AUTHOR_ID, now.strftime('%Y-%m-%d'), now,
            1, 1, now.strftime('%Y-%m-%d')
        )

        if dry_run:
            return {
                'dry_run': True,
                'sql': insert_sql.strip(),
                'params': [str(p) for p in params],
                'rollback': 'DELETE FROM api_state_act_log WHERE state_act_id = <returned_id>'
            }

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(insert_sql, params)
            state_act_id = cursor.lastrowid

            # Generate slug for public URLs (mirrors Django AutoSlugField)
            slug = f"{state_act_id}-{_slugify(title)}"
            cursor.execute(
                'UPDATE api_state_act_log SET slug = %s WHERE state_act_id = %s',
                (slug, state_act_id)
            )

            # Log initial status
            cursor.execute('''
                INSERT INTO api_state_act_status_log
                    (state_act_id, state_act_status_id, status_time)
                VALUES (%s, %s, %s)
            ''', (state_act_id, status_id, now))

            # Also add the source URL to api_source_list + api_state_act_source
            cursor.execute(
                'SELECT source_id FROM api_source_list WHERE source_url = %s LIMIT 1',
                (source_url,)
            )
            existing = cursor.fetchone()
            if existing:
                source_id = existing['source_id']
            else:
                cursor.execute('''
                    INSERT INTO api_source_list
                        (source_url, is_collected, is_file, is_404)
                    VALUES (%s, 0, 0, 0)
                ''', (source_url,))
                source_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO api_state_act_source (source_id, state_act_id)
                VALUES (%s, %s)
            ''', (source_id, state_act_id))

            # Write source citation to api_state_act_source_log_new
            # (admin dashboard reads source display from this table)
            cursor.execute('''
                INSERT INTO api_state_act_source_log_new
                    (status, source, source_markdown, datetime_created,
                     datetime_modified, order_nr, state_act_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', ('NEW', citation_text, citation_text, now, now, 1, state_act_id))

            conn.commit()

            return {
                'success': True,
                'state_act_id': state_act_id,
                'source_id': source_id,
                'status_id': status_id,
                'message': f'State act {state_act_id} created with status {status_id}'
            }

        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e), 'message': f'Failed to create state act: {e}'}

    # ========================================================================
    # Entry Creation: Create Intervention
    # ========================================================================

    async def create_intervention(
        self,
        state_act_id: int,
        description: str,
        intervention_type_id: int,
        chapter_id: int,
        subchapter_id: int,
        gta_evaluation_id: int,
        affected_flow_id: int,
        eligible_firm_id: int,
        implementation_level_id: int,
        intervention_area_id: int,
        date_implemented: str,
        date_announced: str,
        title: Optional[str] = None,
        announced_as_temporary: int = 0,
        is_horizontal: int = 0,
        aj_type: int = 1,
        dm_type: int = 1,
        dry_run: bool = False
    ) -> dict:
        """Create a new intervention in api_intervention_log.

        Args:
            state_act_id: FK to api_state_act_log
            description: Intervention description text
            intervention_type_id: e.g. 81 (Equity stake)
            chapter_id: MAST chapter
            subchapter_id: MAST subchapter
            gta_evaluation_id: 1=Red, 2=Amber, 3=Green
            affected_flow_id: 1=Inward, 2=Outward, 3=Outward subsidy
            eligible_firm_id: e.g. 3 (firm-specific)
            implementation_level_id: e.g. 6 (NFI)
            intervention_area_id: 1=goods, 2=service, 3=investment
            date_implemented: YYYY-MM-DD
            date_announced: YYYY-MM-DD
            title: Optional title (defaults to state act title)
            announced_as_temporary: 0/1
            is_horizontal: 0/1 (1 if measure affects practically all sectors with uncertain intensity)
            aj_type: 1=inferred, 2=targeted, 3=excluded, 4=incidental
            dm_type: 1=inferred, 2=targeted, 3=excluded, 4=incidental
            dry_run: If True, return SQL without executing

        Returns:
            Dict with intervention_id and success status
        """
        now = datetime.now(UTC)

        # If no title provided, fetch from state act
        if not title:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT title FROM api_state_act_log WHERE state_act_id = %s',
                (state_act_id,)
            )
            sa = cursor.fetchone()
            title = sa['title'] if sa else 'Untitled'

        # Convert plain text description to HTML (<p> wrapped) + store markdown copy
        description_html = ''.join(f'<p>{p.strip()}</p>' for p in description.split('\n\n') if p.strip()) if description else ''
        description_markdown = description  # Plain text version

        insert_sql = '''
            INSERT INTO api_intervention_log
                (state_act_id, title, description, description_markdown_collected,
                 intervention_type_id,
                 chapter_id, subchapter_id, gta_evaluation_id,
                 affected_flow_id, eligible_firm_id, implementation_level_id,
                 intervention_area_id, date_implemented, date_announced,
                 announced_as_temporary, is_horizontal, aj_type, dm_type,
                 status_id,
                 is_in_counts, is_in_coverage, is_in_inspector,
                 date_created, last_modified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        params = (
            state_act_id, title, description_html, description_markdown,
            intervention_type_id,
            chapter_id, subchapter_id, gta_evaluation_id,
            affected_flow_id, eligible_firm_id, implementation_level_id,
            intervention_area_id, date_implemented, date_announced,
            announced_as_temporary, is_horizontal, aj_type, dm_type,
            1,  # status_id=1 (In progress), matching state act status
            0, 0, 0,
            now.strftime('%Y-%m-%d'), now
        )

        if dry_run:
            return {
                'dry_run': True,
                'sql': insert_sql.strip(),
                'params': [str(p) for p in params],
                'rollback': 'DELETE FROM api_intervention_log WHERE intervention_id = <returned_id>'
            }

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Validate state_act_id exists
            cursor.execute(
                'SELECT state_act_id FROM api_state_act_log WHERE state_act_id = %s',
                (state_act_id,)
            )
            if not cursor.fetchone():
                return {'success': False, 'error': f'State act {state_act_id} not found'}

            cursor.execute(insert_sql, params)
            intervention_id = cursor.lastrowid

            # Generate slug for public URLs (mirrors Django AutoSlugField)
            slug = f"{intervention_id}-{_slugify(title)}"
            cursor.execute(
                'UPDATE api_intervention_log SET slug = %s WHERE intervention_id = %s',
                (slug, intervention_id)
            )

            # Write description to api_intervention_description_log
            # (admin dashboard reads intervention descriptions from this table)
            cursor.execute('''
                INSERT INTO api_intervention_description_log
                    (status, description, description_markdown,
                     datetime_created, datetime_modified, order_nr, intervention_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', ('NEW', description_html, description_markdown, now, now, 1, intervention_id))

            conn.commit()

            return {
                'success': True,
                'intervention_id': intervention_id,
                'state_act_id': state_act_id,
                'message': f'Intervention {intervention_id} created under state act {state_act_id}'
            }

        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e), 'message': f'Failed to create intervention: {e}'}

    # ========================================================================
    # Entry Creation: Add Implementing Jurisdiction
    # ========================================================================

    async def add_ij(
        self,
        intervention_id: int,
        jurisdiction_id: int,
        dry_run: bool = False
    ) -> dict:
        """Add implementing jurisdiction to an intervention.

        Args:
            intervention_id: FK to api_intervention_log
            jurisdiction_id: FK to api_jurisdiction_list
            dry_run: If True, return SQL without executing

        Returns:
            Dict with success status
        """
        insert_sql = '''
            INSERT INTO api_intervention_ij (intervention_id, jurisdiction_id)
            VALUES (%s, %s)
        '''
        params = (intervention_id, jurisdiction_id)

        if dry_run:
            return {'dry_run': True, 'sql': insert_sql.strip(), 'params': [str(p) for p in params]}

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Validate FK references
            cursor.execute('SELECT intervention_id FROM api_intervention_log WHERE intervention_id = %s', (intervention_id,))
            if not cursor.fetchone():
                return {'success': False, 'error': f'Intervention {intervention_id} not found'}
            cursor.execute('SELECT jurisdiction_id FROM api_jurisdiction_list WHERE jurisdiction_id = %s', (jurisdiction_id,))
            if not cursor.fetchone():
                return {'success': False, 'error': f'Jurisdiction {jurisdiction_id} not found'}

            cursor.execute(insert_sql, params)
            conn.commit()
            return {
                'success': True,
                'id': cursor.lastrowid,
                'message': f'Jurisdiction {jurisdiction_id} added to intervention {intervention_id}'
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}

    # ========================================================================
    # Entry Creation: Add Product
    # ========================================================================

    async def add_product(
        self,
        intervention_id: int,
        product_id: int,
        prior_level: Optional[str] = None,
        new_level: Optional[str] = None,
        unit_id: Optional[int] = None,
        date_implemented: Optional[str] = None,
        date_removed: Optional[str] = None,
        dry_run: bool = False
    ) -> dict:
        """Add affected product to an intervention.

        Args:
            intervention_id: FK to api_intervention_log
            product_id: FK to api_product_list (look up from HS code via gta_mnt_lookup)
            prior_level: Optional prior tariff/level value for this product
            new_level: Optional new tariff/level value for this product
            unit_id: Optional FK to api_unit_list (e.g. percentage, specific rate)
            date_implemented: Optional per-product implementation date (YYYY-MM-DD)
            date_removed: Optional per-product removal date (YYYY-MM-DD)
            dry_run: If True, return SQL without executing

        Returns:
            Dict with success status
        """
        # Build column list dynamically based on provided optional fields
        columns = ['intervention_id', 'product_id', 'is_completely_captured', 'is_in_original']
        values = [intervention_id, product_id, 0, 1]

        if prior_level is not None:
            columns.append('prior_level')
            values.append(prior_level)
        if new_level is not None:
            columns.append('new_level')
            values.append(new_level)
        if unit_id is not None:
            columns.append('unit_id')
            values.append(unit_id)
        if date_implemented is not None:
            columns.append('date_implemented')
            values.append(date_implemented)
        if date_removed is not None:
            columns.append('date_removed')
            values.append(date_removed)

        placeholders = ', '.join(['%s'] * len(values))
        insert_sql = f'''
            INSERT INTO api_intervention_product
                ({', '.join(columns)})
            VALUES ({placeholders})
        '''
        params = tuple(values)

        if dry_run:
            return {'dry_run': True, 'sql': insert_sql.strip(), 'params': [str(p) for p in params]}

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT product_id FROM api_product_list WHERE product_id = %s', (product_id,))
            if not cursor.fetchone():
                return {'success': False, 'error': f'Product {product_id} not found in api_product_list'}

            cursor.execute(insert_sql, params)
            conn.commit()
            return {
                'success': True,
                'id': cursor.lastrowid,
                'message': f'Product {product_id} added to intervention {intervention_id}'
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}

    # ========================================================================
    # Entry Creation: Add Sector
    # ========================================================================

    async def add_sector(
        self,
        intervention_id: int,
        sector_id: int,
        sector_type: str = 'N',
        dry_run: bool = False
    ) -> dict:
        """Add affected sector to an intervention.

        Args:
            intervention_id: FK to api_intervention_log
            sector_id: FK to api_sector_list
            sector_type: 'N' (normal), 'A' (additional), 'P' (primary)
            dry_run: If True, return SQL without executing

        Returns:
            Dict with success status
        """
        insert_sql = '''
            INSERT INTO api_intervention_sector
                (intervention_id, sector_id, type)
            VALUES (%s, %s, %s)
        '''
        params = (intervention_id, sector_id, sector_type)

        if dry_run:
            return {'dry_run': True, 'sql': insert_sql.strip(), 'params': [str(p) for p in params]}

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT sector_id FROM api_sector_list WHERE sector_id = %s', (sector_id,))
            if not cursor.fetchone():
                return {'success': False, 'error': f'Sector {sector_id} not found'}

            cursor.execute(insert_sql, params)
            conn.commit()
            return {
                'success': True,
                'id': cursor.lastrowid,
                'message': f'Sector {sector_id} added to intervention {intervention_id}'
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}

    # ========================================================================
    # Entry Creation: Add Rationale
    # ========================================================================

    async def add_rationale(
        self,
        intervention_id: int,
        rationale_id: int,
        dry_run: bool = False
    ) -> dict:
        """Add rationale/motive to an intervention.

        Args:
            intervention_id: FK to api_intervention_log
            rationale_id: FK to api_rationale_list
            dry_run: If True, return SQL without executing

        Returns:
            Dict with success status
        """
        insert_sql = '''
            INSERT INTO api_intervention_rationale (intervention_id, rationale_id)
            VALUES (%s, %s)
        '''
        params = (intervention_id, rationale_id)

        if dry_run:
            return {'dry_run': True, 'sql': insert_sql.strip(), 'params': [str(p) for p in params]}

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT rationale_id FROM api_rationale_list WHERE rationale_id = %s', (rationale_id,))
            if not cursor.fetchone():
                return {'success': False, 'error': f'Rationale {rationale_id} not found'}

            cursor.execute(insert_sql, params)
            conn.commit()
            return {
                'success': True,
                'id': cursor.lastrowid,
                'message': f'Rationale {rationale_id} added to intervention {intervention_id}'
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}

    # ========================================================================
    # Entry Creation: Add Firm
    # ========================================================================

    async def add_firm(
        self,
        intervention_id: int,
        firm_name: str,
        role_id: int,
        jurisdiction_id: Optional[int] = None,
        dry_run: bool = False
    ) -> dict:
        """Add firm to an intervention. Creates firm in mtz_firm_log if it doesn't exist.

        Args:
            intervention_id: FK to api_intervention_log
            firm_name: Firm name (looked up or created)
            role_id: FK to mtz_firm_role (1=beneficiary, 2=target, 3=acting agency, etc.)
            jurisdiction_id: Optional FK to api_jurisdiction_list (firm's home jurisdiction)
            dry_run: If True, return SQL without executing

        Returns:
            Dict with firm_id and success status
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Look up existing firm
        cursor.execute(
            'SELECT firm_id FROM mtz_firm_log WHERE firm_name = %s LIMIT 1',
            (firm_name,)
        )
        existing = cursor.fetchone()

        if dry_run:
            sqls = []
            if not existing:
                sqls.append(f"INSERT INTO mtz_firm_log (firm_name, jurisdiction_id, priority, status_id, hs_status_id, cpc_status_id) VALUES ('{firm_name}', {jurisdiction_id}, 0, 1, 1, 1)")
            sqls.append(f"INSERT INTO api_intervention_firm (firm_id, intervention_id, role_id) VALUES (<firm_id>, {intervention_id}, {role_id})")
            return {'dry_run': True, 'sql': sqls, 'existing_firm': existing is not None}

        try:
            if existing:
                firm_id = existing['firm_id']
            else:
                cursor.execute('''
                    INSERT INTO mtz_firm_log
                        (firm_name, jurisdiction_id, priority,
                         status_id, hs_status_id, cpc_status_id)
                    VALUES (%s, %s, 0, 1, 1, 1)
                ''', (firm_name, jurisdiction_id))
                firm_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO api_intervention_firm (firm_id, intervention_id, role_id)
                VALUES (%s, %s, %s)
            ''', (firm_id, intervention_id, role_id))

            # Acting agencies also need a legacy table entry (api_acting_agency_log)
            # role_id 3 = acting agency in mtz_firm_role
            if role_id == 3:
                cursor.execute('''
                    INSERT INTO api_acting_agency_log
                        (agency_name, agency_name_original, intervention_id)
                    VALUES (%s, %s, %s)
                ''', (firm_name, firm_name, intervention_id))

            conn.commit()
            return {
                'success': True,
                'firm_id': firm_id,
                'created_new': existing is None,
                'message': f'Firm "{firm_name}" (ID {firm_id}) added to intervention {intervention_id} with role {role_id}'
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}

    # ========================================================================
    # Entry Creation: Add Source
    # ========================================================================

    async def add_source(
        self,
        state_act_id: int,
        source_url: str,
        source_citation: Optional[str] = None,
        dry_run: bool = False
    ) -> dict:
        """Add a source URL to a state act.

        Creates in api_source_list if URL is new, then links via api_state_act_source.
        Also writes citation to api_state_act_source_log_new for admin dashboard display.

        Args:
            state_act_id: FK to api_state_act_log
            source_url: Source URL
            source_citation: Full GTA citation string. If omitted, source_url is used.
            dry_run: If True, return SQL without executing

        Returns:
            Dict with source_id and success status
        """
        now = datetime.now(UTC)
        citation_text = source_citation or source_url
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if URL already exists
        cursor.execute(
            'SELECT source_id FROM api_source_list WHERE source_url = %s LIMIT 1',
            (source_url,)
        )
        existing = cursor.fetchone()

        if dry_run:
            sqls = []
            if not existing:
                sqls.append(f"INSERT INTO api_source_list (source_url, is_collected, is_file, is_404) VALUES ('{source_url}', 0, 0, 0)")
            sqls.append(f"INSERT INTO api_state_act_source (source_id, state_act_id) VALUES (<source_id>, {state_act_id})")
            sqls.append(f"INSERT INTO api_state_act_source_log_new (status, source, source_markdown, ...) VALUES ('NEW', '<citation>', ...)")
            return {'dry_run': True, 'sql': sqls}

        try:
            if existing:
                source_id = existing['source_id']
            else:
                cursor.execute('''
                    INSERT INTO api_source_list (source_url, is_collected, is_file, is_404)
                    VALUES (%s, 0, 0, 0)
                ''', (source_url,))
                source_id = cursor.lastrowid

            # Check for duplicate link
            cursor.execute(
                'SELECT id FROM api_state_act_source WHERE source_id = %s AND state_act_id = %s',
                (source_id, state_act_id)
            )
            if cursor.fetchone():
                return {
                    'success': True,
                    'source_id': source_id,
                    'message': f'Source {source_id} already linked to state act {state_act_id}'
                }

            cursor.execute('''
                INSERT INTO api_state_act_source (source_id, state_act_id)
                VALUES (%s, %s)
            ''', (source_id, state_act_id))

            # Determine next order_nr for this state act
            cursor.execute(
                'SELECT COALESCE(MAX(order_nr), 0) + 1 as next_nr FROM api_state_act_source_log_new WHERE state_act_id = %s',
                (state_act_id,)
            )
            next_order = cursor.fetchone()['next_nr']

            # Write citation to api_state_act_source_log_new for admin dashboard display
            cursor.execute('''
                INSERT INTO api_state_act_source_log_new
                    (status, source, source_markdown, datetime_created,
                     datetime_modified, order_nr, state_act_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', ('NEW', citation_text, citation_text, now, now, next_order, state_act_id))

            conn.commit()
            return {
                'success': True,
                'source_id': source_id,
                'created_new': existing is None,
                'message': f'Source {source_id} linked to state act {state_act_id}'
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}

    # ========================================================================
    # Entry Creation: Queue Recalculation
    # ========================================================================

    async def queue_recalculation(
        self,
        intervention_id: int,
        dry_run: bool = False
    ) -> dict:
        """Queue an intervention for AJ/DM auto-population via COMTRADE.

        Inserts into api_recalculation_log with status=0 (PENDING).
        The population_procedure picks this up and calculates affected jurisdictions
        and distorted markets from COMTRADE trade data.

        Args:
            intervention_id: FK to api_intervention_log
            dry_run: If True, return SQL without executing

        Returns:
            Dict with success status
        """
        insert_sql = '''
            INSERT INTO api_recalculation_log (intervention_id, status)
            VALUES (%s, 0)
        '''

        if dry_run:
            return {
                'dry_run': True,
                'sql': insert_sql.strip(),
                'params': [str(intervention_id)]
            }

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Validate intervention exists
            cursor.execute(
                'SELECT intervention_id FROM api_intervention_log WHERE intervention_id = %s',
                (intervention_id,)
            )
            if not cursor.fetchone():
                return {'success': False, 'error': f'Intervention {intervention_id} not found'}

            cursor.execute(insert_sql, (intervention_id,))
            conn.commit()
            return {
                'success': True,
                'id': cursor.lastrowid,
                'message': f'Intervention {intervention_id} queued for AJ/DM recalculation'
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}

    # ========================================================================
    # Entry Creation: Add Intervention Level
    # ========================================================================

    async def add_level(
        self,
        intervention_id: int,
        prior_level: Optional[str] = None,
        new_level: Optional[str] = None,
        unit_id: Optional[int] = None,
        level_type_id: Optional[int] = None,
        tariff_peak: Optional[int] = None,
        dry_run: bool = False
    ) -> dict:
        """Add a level row to api_intervention_level.

        Args:
            intervention_id: FK to api_intervention_log
            prior_level: Prior level value (varchar)
            new_level: New level value (varchar)
            unit_id: FK to api_unit_list
            level_type_id: FK to api_level_type_list
            tariff_peak: Tariff peak indicator
            dry_run: If True, return SQL without executing

        Returns:
            Dict with success status
        """
        insert_sql = '''
            INSERT INTO api_intervention_level
                (intervention_id, prior_level, new_level, intervention_unit_id, level_type_id, tariff_peak)
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        params = (intervention_id, prior_level, new_level, unit_id, level_type_id, tariff_peak)

        if dry_run:
            return {'dry_run': True, 'sql': insert_sql.strip(), 'params': [str(p) for p in params]}

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(insert_sql, params)
            conn.commit()
            return {
                'success': True,
                'id': cursor.lastrowid,
                'message': f'Level row added to intervention {intervention_id}'
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}

    # ========================================================================
    # Motive Quotes
    # ========================================================================

    async def add_motive_quote(
        self,
        state_act_id: int,
        motive_quote: str,
        source_url: Optional[str] = None,
        dry_run: bool = False
    ) -> dict:
        """Add a stated motive quote to gta_stated_motive_log.

        Args:
            state_act_id: FK to api_state_act_log
            motive_quote: The quoted text from the source
            source_url: URL where the quote was found
            dry_run: If True, return SQL without executing

        Returns:
            Dict with success status
        """
        insert_sql = '''
            INSERT INTO gta_stated_motive_log
                (stated_motive_name, state_act_id, stated_motive_url)
            VALUES (%s, %s, %s)
        '''
        params = (motive_quote, state_act_id, source_url)

        if dry_run:
            return {'dry_run': True, 'sql': insert_sql.strip(), 'params': [str(p) for p in params]}

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(insert_sql, params)
            conn.commit()
            return {
                'success': True,
                'id': cursor.lastrowid,
                'message': f'Motive quote added to state act {state_act_id}'
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}

    # ========================================================================
    # WS10: List Templates
    # ========================================================================

    async def list_templates(
        self,
        include_checklist: bool = False
    ) -> dict:
        """List available comment templates.

        Args:
            include_checklist: Include checklist templates

        Returns:
            Dict with 'results' list of templates
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT comment_template_id as id,
                   comment_template_short as template_name,
                   comment_template_text as template_text,
                   is_checklist
            FROM api_comment_template_list
            WHERE visible = 1
        '''
        if not include_checklist:
            query += " AND is_checklist = 0"

        query += ' ORDER BY comment_template_short'

        cursor.execute(query)
        results = cursor.fetchall()

        return {'results': results}


# Backwards compatibility alias
GTAAPIClient = GTADatabaseClient
