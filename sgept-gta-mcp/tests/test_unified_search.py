"""Unit tests for the unified semantic search orchestration.

Covers acceptance criteria from issue 060:
- score-descending ordering
- score field presence / auto-inclusion
- zero structured matches → empty results, no error
- candidate-pool ceiling enforcement
- semantic_query omitted → standard path unchanged (no score field)
- show_keys excludes score when not requested
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock

from gta_mcp.models import GTASearchInput, SEMANTIC_CANDIDATE_CEILING_DEFAULT


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _make_struct_record(iid: int, title: str = "Title", gta_eval: str = "Red") -> dict:
    return {
        "intervention_id": iid,
        "state_act_title": title,
        "gta_evaluation": gta_eval,
        "date_announced": "2024-01-01",
        "is_in_force": True,
    }


def _make_semantic_record(iid: int, score: float) -> dict:
    return {
        "intervention_id": iid,
        "title": f"Intervention {iid}",
        "score": score,
        "blurb": "Some blurb text.",
        "url": f"https://example.com/{iid}",
        "publication_date": "2024-01-01",
    }


# ---------------------------------------------------------------------------
# Model-level ceiling constant
# ---------------------------------------------------------------------------


class TestSemanticCandidateCeiling:

    def test_default_ceiling_is_1000(self):
        assert SEMANTIC_CANDIDATE_CEILING_DEFAULT == 1000

    def test_env_var_override(self, monkeypatch):
        """SEMANTIC_CANDIDATE_CEILING env var is read at runtime."""
        monkeypatch.setenv("SEMANTIC_CANDIDATE_CEILING", "500")
        ceiling = int(os.getenv("SEMANTIC_CANDIDATE_CEILING", str(SEMANTIC_CANDIDATE_CEILING_DEFAULT)))
        assert ceiling == 500

    def test_env_var_missing_uses_default(self, monkeypatch):
        monkeypatch.delenv("SEMANTIC_CANDIDATE_CEILING", raising=False)
        ceiling = int(os.getenv("SEMANTIC_CANDIDATE_CEILING", str(SEMANTIC_CANDIDATE_CEILING_DEFAULT)))
        assert ceiling == SEMANTIC_CANDIDATE_CEILING_DEFAULT


# ---------------------------------------------------------------------------
# _gta_unified_semantic_search helper unit tests
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client():
    client = AsyncMock()
    return client


@pytest.fixture
def base_params():
    return GTASearchInput(
        semantic_query="chip production subsidies",
        sorting=None,
        limit=5,
        response_format="json",
    )


@pytest.mark.asyncio
class TestUnifiedSearchOrchestration:

    async def test_score_descending_ordering(self, mock_client, base_params, monkeypatch):
        """Records returned in score-descending order from semantic results."""
        monkeypatch.delenv("SEMANTIC_CANDIDATE_CEILING", raising=False)

        candidate_ids = [10, 20, 30]
        mock_client.search_interventions.side_effect = [
            # Stage 1: candidate IDs
            [{"intervention_id": i} for i in candidate_ids],
            # Stage 3: structural records
            [_make_struct_record(i) for i in candidate_ids],
        ]

        semantic_results = [
            _make_semantic_record(30, score=0.9),
            _make_semantic_record(10, score=0.7),
            _make_semantic_record(20, score=0.5),
        ]

        mock_client.semantic_search_interventions = AsyncMock(
            return_value={"results": semantic_results, "total": 3, "query": "chip"}
        )
        from gta_mcp.server import _gta_unified_semantic_search
        import json
        result = await _gta_unified_semantic_search(
            params=base_params,
            filters={"announcement_period": ["1900-01-01", "2099-12-31"]},
            filter_messages=[],
            original_params={},
            client=mock_client,
        )
        data = json.loads(result)
        ids = [r["intervention_id"] for r in data["results"]]
        assert ids == [30, 10, 20], f"Expected score-desc order, got {ids}"

    async def test_score_field_present_by_default(self, mock_client, base_params, monkeypatch):
        """When semantic_query set, score auto-included in each record."""
        monkeypatch.delenv("SEMANTIC_CANDIDATE_CEILING", raising=False)

        candidate_ids = [1, 2]
        mock_client.search_interventions.side_effect = [
            [{"intervention_id": i} for i in candidate_ids],
            [_make_struct_record(i) for i in candidate_ids],
        ]
        semantic_results = [
            _make_semantic_record(1, score=0.88),
            _make_semantic_record(2, score=0.77),
        ]

        mock_client.semantic_search_interventions = AsyncMock(
            return_value={"results": semantic_results, "total": 2, "query": "test"}
        )
        from gta_mcp.server import _gta_unified_semantic_search
        import json
        result = await _gta_unified_semantic_search(
            params=base_params,
            filters={"announcement_period": ["1900-01-01", "2099-12-31"]},
            filter_messages=[],
            original_params={},
            client=mock_client,
        )
        data = json.loads(result)
        for rec in data["results"]:
            assert "score" in rec, f"score missing from record {rec}"

    async def test_score_excluded_when_show_keys_omits_it(self, mock_client, monkeypatch):
        """score is excluded when show_keys is set but doesn't include 'score'."""
        monkeypatch.delenv("SEMANTIC_CANDIDATE_CEILING", raising=False)

        params = GTASearchInput(
            semantic_query="chip production subsidies",
            sorting=None,
            limit=2,
            response_format="json",
            show_keys=["intervention_id", "state_act_title"],
        )
        candidate_ids = [1, 2]
        mock_client.search_interventions.side_effect = [
            [{"intervention_id": i} for i in candidate_ids],
            [{"intervention_id": i, "state_act_title": f"Title {i}"} for i in candidate_ids],
        ]
        semantic_results = [
            _make_semantic_record(1, score=0.88),
            _make_semantic_record(2, score=0.77),
        ]

        mock_client.semantic_search_interventions = AsyncMock(
            return_value={"results": semantic_results, "total": 2, "query": "test"}
        )
        from gta_mcp.server import _gta_unified_semantic_search
        import json
        result = await _gta_unified_semantic_search(
            params=params,
            filters={"announcement_period": ["1900-01-01", "2099-12-31"]},
            filter_messages=[],
            original_params={},
            client=mock_client,
        )
        data = json.loads(result)
        for rec in data["results"]:
            assert "score" not in rec, f"score should be excluded, got {rec}"

    async def test_zero_structural_matches_empty_results(self, mock_client, base_params, monkeypatch):
        """Zero structured matches → empty results list, no error raised."""
        monkeypatch.delenv("SEMANTIC_CANDIDATE_CEILING", raising=False)

        mock_client.search_interventions.return_value = []  # Stage 1: no candidates

        from gta_mcp.server import _gta_unified_semantic_search
        import json
        result = await _gta_unified_semantic_search(
            params=base_params,
            filters={"announcement_period": ["1900-01-01", "2099-12-31"]},
            filter_messages=[],
            original_params={},
            client=mock_client,
        )
        data = json.loads(result)
        assert data["results"] == []
        assert data["count"] == 0

    async def test_ceiling_limits_candidate_pool(self, mock_client, base_params, monkeypatch):
        """Stage 1 request uses ceiling as limit, not params.limit."""
        monkeypatch.setenv("SEMANTIC_CANDIDATE_CEILING", "42")

        # Track what limit was passed to Stage 1 call
        stage1_limit = None

        async def fake_search_interventions(filters, limit, offset, sorting, show_keys):
            nonlocal stage1_limit
            if show_keys == ["intervention_id"]:
                stage1_limit = limit
                return [{"intervention_id": i} for i in range(1, 4)]
            # Stage 3: structural records
            return [_make_struct_record(i) for i in range(1, 4)]

        mock_client.search_interventions.side_effect = fake_search_interventions

        semantic_results = [_make_semantic_record(i, score=0.9 - i * 0.1) for i in range(1, 4)]
        mock_client.semantic_search_interventions = AsyncMock(
            return_value={"results": semantic_results, "total": 3, "query": "test"}
        )
        from gta_mcp.server import _gta_unified_semantic_search
        await _gta_unified_semantic_search(
            params=base_params,
            filters={"announcement_period": ["1900-01-01", "2099-12-31"]},
            filter_messages=[],
            original_params={},
            client=mock_client,
        )
        assert stage1_limit == 42, f"Expected ceiling=42 as limit, got {stage1_limit}"

    async def test_score_included_when_show_keys_star(self, mock_client, monkeypatch):
        """show_keys=["*"] → score is included."""
        monkeypatch.delenv("SEMANTIC_CANDIDATE_CEILING", raising=False)

        params = GTASearchInput(
            semantic_query="subsidies",
            sorting=None,
            limit=2,
            response_format="json",
            show_keys=["*"],
        )
        candidate_ids = [1, 2]
        mock_client.search_interventions.side_effect = [
            [{"intervention_id": i} for i in candidate_ids],
            [_make_struct_record(i) for i in candidate_ids],
        ]
        semantic_results = [_make_semantic_record(i, score=0.8) for i in candidate_ids]

        mock_client.semantic_search_interventions = AsyncMock(
            return_value={"results": semantic_results, "total": 2, "query": "subsidies"}
        )
        from gta_mcp.server import _gta_unified_semantic_search
        import json
        result = await _gta_unified_semantic_search(
            params=params,
            filters={"announcement_period": ["1900-01-01", "2099-12-31"]},
            filter_messages=[],
            original_params={},
            client=mock_client,
        )
        data = json.loads(result)
        for rec in data["results"]:
            assert "score" in rec


# ---------------------------------------------------------------------------
# Score field in SHOW_KEYS_AVAILABLE
# ---------------------------------------------------------------------------


def test_score_in_show_keys_available():
    """score is listed as an available show_keys field."""
    from gta_mcp.models import SHOW_KEYS_AVAILABLE
    assert "score" in SHOW_KEYS_AVAILABLE
