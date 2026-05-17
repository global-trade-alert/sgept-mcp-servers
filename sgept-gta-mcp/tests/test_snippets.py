"""Tests for include_matched_snippets on gta_search_interventions.

Covers acceptance criteria from issue 061:
- GTASearchInput accepts include_matched_snippets: bool = False
- With semantic_query + flag=True, every returned record has matched_snippets
- Without semantic_query, flag is a no-op (no snippets, no error)
- Flag=False (default) → matched_snippets absent (pre-existing callers byte-identical)
- Snippets forwarded through semantic_search_interventions to danswer
- Markdown and JSON response_format both render snippets
- Tool description documents the semantic_query dependency
- show_keys exclusion: matched_snippets excluded from GTA API struct_show_keys
"""

import json
import pytest
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError

from gta_mcp.models import GTASearchInput, SHOW_KEYS_AVAILABLE, _SYNTHETIC_SHOW_KEYS
from gta_mcp.formatters import format_interventions_markdown, format_interventions_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_struct_record(iid: int) -> dict:
    return {
        "intervention_id": iid,
        "state_act_title": f"Act {iid}",
        "gta_evaluation": "Red",
        "date_announced": "2024-06-01",
        "is_in_force": True,
    }


def _make_semantic_record(iid: int, score: float, snippets=None) -> dict:
    rec = {
        "intervention_id": iid,
        "title": f"Intervention {iid}",
        "score": score,
        "blurb": "Some blurb.",
        "url": f"https://example.com/{iid}",
        "publication_date": "2024-06-01",
    }
    if snippets is not None:
        rec["matched_snippets"] = snippets
    return rec


# ---------------------------------------------------------------------------
# Model validation
# ---------------------------------------------------------------------------


class TestIncludeMatchedSnippetsModel:

    def test_default_false(self):
        m = GTASearchInput(sorting=None)
        assert m.include_matched_snippets is False

    def test_set_true(self):
        m = GTASearchInput(
            semantic_query="export controls",
            sorting=None,
            include_matched_snippets=True,
        )
        assert m.include_matched_snippets is True

    def test_set_false_explicit(self):
        m = GTASearchInput(sorting=None, include_matched_snippets=False)
        assert m.include_matched_snippets is False

    def test_extra_fields_still_rejected(self):
        with pytest.raises(ValidationError):
            GTASearchInput(sorting=None, nonexistent_field=True)

    def test_matched_snippets_in_show_keys_available(self):
        assert "matched_snippets" in SHOW_KEYS_AVAILABLE

    def test_matched_snippets_in_synthetic_keys(self):
        assert "matched_snippets" in _SYNTHETIC_SHOW_KEYS

    def test_score_still_in_synthetic_keys(self):
        assert "score" in _SYNTHETIC_SHOW_KEYS


# ---------------------------------------------------------------------------
# Unified search with snippets
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client():
    return AsyncMock()


