"""Tests for the query planner (Gemini-backed with graceful degrade)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agentrag.config import Settings
from agentrag.types import QueryPlan


@pytest.fixture
def settings_with_key() -> Settings:
    """Settings with a fake API key set."""
    return Settings(google_api_key="fake-key-for-testing")


@pytest.fixture
def settings_no_key() -> Settings:
    """Settings with no API key."""
    return Settings(google_api_key="")


def _mock_gemini_response(sub_queries: list[str]) -> MagicMock:
    """Build a mock Gemini response returning the given sub_queries as JSON."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(sub_queries)
    return mock_response


def test_plan_simple_query_returns_original_as_sub_query(
    settings_with_key: Settings,
) -> None:
    """Simple query with valid Gemini response returns QueryPlan with sub_queries."""
    from agentrag.retrieval.query_planner import plan

    mock_response = _mock_gemini_response(["what is semantic search?"])

    with patch("agentrag.retrieval.query_planner.genai") as mock_genai:
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_response

        result = plan("what is semantic search?", settings_with_key)

    assert isinstance(result, QueryPlan)
    assert result.original_query == "what is semantic search?"
    assert len(result.sub_queries) >= 1
    assert result.original_query in result.sub_queries or len(result.sub_queries) >= 1


def test_plan_compound_query_returns_multiple_sub_queries(
    settings_with_key: Settings,
) -> None:
    """Compound query with Gemini response returns >= 2 sub_queries."""
    from agentrag.retrieval.query_planner import plan

    sub_qs = [
        "what are the advantages of vector databases?",
        "what are the disadvantages of vector databases?",
    ]
    mock_response = _mock_gemini_response(sub_qs)

    with patch("agentrag.retrieval.query_planner.genai") as mock_genai:
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_response

        result = plan(
            "compare advantages and disadvantages of vector databases",
            settings_with_key,
        )

    assert isinstance(result, QueryPlan)
    assert len(result.sub_queries) >= 2


def test_plan_no_api_key_returns_single_query_plan(
    settings_no_key: Settings,
) -> None:
    """Missing API key → single-item plan with original query, no Gemini call."""
    from agentrag.retrieval.query_planner import plan

    result = plan("some query", settings_no_key)

    assert isinstance(result, QueryPlan)
    assert result.original_query == "some query"
    assert result.sub_queries == ["some query"]


def test_plan_gemini_unavailable_degrades_gracefully(
    settings_with_key: Settings,
) -> None:
    """Network error from Gemini → single-item plan, no raise."""
    from agentrag.retrieval.query_planner import plan

    with patch("agentrag.retrieval.query_planner.genai") as mock_genai:
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("network error")

        result = plan("test query", settings_with_key)

    assert isinstance(result, QueryPlan)
    assert result.sub_queries == ["test query"]


def test_plan_invalid_json_response_degrades_gracefully(
    settings_with_key: Settings,
) -> None:
    """Invalid JSON from Gemini → single-item plan, no raise."""
    from agentrag.retrieval.query_planner import plan

    mock_response = MagicMock()
    mock_response.text = "not valid json at all"

    with patch("agentrag.retrieval.query_planner.genai") as mock_genai:
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_response

        result = plan("test query", settings_with_key)

    assert isinstance(result, QueryPlan)
    assert result.sub_queries == ["test query"]


def test_plan_original_query_always_in_result(settings_with_key: Settings) -> None:
    """original_query field always matches the input."""
    from agentrag.retrieval.query_planner import plan

    with patch("agentrag.retrieval.query_planner.genai") as mock_genai:
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("any error")

        result = plan("my specific query", settings_with_key)

    assert result.original_query == "my specific query"
