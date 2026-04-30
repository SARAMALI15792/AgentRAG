"""Tests for the chunk evaluator (Gemini-backed with graceful degrade)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agentrag.config import Settings
from agentrag.types import EvaluationReport, SearchResult


@pytest.fixture
def settings_with_key() -> Settings:
    return Settings(google_api_key="fake-key-for-testing")


@pytest.fixture
def settings_no_key() -> Settings:
    return Settings(google_api_key="")


def _make_results(n: int) -> list[SearchResult]:
    return [
        SearchResult(
            chunk_id=f"chunk_{i}",
            source_id="src_0",
            filename="test.txt",
            text=f"Chunk text number {i}",
            score=0.8,
            metadata={},
        )
        for i in range(n)
    ]


def _mock_evaluator_response(scores: list[dict[str, object]]) -> MagicMock:
    mock = MagicMock()
    mock.text = json.dumps(scores)
    return mock


def test_evaluate_sufficient_when_any_score_above_threshold(
    settings_with_key: Settings,
) -> None:
    """EvaluationReport.sufficient=True when any chunk score >= 0.7."""
    from agentrag.retrieval.evaluator import evaluate

    results = _make_results(2)
    scores = [
        {"chunk_id": "chunk_0", "score": 0.9, "reason": "Directly answers the query"},
        {"chunk_id": "chunk_1", "score": 0.4, "reason": "Partially relevant"},
    ]
    mock_resp = _mock_evaluator_response(scores)

    with patch("agentrag.retrieval.evaluator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_resp

        report = evaluate("test query", results, settings_with_key)

    assert isinstance(report, EvaluationReport)
    assert report.sufficient is True
    assert report.query == "test query"


def test_evaluate_not_sufficient_when_all_scores_below_threshold(
    settings_with_key: Settings,
) -> None:
    """sufficient=False when all scores < 0.7, suggested_queries non-empty."""
    from agentrag.retrieval.evaluator import evaluate

    results = _make_results(2)
    scores = [
        {
            "chunk_id": "chunk_0",
            "score": 0.3,
            "reason": "Tangentially related",
            "suggested_query": "alternative query A",
        },
        {
            "chunk_id": "chunk_1",
            "score": 0.2,
            "reason": "Not relevant",
            "suggested_query": "alternative query B",
        },
    ]
    mock_resp = _mock_evaluator_response(scores)

    with patch("agentrag.retrieval.evaluator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_resp

        report = evaluate("test query", results, settings_with_key)

    assert report.sufficient is False
    assert len(report.suggested_queries) > 0


def test_evaluate_empty_results_returns_not_sufficient(
    settings_with_key: Settings,
) -> None:
    """Empty chunk list → sufficient=False regardless of API response."""
    from agentrag.retrieval.evaluator import evaluate

    report = evaluate("test query", [], settings_with_key)

    assert isinstance(report, EvaluationReport)
    assert report.sufficient is False
    assert report.scored_chunks == []


def test_evaluate_no_api_key_scores_all_half(settings_no_key: Settings) -> None:
    """No API key → all chunks score 0.5, sufficient=True (pass-through)."""
    from agentrag.retrieval.evaluator import evaluate

    results = _make_results(3)
    report = evaluate("test query", results, settings_no_key)

    assert isinstance(report, EvaluationReport)
    assert all(cs.score == 0.5 for cs in report.scored_chunks)
    assert report.sufficient is True


def test_evaluate_gemini_error_degrades_gracefully(
    settings_with_key: Settings,
) -> None:
    """Gemini API error → scores 0.5, sufficient=True, no raise."""
    from agentrag.retrieval.evaluator import evaluate

    results = _make_results(2)

    with patch("agentrag.retrieval.evaluator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("quota exceeded")

        report = evaluate("test query", results, settings_with_key)

    assert isinstance(report, EvaluationReport)
    assert all(cs.score == 0.5 for cs in report.scored_chunks)
    assert report.sufficient is True


def test_evaluate_scores_in_valid_range(settings_with_key: Settings) -> None:
    """All ChunkScore.score values are in [0.0, 1.0]."""
    from agentrag.retrieval.evaluator import evaluate

    results = _make_results(3)
    scores = [
        {"chunk_id": f"chunk_{i}", "score": 0.5 + i * 0.2, "reason": "test"}
        for i in range(3)
    ]
    mock_resp = _mock_evaluator_response(scores)

    with patch("agentrag.retrieval.evaluator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_resp

        report = evaluate("test query", results, settings_with_key)

    for cs in report.scored_chunks:
        assert 0.0 <= cs.score <= 1.0