@pytest.mark.asyncio
class TestUnifiedSearchSnippets:

    async def test_snippets_present_when_flag_true(self, mock_client, monkeypatch):
        """With semantic_query + flag=True, every record has matched_snippets."""
        monkeypatch.delenv("SEMANTIC_CANDIDATE_CEILING", raising=False)

        candidate_ids = [1, 2]
        mock_client.search_interventions.side_effect = [
            [{"intervention_id": i} for i in candidate_ids],
            [_make_struct_record(i) for i in candidate_ids],
        ]
        semantic_results = [
            _make_semantic_record(1, 0.9, snippets=["This measure restricts exports."]),
            _make_semantic_record(2, 0.8, snippets=["The subsidy targets semiconductors."]),
        ]

        params = GTASearchInput(
            semantic_query="export restrictions",
            sorting=None,
            limit=2,
            response_format="json",
            include_matched_snippets=True,
        )

        with patch("gta_mcp.server.semantic_search_interventions", new=AsyncMock(
            return_value={"results": semantic_results, "total": 2, "query": "export restrictions"}
        )):
            from gta_mcp.server import _gta_unified_semantic_search
            result = await _gta_unified_semantic_search(
                params=params,
                filters={"announcement_period": ["1900-01-01", "2099-12-31"]},
                filter_messages=[],
                original_params={},
                client=mock_client,
            )
        data = json.loads(result)
        for rec in data["results"]:
            assert "matched_snippets" in rec, f"matched_snippets missing from record {rec}"
            assert len(rec["matched_snippets"]) >= 1

    async def test_snippets_absent_when_flag_false(self, mock_client, monkeypatch):
        """Flag=False (default) → matched_snippets absent from all records."""
        monkeypatch.delenv("SEMANTIC_CANDIDATE_CEILING", raising=False)

        candidate_ids = [1, 2]
        mock_client.search_interventions.side_effect = [
            [{"intervention_id": i} for i in candidate_ids],
            [_make_struct_record(i) for i in candidate_ids],
        ]
        # Danswer could theoretically return snippets even without the flag —
        # we must NOT forward them when include_matched_snippets=False.
        semantic_results = [
            _make_semantic_record(1, 0.9, snippets=["Should not appear."]),
            _make_semantic_record(2, 0.8, snippets=["Should not appear."]),
        ]

        params = GTASearchInput(
            semantic_query="export restrictions",
            sorting=None,
            limit=2,
            response_format="json",
            include_matched_snippets=False,
        )

        with patch("gta_mcp.server.semantic_search_interventions", new=AsyncMock(
            return_value={"results": semantic_results, "total": 2, "query": "export restrictions"}
        )):
            from gta_mcp.server import _gta_unified_semantic_search
            result = await _gta_unified_semantic_search(
                params=params,
                filters={"announcement_period": ["1900-01-01", "2099-12-31"]},
                filter_messages=[],
                original_params={},
                client=mock_client,
            )
        data = json.loads(result)
        for rec in data["results"]:
            assert "matched_snippets" not in rec, f"matched_snippets should be absent, got {rec}"

    async def test_include_matched_snippets_forwarded_to_danswer(self, mock_client, monkeypatch):
        """include_matched_snippets=True is forwarded to the danswer call."""
        monkeypatch.delenv("SEMANTIC_CANDIDATE_CEILING", raising=False)

        candidate_ids = [1]
        mock_client.search_interventions.side_effect = [
            [{"intervention_id": 1}],
            [_make_struct_record(1)],
        ]

        params = GTASearchInput(
            semantic_query="export restrictions",
            sorting=None,
            limit=1,
            response_format="json",
            include_matched_snippets=True,
        )

        captured_kwargs = {}

        async def fake_semantic_search(**kwargs):
            captured_kwargs.update(kwargs)
            return {"results": [_make_semantic_record(1, 0.9, snippets=["Test snippet."])],
                    "total": 1, "query": "export restrictions"}

        with patch("gta_mcp.server.semantic_search_interventions", new=fake_semantic_search):
            from gta_mcp.server import _gta_unified_semantic_search
            await _gta_unified_semantic_search(
                params=params,
                filters={"announcement_period": ["1900-01-01", "2099-12-31"]},
                filter_messages=[],
                original_params={},
                client=mock_client,
            )

        assert captured_kwargs.get("include_matched_snippets") is True

    async def test_flag_not_forwarded_when_false(self, mock_client, monkeypatch):
        """include_matched_snippets=False (default) → not forwarded to danswer body."""
        monkeypatch.delenv("SEMANTIC_CANDIDATE_CEILING", raising=False)

        candidate_ids = [1]
        mock_client.search_interventions.side_effect = [
            [{"intervention_id": 1}],
            [_make_struct_record(1)],
        ]

        params = GTASearchInput(
            semantic_query="export restrictions",
            sorting=None,
            limit=1,
            response_format="json",
            include_matched_snippets=False,
        )

        captured_kwargs = {}

        async def fake_semantic_search(**kwargs):
            captured_kwargs.update(kwargs)
            return {"results": [_make_semantic_record(1, 0.9)],
                    "total": 1, "query": "export restrictions"}

        with patch("gta_mcp.server.semantic_search_interventions", new=fake_semantic_search):
            from gta_mcp.server import _gta_unified_semantic_search
            await _gta_unified_semantic_search(
                params=params,
                filters={"announcement_period": ["1900-01-01", "2099-12-31"]},
                filter_messages=[],
                original_params={},
                client=mock_client,
            )

        assert captured_kwargs.get("include_matched_snippets") is False

    async def test_no_snippets_without_semantic_query(self, mock_client, monkeypatch):
        """Flag set without semantic_query → no error, no snippets (no-op)."""
        monkeypatch.delenv("SEMANTIC_CANDIDATE_CEILING", raising=False)

        # Standard (non-semantic) path
        mock_client.search_interventions.return_value = [_make_struct_record(1)]

        params = GTASearchInput(
            sorting="-date_announced",
            limit=5,
            response_format="json",
            include_matched_snippets=True,
        )
        assert params.semantic_query is None

        # Should not call danswer at all — danswer mock should not be invoked
        danswer_called = []

        async def should_not_call(**kwargs):
            danswer_called.append(True)
            return {}

        with patch("gta_mcp.server.semantic_search_interventions", new=should_not_call):
            from gta_mcp.server import gta_search_interventions
            import os
            os.environ.setdefault("GTA_API_KEY", "test-key")
            with patch("gta_mcp.server.get_api_client", return_value=mock_client):
                result = await gta_search_interventions(
                    include_matched_snippets=True,
                    response_format="json",
                    limit=5,
                )

        assert not danswer_called, "danswer should not be called when semantic_query is None"
        data = json.loads(result)
        for rec in data.get("results", []):
            assert "matched_snippets" not in rec

    async def test_show_keys_excludes_matched_snippets_from_api_call(self, mock_client, monkeypatch):
        """matched_snippets in show_keys is not forwarded to the GTA struct fetch."""
        monkeypatch.delenv("SEMANTIC_CANDIDATE_CEILING", raising=False)

        candidate_ids = [1]
        captured_struct_show_keys = []

        async def fake_search(filters, limit, offset, sorting, show_keys):
            if show_keys == ["intervention_id"]:
                return [{"intervention_id": 1}]
            captured_struct_show_keys.append(show_keys)
            return [_make_struct_record(1)]

        mock_client.search_interventions.side_effect = fake_search

        params = GTASearchInput(
            semantic_query="export restrictions",
            sorting=None,
            limit=1,
            response_format="json",
            include_matched_snippets=True,
            show_keys=["intervention_id", "state_act_title", "matched_snippets"],
        )

        with patch("gta_mcp.server.semantic_search_interventions", new=AsyncMock(
            return_value={"results": [_make_semantic_record(1, 0.9, snippets=["Snippet."])],
                          "total": 1, "query": "test"}
        )):
            from gta_mcp.server import _gta_unified_semantic_search
            await _gta_unified_semantic_search(
                params=params,
                filters={"announcement_period": ["1900-01-01", "2099-12-31"]},
                filter_messages=[],
                original_params={},
                client=mock_client,
            )

        assert captured_struct_show_keys, "struct fetch was not called"
        for keys in captured_struct_show_keys:
            if keys is not None:
                assert "matched_snippets" not in keys, "matched_snippets leaked into GTA API call"


