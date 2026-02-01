"""Unit tests for GTA API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from gta_mnt.api import GTAAPIClient
from gta_mnt.auth import JWTAuthManager
from gta_mnt.constants import SANCHO_USER_ID, SANCHO_FRAMEWORK_ID


@pytest.fixture
def mock_auth():
    """Mock JWTAuthManager."""
    auth = MagicMock(spec=JWTAuthManager)
    auth.get_token = AsyncMock(return_value="mock-jwt-token")
    return auth


@pytest.fixture
def api_client(mock_auth):
    """Create GTAAPIClient with mocked auth."""
    return GTAAPIClient(mock_auth)


@pytest.mark.asyncio
async def test_list_step1_queue_basic(api_client):
    """Test list_step1_queue with default parameters."""
    mock_response = {
        "results": [
            {"id": 123, "title": "Test Measure", "status_time": "2026-02-01"}
        ],
        "count": 1
    }

    with patch.object(api_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=MagicMock(
            json=lambda: mock_response,
            raise_for_status=MagicMock()
        ))
        mock_get_client.return_value = mock_client

        result = await api_client.list_step1_queue(limit=20, offset=0)

        assert result == mock_response
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/api/state-acts/"
        assert call_args[1]["params"]["status_id"] == 2
        assert call_args[1]["params"]["limit"] == 20


@pytest.mark.asyncio
async def test_list_step1_queue_with_filters(api_client):
    """Test list_step1_queue with jurisdiction and date filters."""
    mock_response = {"results": [], "count": 0}

    with patch.object(api_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=MagicMock(
            json=lambda: mock_response,
            raise_for_status=MagicMock()
        ))
        mock_get_client.return_value = mock_client

        await api_client.list_step1_queue(
            implementing_jurisdictions=["USA", "CHN"],
            date_entered_review_gte="2026-01-01"
        )

        call_args = mock_client.get.call_args[1]["params"]
        assert call_args["implementing_jurisdiction__in"] == "USA,CHN"
        assert call_args["status_time__gte"] == "2026-01-01"


@pytest.mark.asyncio
async def test_get_measure_with_interventions_and_comments(api_client):
    """Test get_measure fetches interventions and comments when requested."""
    measure_data = {"id": 123, "title": "Test Measure"}
    interventions_data = {"results": [{"id": 1, "intervention_type": "Tariff"}]}
    comments_data = {"results": [{"id": 1, "text": "Test comment"}]}

    with patch.object(api_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        # Mock three sequential GET calls
        mock_responses = [
            MagicMock(json=lambda: measure_data, raise_for_status=MagicMock()),
            MagicMock(json=lambda: interventions_data, raise_for_status=MagicMock()),
            MagicMock(json=lambda: comments_data, raise_for_status=MagicMock())
        ]
        mock_client.get = AsyncMock(side_effect=mock_responses)
        mock_get_client.return_value = mock_client

        result = await api_client.get_measure(
            state_act_id=123,
            include_interventions=True,
            include_comments=True
        )

        assert result["id"] == 123
        assert "interventions" in result
        assert len(result["interventions"]) == 1
        assert "comments" in result
        assert len(result["comments"]) == 1


@pytest.mark.asyncio
async def test_get_measure_without_nested_data(api_client):
    """Test get_measure skips interventions/comments when not requested."""
    measure_data = {"id": 123, "title": "Test Measure"}

    with patch.object(api_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=MagicMock(
            json=lambda: measure_data,
            raise_for_status=MagicMock()
        ))
        mock_get_client.return_value = mock_client

        result = await api_client.get_measure(
            state_act_id=123,
            include_interventions=False,
            include_comments=False
        )

        # Should only call GET once (for measure, not interventions/comments)
        assert mock_client.get.call_count == 1
        assert "interventions" not in result
        assert "comments" not in result


@pytest.mark.asyncio
async def test_set_status_creates_log_entry(api_client):
    """Test set_status updates measure and creates status log."""
    with patch.object(api_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.patch = AsyncMock(return_value=MagicMock(
            raise_for_status=MagicMock()
        ))
        mock_client.post = AsyncMock(return_value=MagicMock(
            raise_for_status=MagicMock()
        ))
        mock_get_client.return_value = mock_client

        result = await api_client.set_status(
            state_act_id=123,
            new_status_id=6,
            comment="Under revision due to critical issues"
        )

        # Verify PATCH to update status
        mock_client.patch.assert_called_once()
        patch_args = mock_client.patch.call_args
        assert patch_args[0][0] == "/api/state-acts/123/"
        assert patch_args[1]["json"]["status_id"] == 6

        # Verify POST to create log entry
        mock_client.post.assert_called_once()
        post_args = mock_client.post.call_args
        assert post_args[0][0] == "/api/state-act-status-log/"
        assert post_args[1]["json"]["status_id"] == 6
        assert post_args[1]["json"]["comment"] == "Under revision due to critical issues"

        assert result["success"] is True
        assert result["new_status_id"] == 6


@pytest.mark.asyncio
async def test_add_comment_uses_sancho_user_id(api_client):
    """Test add_comment uses SANCHO_USER_ID as author."""
    with patch.object(api_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=MagicMock(
            json=lambda: {"id": 456},
            raise_for_status=MagicMock()
        ))
        mock_get_client.return_value = mock_client

        result = await api_client.add_comment(
            measure_id=123,
            comment_text="Test comment",
            template_id=None
        )

        # Verify user_id in payload
        post_args = mock_client.post.call_args
        assert post_args[1]["json"]["user_id"] == SANCHO_USER_ID
        assert post_args[1]["json"]["comment"] == "Test comment"
        assert result["comment_id"] == 456


@pytest.mark.asyncio
async def test_add_framework_uses_framework_id(api_client):
    """Test add_framework uses SANCHO_FRAMEWORK_ID."""
    with patch.object(api_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=MagicMock(
            raise_for_status=MagicMock()
        ))
        mock_get_client.return_value = mock_client

        result = await api_client.add_framework(state_act_id=123)

        # Verify framework_id in payload
        post_args = mock_client.post.call_args
        assert post_args[0][0] == "/api/state-acts/123/frameworks/"
        assert post_args[1]["json"]["framework_id"] == SANCHO_FRAMEWORK_ID
        assert result["framework_id"] == SANCHO_FRAMEWORK_ID


@pytest.mark.asyncio
async def test_list_templates_excludes_checklist_by_default(api_client):
    """Test list_templates excludes checklist templates by default."""
    mock_response = {"results": [{"id": 1, "name": "Issue template"}]}

    with patch.object(api_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=MagicMock(
            json=lambda: mock_response,
            raise_for_status=MagicMock()
        ))
        mock_get_client.return_value = mock_client

        await api_client.list_templates(include_checklist=False)

        call_args = mock_client.get.call_args[1]["params"]
        assert call_args["exclude_type"] == "checklist"


@pytest.mark.asyncio
async def test_close_client(api_client):
    """Test close method closes httpx client."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    api_client._client = mock_client

    await api_client.close()

    mock_client.aclose.assert_called_once()
    assert api_client._client is None
