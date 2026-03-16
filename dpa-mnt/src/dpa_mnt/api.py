"""DPA database client for dpa_mnt server - Direct MySQL Access.

All queries use lux_* tables for DPA data.
Comments use gta_comment (the table the Lumière dashboard reads).
Review tracking uses lux_intervention_issue_log (issue 83 = BC review).
"""

import os
from typing import Optional
from datetime import datetime, UTC

import pymysql
import pymysql.cursors

from .constants import (
    SANCHO_USER_ID, DPA_FRAMEWORK_ID, REVIEWER_NAME,
    BUZESSA_REVIEWER_ID, BUZETTA_AUTHOR_ID, AUTHOR_NAME,
    BC_REVIEW_ISSUE_ID
)
from .storage import ReviewStorage


class DPADatabaseClient:
    """Client for DPA database operations via direct MySQL access."""

    def __init__(self, storage: Optional[ReviewStorage] = None):
        self.host = os.getenv('GTA_DB_HOST', 'gtaapi.cp7esvs8xwum.eu-west-1.rds.amazonaws.com')
        self.database = os.getenv('GTA_DB_NAME', 'gtaapi')
        self.port = int(os.getenv('GTA_DB_PORT', '3306'))
        self.user = os.getenv('GTA_DB_USER_WRITE', os.getenv('GTA_DB_USER', 'gtaapi'))
        self.password = os.getenv('GTA_DB_PASSWORD_WRITE', os.getenv('GTA_DB_PASSWORD', ''))
        self.storage = storage or ReviewStorage()
        self._conn: Optional[pymysql.Connection] = None

    _users_ensured: bool = False

    def _get_connection(self) -> pymysql.Connection:
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
            if not DPADatabaseClient._users_ensured:
                self._ensure_automated_users()
                DPADatabaseClient._users_ensured = True
        return self._conn

    def _ensure_automated_users(self) -> None:
        """Create auth_user entries for Buzessa/Buzetta if they don't exist.

        Uses INSERT IGNORE so this is idempotent and safe to call on every connection.
        """
        cursor = self._conn.cursor()
        now = datetime.now(UTC)
        users = [
            (BUZESSA_REVIEWER_ID, 'buzessa_claudini', 'Buzessa', 'Claudini',
             'buzessa.claudini@digitalpolicyalert.org'),
            (BUZETTA_AUTHOR_ID, 'buzetta_claudini', 'Buzetta', 'Claudini',
             'buzetta.claudini@digitalpolicyalert.org'),
        ]
        for user_id, username, first_name, last_name, email in users:
            cursor.execute('''
                INSERT IGNORE INTO auth_user
                    (id, username, first_name, last_name, email, password,
                     is_staff, is_active, is_superuser, date_joined)
                VALUES (%s, %s, %s, %s, %s, '!unusable', 0, 1, 0, %s)
            ''', (user_id, username, first_name, last_name, email, now))
        self._conn.commit()

    def close(self):
        if self._conn and self._conn.open:
            self._conn.close()
            self._conn = None

    # ========================================================================
    # List Review Queue
    # ========================================================================

    async def list_review_queue(
        self,
        limit: int = 20,
        offset: int = 0,
        implementing_jurisdictions: Optional[list[str]] = None,
        date_entered_review_gte: Optional[str] = None
    ) -> dict:
        """List events awaiting review (status_id = 2: AT: in step 1 review).

        Returns events ordered by most recently entering review.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT DISTINCT
                e.event_id,
                e.event_title,
                e.event_date,
                et.event_type_name,
                at2.action_type_name,
                gb.gov_branch_name,
                gbo.gov_body_name,
                esl.date_added as status_time
            FROM lux_event_log e
            JOIN lux_event_status_log esl
                ON e.event_id = esl.event_id AND esl.status_id = 2
            LEFT JOIN lux_event_type_list et ON e.event_type_id = et.event_type_id
            LEFT JOIN lux_action_type_list at2 ON e.action_type_id = at2.action_type_id
            LEFT JOIN lux_government_branch_list gb ON e.gov_branch_id = gb.gov_branch_id
            LEFT JOIN lux_government_body_list gbo ON e.gov_body_id = gbo.gov_body_id
            WHERE e.status_id = 2
        '''
        params = []

        if implementing_jurisdictions:
            placeholders = ', '.join(['%s'] * len(implementing_jurisdictions))
            query += f'''
                AND e.intervention_id IN (
                    SELECT ii.intervention_id
                    FROM lux_intervention_implementer ii
                    JOIN api_jurisdiction_list j ON ii.jurisdiction_id = j.jurisdiction_id
                    WHERE j.iso_code IN ({placeholders})
                )
            '''
            params.extend(implementing_jurisdictions)

        if date_entered_review_gte:
            query += ' AND esl.date_added >= %s'
            params.append(date_entered_review_gte)

        query += ' ORDER BY esl.date_added DESC'
        query += ' LIMIT %s OFFSET %s'
        params.extend([limit, offset])

        cursor.execute(query, params)
        results = cursor.fetchall()

        # Get total count
        count_query = '''
            SELECT COUNT(DISTINCT e.event_id) as count
            FROM lux_event_log e
            WHERE e.status_id = 2
        '''
        cursor.execute(count_query)
        count = cursor.fetchone()['count']

        return {'results': results, 'count': count}

    # ========================================================================
    # Get Event Detail
    # ========================================================================

    async def get_event(
        self,
        event_id: int,
        include_intervention: bool = True,
        include_comments: bool = True
    ) -> dict:
        """Get complete event details with intervention, sources, and comments.

        Multi-query approach: event base, intervention, economic activities,
        implementing jurisdictions, policy areas, development, related
        interventions, sources, and comments.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. Event base
        cursor.execute('''
            SELECT
                e.event_id,
                e.intervention_id,
                e.event_title,
                e.event_description,
                e.event_date,
                e.event_type_id,
                et.event_type_name,
                e.action_type_id,
                at2.action_type_name,
                e.gov_branch_id,
                gb.gov_branch_name,
                e.gov_body_id,
                gbo.gov_body_name,
                e.status_id,
                esl.status_name,
                e.is_case,
                e.is_current
            FROM lux_event_log e
            LEFT JOIN lux_event_type_list et ON e.event_type_id = et.event_type_id
            LEFT JOIN lux_action_type_list at2 ON e.action_type_id = at2.action_type_id
            LEFT JOIN lux_government_branch_list gb ON e.gov_branch_id = gb.gov_branch_id
            LEFT JOIN lux_government_body_list gbo ON e.gov_body_id = gbo.gov_body_id
            LEFT JOIN lux_event_status_list esl ON e.status_id = esl.status_id
            WHERE e.event_id = %s
        ''', (event_id,))
        event = cursor.fetchone()

        if not event:
            return {'error': f'Event {event_id} not found'}

        result = {'event': event}
        intervention_id = event.get('intervention_id')

        # 2. Intervention details
        if include_intervention and intervention_id:
            cursor.execute('''
                SELECT
                    i.intervention_id,
                    i.intervention_title,
                    i.development_id,
                    i.policy_area_id,
                    pa.policy_area_name,
                    i.intervention_type_id,
                    it.intervention_type_name,
                    i.implementation_level_id,
                    il.implementation_level_name,
                    i.current_status_id,
                    cs.current_status_name
                FROM lux_intervention_log i
                LEFT JOIN lux_policy_area_list pa ON i.policy_area_id = pa.policy_area_id
                LEFT JOIN lux_intervention_type_list it ON i.intervention_type_id = it.intervention_type_id
                LEFT JOIN lux_implementation_level_list il ON i.implementation_level_id = il.implementation_level_id
                LEFT JOIN lux_current_status_list cs ON i.current_status_id = cs.current_status_id
                WHERE i.intervention_id = %s
            ''', (intervention_id,))
            result['intervention'] = cursor.fetchone() or {}

            # 3. Economic activities
            cursor.execute('''
                SELECT ea.economic_activity_id, eal.economic_activity_name
                FROM lux_intervention_econ_activity ea
                JOIN lux_economic_activity_list eal ON ea.economic_activity_id = eal.economic_activity_id
                WHERE ea.intervention_id = %s
            ''', (intervention_id,))
            result['economic_activities'] = cursor.fetchall()

            # 4. Implementing jurisdictions
            cursor.execute('''
                SELECT j.jurisdiction_id, j.jurisdiction_name, j.iso_code
                FROM lux_intervention_implementer ii
                JOIN api_jurisdiction_list j ON ii.jurisdiction_id = j.jurisdiction_id
                WHERE ii.intervention_id = %s
            ''', (intervention_id,))
            result['implementing_jurisdictions'] = cursor.fetchall()

            # 5. Additional policy areas
            cursor.execute('''
                SELECT pa.policy_area_id, pa.policy_area_name
                FROM lux_intervention_policy_area ipa
                JOIN lux_policy_area_list pa ON ipa.policy_area_id = pa.policy_area_id
                WHERE ipa.intervention_id = %s
            ''', (intervention_id,))
            result['policy_areas'] = cursor.fetchall()

            # 6. Development
            development_id = result.get('intervention', {}).get('development_id')
            if development_id:
                cursor.execute('''
                    SELECT development_id, development_name
                    FROM lux_development_log
                    WHERE development_id = %s
                ''', (development_id,))
                result['development'] = cursor.fetchone() or {}
            else:
                result['development'] = {}

            # 7. Related interventions
            cursor.execute('''
                SELECT
                    ri.intervention_id_2 as related_intervention_id,
                    i.intervention_title,
                    ri.relation_id,
                    rl.relation_name as relationship_name
                FROM lux_related_intervention_log ri
                JOIN lux_intervention_log i ON ri.intervention_id_2 = i.intervention_id
                LEFT JOIN lux_relationship_list rl ON ri.relation_id = rl.relation_id
                WHERE ri.intervention_id_1 = %s
            ''', (intervention_id,))
            related1 = cursor.fetchall()

            cursor.execute('''
                SELECT
                    ri.intervention_id_1 as related_intervention_id,
                    i.intervention_title,
                    ri.relation_id,
                    rl.relation_name as relationship_name
                FROM lux_related_intervention_log ri
                JOIN lux_intervention_log i ON ri.intervention_id_1 = i.intervention_id
                LEFT JOIN lux_relationship_list rl ON ri.relation_id = rl.relation_id
                WHERE ri.intervention_id_2 = %s
            ''', (intervention_id,))
            related2 = cursor.fetchall()

            result['related_interventions'] = related1 + related2
        else:
            result['intervention'] = {}
            result['economic_activities'] = []
            result['implementing_jurisdictions'] = []
            result['policy_areas'] = []
            result['development'] = {}
            result['related_interventions'] = []

        # 8. Sources (via lux_event_source → lux_source_log, with file info)
        # display_on_flag: 1 = primary source shown on front page, 0 = background/contextual
        cursor.execute('''
            SELECT
                s.source_id,
                s.source_name,
                s.source_url,
                s.source_type_id,
                st.source_type_name,
                s.institution_name,
                s.source_date,
                es.display_on_flag,
                f.file_url,
                f.file_name
            FROM lux_event_source es
            JOIN lux_source_log s ON es.source_id = s.source_id
            LEFT JOIN lux_source_type_list st ON s.source_type_id = st.source_type_id
            LEFT JOIN lux_source_file sf ON s.source_id = sf.source_id
            LEFT JOIN lux_file_log f ON sf.file_id = f.id AND f.is_deleted = 0
            WHERE es.event_id = %s
            ORDER BY es.display_on_flag DESC, s.source_id ASC
        ''', (event_id,))
        result['sources'] = cursor.fetchall()

        # 9. Comments (shared api_comment_log, measure_id = event_id)
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
            ''', (event_id,))
            result['comments'] = cursor.fetchall()
        else:
            result['comments'] = []

        return result

    # ========================================================================
    # Add Comment
    # ========================================================================

    async def add_comment(
        self,
        event_id: int,
        comment_text: str,
        template_id: Optional[int] = None
    ) -> dict:
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Look up intervention_id for storage path
            cursor.execute(
                'SELECT intervention_id FROM lux_event_log WHERE event_id = %s',
                (event_id,)
            )
            row = cursor.fetchone()
            intervention_id = row['intervention_id'] if row else None

            now = datetime.now(UTC)
            cursor.execute('''
                INSERT INTO api_comment_log
                    (author_id, measure_id, comment_value, creation_time, updated_at, comment_visible, comment_template_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (SANCHO_USER_ID, event_id, comment_text, now, now, 1, template_id))

            conn.commit()
            comment_id = cursor.lastrowid

            if intervention_id:
                self.storage.save_comment(
                    intervention_id=intervention_id,
                    event_id=event_id,
                    comment_text=comment_text,
                    comment_id=comment_id
                )

            return {
                'comment_id': comment_id,
                'success': True,
                'message': f'Comment added to event {event_id}'
            }

        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to add comment: {e}'
            }

    # ========================================================================
    # Set Status
    # ========================================================================

    async def set_status(
        self,
        event_id: int,
        new_status_id: int,
        comment: Optional[str] = None
    ) -> dict:
        """Update event status in lux_event_log and log to lux_event_status_log."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'UPDATE lux_event_log SET status_id = %s WHERE event_id = %s',
                (new_status_id, event_id)
            )

            cursor.execute('''
                INSERT INTO lux_event_status_log
                    (event_id, status_id, user_id, date_added)
                VALUES (%s, %s, %s, %s)
            ''', (event_id, new_status_id, SANCHO_USER_ID, datetime.now(UTC)))

            conn.commit()

            return {
                'success': True,
                'event_id': event_id,
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
    # Add Framework
    # ========================================================================

    async def add_review_tag(
        self,
        event_id: int
    ) -> dict:
        """Tag the intervention with 'BC review' issue after reviewing an event.

        Looks up the intervention_id from the event, then inserts into
        lux_intervention_issue_log if not already present. This tracks
        which interventions have had at least one event reviewed.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get intervention_id from event
            cursor.execute(
                'SELECT intervention_id FROM lux_event_log WHERE event_id = %s',
                (event_id,)
            )
            row = cursor.fetchone()
            if not row or not row.get('intervention_id'):
                return {
                    'success': False,
                    'message': f'Event {event_id} not found or has no intervention_id'
                }

            intervention_id = row['intervention_id']

            # Check if already tagged
            cursor.execute('''
                SELECT id FROM lux_intervention_issue_log
                WHERE intervention_id = %s AND issue_id = %s
            ''', (intervention_id, BC_REVIEW_ISSUE_ID))

            if cursor.fetchone():
                return {
                    'event_id': event_id,
                    'intervention_id': intervention_id,
                    'issue_id': BC_REVIEW_ISSUE_ID,
                    'success': True,
                    'message': f"Intervention {intervention_id} already tagged with BC review (issue {BC_REVIEW_ISSUE_ID})"
                }

            # Insert issue tag
            cursor.execute('''
                INSERT INTO lux_intervention_issue_log (intervention_id, issue_id)
                VALUES (%s, %s)
            ''', (intervention_id, BC_REVIEW_ISSUE_ID))

            conn.commit()

            return {
                'event_id': event_id,
                'intervention_id': intervention_id,
                'issue_id': BC_REVIEW_ISSUE_ID,
                'success': True,
                'message': f"Intervention {intervention_id} tagged with BC review (issue {BC_REVIEW_ISSUE_ID})"
            }

        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to add review tag: {e}'
            }

    # ========================================================================
    # Get Intervention Context
    # ========================================================================

    async def get_intervention_context(
        self,
        intervention_id: int
    ) -> dict:
        """Get all events on an intervention for lifecycle and consistency review.

        Returns the intervention metadata plus all events ordered by date,
        with status information to distinguish published (verified context)
        from in-review events. This is the mandatory first step before
        reviewing any individual event.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Intervention metadata
        cursor.execute('''
            SELECT
                i.intervention_id,
                i.intervention_title,
                i.development_id,
                i.policy_area_id,
                pa.policy_area_name,
                i.intervention_type_id,
                it.intervention_type_name,
                i.implementation_level_id,
                il.implementation_level_name,
                i.current_status_id,
                cs.current_status_name
            FROM lux_intervention_log i
            LEFT JOIN lux_policy_area_list pa ON i.policy_area_id = pa.policy_area_id
            LEFT JOIN lux_intervention_type_list it ON i.intervention_type_id = it.intervention_type_id
            LEFT JOIN lux_implementation_level_list il ON i.implementation_level_id = il.implementation_level_id
            LEFT JOIN lux_current_status_list cs ON i.current_status_id = cs.current_status_id
            WHERE i.intervention_id = %s
        ''', (intervention_id,))
        intervention = cursor.fetchone()

        if not intervention:
            return {'error': f'Intervention {intervention_id} not found'}

        # Development name
        development = {}
        dev_id = intervention.get('development_id')
        if dev_id:
            cursor.execute(
                'SELECT development_id, development_name FROM lux_development_log WHERE development_id = %s',
                (dev_id,)
            )
            development = cursor.fetchone() or {}

        # Implementing jurisdictions
        cursor.execute('''
            SELECT j.jurisdiction_id, j.jurisdiction_name, j.iso_code
            FROM lux_intervention_implementer ii
            JOIN api_jurisdiction_list j ON ii.jurisdiction_id = j.jurisdiction_id
            WHERE ii.intervention_id = %s
        ''', (intervention_id,))
        implementers = cursor.fetchall()

        # Economic activities
        cursor.execute('''
            SELECT ea.economic_activity_id, eal.economic_activity_name
            FROM lux_intervention_econ_activity ea
            JOIN lux_economic_activity_list eal ON ea.economic_activity_id = eal.economic_activity_id
            WHERE ea.intervention_id = %s
        ''', (intervention_id,))
        econ_activities = cursor.fetchall()

        # All events on this intervention, ordered by date
        cursor.execute('''
            SELECT
                e.event_id,
                e.event_title,
                e.event_description,
                e.event_date,
                e.event_type_id,
                et.event_type_name,
                e.action_type_id,
                at2.action_type_name,
                e.gov_branch_id,
                gb.gov_branch_name,
                e.gov_body_id,
                gbo.gov_body_name,
                e.status_id,
                esl.status_name,
                e.is_case,
                e.is_current
            FROM lux_event_log e
            LEFT JOIN lux_event_type_list et ON e.event_type_id = et.event_type_id
            LEFT JOIN lux_action_type_list at2 ON e.action_type_id = at2.action_type_id
            LEFT JOIN lux_government_branch_list gb ON e.gov_branch_id = gb.gov_branch_id
            LEFT JOIN lux_government_body_list gbo ON e.gov_body_id = gbo.gov_body_id
            LEFT JOIN lux_event_status_list esl ON e.status_id = esl.status_id
            WHERE e.intervention_id = %s
            ORDER BY e.event_date ASC, e.event_id ASC
        ''', (intervention_id,))
        events = cursor.fetchall()

        # Related interventions
        cursor.execute('''
            SELECT
                ri.intervention_id_2 as related_intervention_id,
                i.intervention_title,
                ri.relation_id,
                rl.relation_name as relationship_name
            FROM lux_related_intervention_log ri
            JOIN lux_intervention_log i ON ri.intervention_id_2 = i.intervention_id
            LEFT JOIN lux_relationship_list rl ON ri.relation_id = rl.relation_id
            WHERE ri.intervention_id_1 = %s
        ''', (intervention_id,))
        related1 = cursor.fetchall()

        cursor.execute('''
            SELECT
                ri.intervention_id_1 as related_intervention_id,
                i.intervention_title,
                ri.relation_id,
                rl.relation_name as relationship_name
            FROM lux_related_intervention_log ri
            JOIN lux_intervention_log i ON ri.intervention_id_1 = i.intervention_id
            LEFT JOIN lux_relationship_list rl ON ri.relation_id = rl.relation_id
            WHERE ri.intervention_id_2 = %s
        ''', (intervention_id,))
        related2 = cursor.fetchall()

        return {
            'intervention': intervention,
            'development': development,
            'implementing_jurisdictions': implementers,
            'economic_activities': econ_activities,
            'events': events,
            'related_interventions': related1 + related2
        }

    # ========================================================================
    # List Templates
    # ========================================================================

    async def list_templates(
        self,
        include_checklist: bool = False
    ) -> dict:
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
