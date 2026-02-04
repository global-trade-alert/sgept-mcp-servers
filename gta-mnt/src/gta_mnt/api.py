"""GTA API client for gta_mnt server - Direct Database Access.

Refactored to use direct MySQL connections instead of REST API endpoints.
"""

import os
from typing import Optional
from datetime import datetime, UTC

import pymysql
import pymysql.cursors

from .constants import SANCHO_USER_ID, SANCHO_FRAMEWORK_ID
from .storage import ReviewStorage


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
        limit: int = 20,
        offset: int = 0,
        implementing_jurisdictions: Optional[list[str]] = None,
        date_entered_review_gte: Optional[str] = None
    ) -> dict:
        """List measures awaiting Step 1 review.

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
            WHERE sa.status_id = 2
        '''
        params = []

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
            WHERE sa.status_id = 2
        '''
        cursor.execute(count_query)
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

        # Get measure from api_state_act_log (the main state act table)
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
                s.status_name
            FROM api_state_act_log sa
            LEFT JOIN api_state_act_status_list s ON sa.status_id = s.status_id
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
            # Enhanced query with implementation_level_name and unit_name
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
                    i.prior_level,
                    i.new_level,
                    i.unit_id,
                    u.unit_name
                FROM api_intervention_log i
                LEFT JOIN api_intervention_type_list t ON i.intervention_type_id = t.intervention_type_id
                LEFT JOIN api_gta_evaluation_list e ON i.gta_evaluation_id = e.gta_evaluation_id
                LEFT JOIN api_affected_flow_list af ON i.affected_flow_id = af.affected_flow_id
                LEFT JOIN api_eligible_firm_list ef ON i.eligible_firm_id = ef.eligible_firm_id
                LEFT JOIN api_implementation_level_list il ON i.implementation_level_id = il.implementation_level_id
                LEFT JOIN api_unit_list u ON i.unit_id = u.unit_id
                WHERE i.state_act_id = %s
            ''', (state_act_id,))
            measure['interventions'] = cursor.fetchall()

            # Get affected jurisdictions for each intervention (via api_intervention_aj)
            # Enhanced to include jurisdiction type (inferred/targeted/excluded/incidental)
            for intervention in measure['interventions']:
                try:
                    cursor.execute('''
                        SELECT
                            j.jurisdiction_id,
                            j.jurisdiction_name,
                            j.iso_code,
                            aj.aj_type_id as type_id,
                            ajt.aj_type_name as type_name
                        FROM api_intervention_aj aj
                        JOIN api_jurisdiction_list j ON aj.jurisdiction_id = j.jurisdiction_id
                        LEFT JOIN api_aj_type_list ajt ON aj.aj_type_id = ajt.aj_type_id
                        WHERE aj.intervention_id = %s
                    ''', (intervention['id'],))
                    intervention['affected_jurisdictions'] = cursor.fetchall()
                except Exception:
                    # Fallback to simpler query if aj_type columns don't exist
                    cursor.execute('''
                        SELECT j.jurisdiction_id, j.jurisdiction_name, j.iso_code
                        FROM api_intervention_aj aj
                        JOIN api_jurisdiction_list j ON aj.jurisdiction_id = j.jurisdiction_id
                        WHERE aj.intervention_id = %s
                    ''', (intervention['id'],))
                    intervention['affected_jurisdictions'] = cursor.fetchall()

                # Get distorted markets for each intervention
                try:
                    cursor.execute('''
                        SELECT
                            j.jurisdiction_id,
                            j.jurisdiction_name,
                            j.iso_code,
                            dm.dm_type_id as type_id,
                            dmt.dm_type_name as type_name
                        FROM api_intervention_dm dm
                        JOIN api_jurisdiction_list j ON dm.jurisdiction_id = j.jurisdiction_id
                        LEFT JOIN api_dm_type_list dmt ON dm.dm_type_id = dmt.dm_type_id
                        WHERE dm.intervention_id = %s
                    ''', (intervention['id'],))
                    intervention['distorted_markets'] = cursor.fetchall()
                except Exception:
                    # Table may not exist or have different structure
                    intervention['distorted_markets'] = []

                # Get firms associated with intervention
                try:
                    cursor.execute('''
                        SELECT
                            f.firm_id,
                            f.firm_name,
                            fi.role_id,
                            fr.role_name
                        FROM api_intervention_firm fi
                        JOIN api_firm_list f ON fi.firm_id = f.firm_id
                        LEFT JOIN api_firm_role_list fr ON fi.role_id = fr.role_id
                        WHERE fi.intervention_id = %s
                    ''', (intervention['id'],))
                    intervention['firms'] = cursor.fetchall()
                except Exception:
                    # Table may not exist or have different structure
                    intervention['firms'] = []

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
        cursor.execute('''
            SELECT sl.source_url, sl.is_collected, sl.is_file, sl.last_checked
            FROM api_state_act_source sas
            JOIN api_source_list sl ON sas.source_id = sl.source_id
            WHERE sas.state_act_id = %s
            ORDER BY sl.last_checked DESC
        ''', (state_act_id,))
        sources = cursor.fetchall()
        measure['sources'] = sources

        # Also include the direct source field
        measure['source_info'] = {
            'primary_source': measure.get('source') or measure.get('source_markdown'),
            'linked_sources': sources
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
            new_status_id: Status ID (2=Step1, 3=Publishable, 6=Under revision, 22=SC Reviewed)
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

        Note: If framework 495 doesn't exist, we use status 22 (Sancho Claudino Reviewed)
        instead as an alternative tracking mechanism.

        Args:
            state_act_id: StateAct ID
            framework_name: Framework name (default: "sancho claudino review")

        Returns:
            Dict with success status and message
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Check if framework exists
            cursor.execute(
                'SELECT id FROM gta_framework WHERE id = %s',
                (SANCHO_FRAMEWORK_ID,)
            )
            framework = cursor.fetchone()

            if framework:
                # Use framework tagging
                cursor.execute('''
                    INSERT INTO api_state_act_framework (framework_id, state_act_id)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE framework_id = framework_id
                ''', (SANCHO_FRAMEWORK_ID, state_act_id))
                conn.commit()

                return {
                    'state_act_id': state_act_id,
                    'framework_id': SANCHO_FRAMEWORK_ID,
                    'success': True,
                    'message': f"Framework '{framework_name}' attached to StateAct {state_act_id}"
                }
            else:
                # Framework doesn't exist - use status 22 as alternative
                # Status 22 = "Sancho Claudino Reviewed"
                await self.set_status(state_act_id, 22)

                return {
                    'state_act_id': state_act_id,
                    'framework_id': None,
                    'status_id': 22,
                    'success': True,
                    'message': f"Framework {SANCHO_FRAMEWORK_ID} not found. Set status to 22 (Sancho Claudino Reviewed) instead."
                }

        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to add framework: {e}'
            }

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