# ---------------------------------------------------------------------------
# Formatter tests
# ---------------------------------------------------------------------------


class TestSnippetsMarkdownRenderer:

    def test_snippets_rendered_in_markdown(self):
        data = {
            "results": [
                {
                    "intervention_id": 42,
                    "state_act_title": "Test Act",
                    "gta_evaluation": "Red",
                    "date_announced": "2024-01-01",
                    "is_in_force": True,
                    "score": 0.95,
                    "matched_snippets": [
                        "The measure restricts exports of advanced chips.",
                        "Implementation began in January 2024.",
                    ],
                }
            ],
            "count": 1,
        }
        output = format_interventions_markdown(data)
        assert "Matched Snippets" in output
        assert "The measure restricts exports of advanced chips." in output
        assert "Implementation began in January 2024." in output

    def test_no_snippets_section_when_absent(self):
        data = {
            "results": [
                {
                    "intervention_id": 42,
                    "state_act_title": "Test Act",
                    "gta_evaluation": "Red",
                    "date_announced": "2024-01-01",
                    "is_in_force": True,
                }
            ],
            "count": 1,
        }
        output = format_interventions_markdown(data)
        assert "Matched Snippets" not in output

    def test_snippets_rendered_as_blockquotes(self):
        data = {
            "results": [
                {
                    "intervention_id": 42,
                    "state_act_title": "Test Act",
                    "gta_evaluation": "Red",
                    "date_announced": "2024-01-01",
                    "is_in_force": True,
                    "matched_snippets": ["Quoted evidence here."],
                }
            ],
            "count": 1,
        }
        output = format_interventions_markdown(data)
        assert "> Quoted evidence here." in output

    def test_json_format_includes_snippets(self):
        data = {
            "results": [
                {
                    "intervention_id": 42,
                    "matched_snippets": ["Chip export restriction."],
                    "score": 0.9,
                }
            ],
            "count": 1,
        }
        output = format_interventions_json(data)
        parsed = json.loads(output)
        assert "matched_snippets" in parsed["results"][0]
        assert parsed["results"][0]["matched_snippets"] == ["Chip export restriction."]

    def test_pre_existing_caller_no_snippets_unchanged(self):
        """Records without matched_snippets produce output identical to before this change."""
        record = {
            "intervention_id": 99,
            "state_act_title": "Old Act",
            "gta_evaluation": "Green",
            "date_announced": "2023-01-01",
            "is_in_force": False,
        }
        data = {"results": [record], "count": 1}
        output = format_interventions_markdown(data)
        assert "Matched Snippets" not in output
        assert "matched_snippets" not in output


# ---------------------------------------------------------------------------
# Tool description contains semantic_query dependency note
# ---------------------------------------------------------------------------


def test_tool_description_documents_semantic_query_dependency():
    """The gta_search_interventions docstring mentions the semantic_query dependency."""
    from gta_mcp.server import gta_search_interventions
    doc = gta_search_interventions.__doc__ or ""
    assert "semantic_query" in doc
    assert "include_matched_snippets" in doc or "citation" in doc.lower() or "snippet" in doc.lower()
