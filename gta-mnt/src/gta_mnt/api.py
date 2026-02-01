"""GTA API client for gta_mnt server."""

from typing import Optional
import httpx
from datetime import datetime, UTC

from .auth import JWTAuthManager
from .constants import SANCHO_USER_ID, SANCHO_FRAMEWORK_ID
from .storage import ReviewStorage


class GTAAPIClient:
    """Client for GTA API operations.

    Handles authenticated requests to the GTA Django API for:
    - Measure queries
    - Comment creation
    - Status updates
    - Framework tagging
    """

    BASE_URL = "https://api.globaltradealert.org"

    def __init__(self, auth_manager: JWTAuthManager, storage: Optional[ReviewStorage] = None):
        self.auth = auth_manager
        self._client: Optional[httpx.AsyncClient] = None
        self.storage = storage or ReviewStorage()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx async client with auth headers."""
        if self._client is None:
            token = await self.auth.get_token()
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

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

        Query joins api_state_act with api_state_act_status_log to get accurate
        status_time ordering (most recent first).

        Args:
            limit: Max measures to return (1-100)
            offset: Pagination offset
            implementing_jurisdictions: Filter by jurisdiction codes
            date_entered_review_gte: Filter by date entered review (YYYY-MM-DD)

        Returns:
            Dict with 'results' list and 'count' int
        """
        client = await self._get_client()

        # Build filter params
        params = {
            "status_id": 2,  # Step 1 status
            "limit": limit,
            "offset": offset,
            "ordering": "-status_time"  # Most recent first
        }

        if implementing_jurisdictions:
            params["implementing_jurisdiction__in"] = ",".join(implementing_jurisdictions)

        if date_entered_review_gte:
            params["status_time__gte"] = date_entered_review_gte

        response = await client.get("/api/state-acts/", params=params)
        response.raise_for_status()
        return response.json()

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
        client = await self._get_client()

        # Base measure endpoint
        response = await client.get(f"/api/state-acts/{state_act_id}/")
        response.raise_for_status()
        measure = response.json()

        # Optionally fetch interventions
        if include_interventions:
            int_response = await client.get(
                "/api/interventions/",
                params={"state_act_id": state_act_id}
            )
            int_response.raise_for_status()
            measure["interventions"] = int_response.json().get("results", [])

        # Optionally fetch comments
        if include_comments:
            comment_response = await client.get(
                "/api/comments/",
                params={"state_act_id": state_act_id, "ordering": "-created"}
            )
            comment_response.raise_for_status()
            measure["comments"] = comment_response.json().get("results", [])

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
        client = await self._get_client()

        # Update StateAct status
        payload = {"status_id": new_status_id}
        response = await client.patch(
            f"/api/state-acts/{state_act_id}/",
            json=payload
        )
        response.raise_for_status()

        # Create status log entry
        log_payload = {
            "state_act_id": state_act_id,
            "status_id": new_status_id,
            "comment": comment or f"Status changed to {new_status_id}"
        }
        log_response = await client.post(
            "/api/state-act-status-log/",
            json=log_payload
        )
        log_response.raise_for_status()

        return {
            "success": True,
            "state_act_id": state_act_id,
            "new_status_id": new_status_id,
            "message": "Status updated successfully"
        }

    # ========================================================================
    # WS5: Add Comment (Direct Database Insertion)
    # ========================================================================

    async def add_comment(
        self,
        measure_id: int,
        comment_text: str,
        template_id: Optional[int] = None
    ) -> dict:
        """Add a comment to a StateAct via direct database insertion.

        Note: GTA API has no standalone comment POST endpoint.
        Comments are created via Django ORM direct database access.

        Args:
            measure_id: StateAct ID
            comment_text: Full comment text (structured markdown)
            template_id: Optional template ID for standardized comments

        Returns:
            Dict with comment_id, success status, and message
        """
        client = await self._get_client()

        # Direct database insertion payload
        payload = {
            "state_act_id": measure_id,
            "user_id": SANCHO_USER_ID,  # Sancho Claudino user
            "comment": comment_text,
            "created": datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
            "template_id": template_id
        }

        # Insert comment via Django ORM endpoint
        # Note: This assumes GTA backend has a POST endpoint for api_comment_log
        # If not available, this will need to be a direct SQL INSERT via psycopg2
        response = await client.post(
            "/api/comments/",
            json=payload
        )
        response.raise_for_status()
        result = response.json()

        comment_id = result.get("id", 0)

        # Save comment to persistent storage
        self.storage.save_comment(
            state_act_id=measure_id,
            comment_text=comment_text,
            comment_id=comment_id
        )

        return {
            "comment_id": comment_id,
            "success": True,
            "message": f"Comment added to StateAct {measure_id}"
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

        Args:
            state_act_id: StateAct ID
            framework_name: Framework name (default: "sancho claudino review")

        Returns:
            Dict with success status and message
        """
        client = await self._get_client()

        # Attach framework via M2M relationship
        payload = {
            "state_act_id": state_act_id,
            "framework_id": SANCHO_FRAMEWORK_ID  # "sancho claudino review"
        }

        response = await client.post(
            f"/api/state-acts/{state_act_id}/frameworks/",
            json=payload
        )
        response.raise_for_status()

        return {
            "state_act_id": state_act_id,
            "framework_id": SANCHO_FRAMEWORK_ID,
            "success": True,
            "message": f"Framework '{framework_name}' attached to StateAct {state_act_id}"
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
        client = await self._get_client()

        params = {}
        if not include_checklist:
            params["exclude_type"] = "checklist"

        response = await client.get("/api/comment-templates/", params=params)
        response.raise_for_status()
        return response.json()
