"""Unit tests for agentic MCP tool handlers (planner, evaluator, searcher mocked)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agentrag.types import (
    ChunkScore,
    EvaluationReport,
    QueryPlan,
    SearchResult,
)


def _make_search_result(chunk_id: str, score: float = 0.8) -> SearchResult:
    return SearchResult(
        chunk_id=chunk_id,
        source_id="src_0",
        filename="test.txt",
        text=f"Text for {chunk_id}",
        score=score,
        metadata={},
    )


# ---------------------------------------------------------------------------
# plan_query
# ---------------------------------------------------------------------------


def test_plan_query_delegates_to_query_planner() -> None:
    """plan_query delegates to query_planner.plan and returns QueryPlan."""
    from agentrag.server.tools import plan_query

    expected = QueryPlan(original_query="test", sub_queries=["sub1", "sub2"])

    with patch("agentrag.server.tools.query_planner") as mock_planner:
        mock_planner.plan.return_value = expected
        result = plan_query("test")

    assert result.original_query == "test"
    assert result.sub_queries == ["sub1", "sub2"]
    mock_planner.plan.assert_called_once()


# ---------------------------------------------------------------------------
# search_multi
# ---------------------------------------------------------------------------


def test_search_multi_merges_and_deduplicates() -> None:
    """search_multi merges results from N queries, deduplicating by chunk_id."""
    from agentrag.server.tools import search_multi

    results_q1 = [_make_search_result("c1", 0.9), _make_search_result("c2", 0.7)]
    results_q2 = [_make_search_result("c2", 0.8), _make_search_result("c3", 0.6)]

    with patch("agentrag.server.tools.search") as mock_search:
        mock_search.side_effect = [results_q1, results_q2]
        results = search_multi(["query one", "query two"], top_k=5)

    chunk_ids = [r.chunk_id for r in results]
    assert len(chunk_ids) == len(set(chunk_ids)), "Duplicate chunk_ids in results"
    assert "c1" in chunk_ids
    assert "c2" in chunk_ids
    assert "c3" in chunk_ids


def test_search_multi_keeps_highest_score_for_duplicate() -> None:
    """When same chunk_id appears in multiple queries, highest score is kept."""
    from agentrag.server.tools import search_multi

    results_q1 = [_make_search_result("dup", 0.6)]
    results_q2 = [_make_search_result("dup", 0.9)]

    with patch("agentrag.server.tools.search") as mock_search:
        mock_search.side_effect = [results_q1, results_q2]
        results = search_multi(["q1", "q2"], top_k=5)

    dup_results = [r for r in results if r.chunk_id == "dup"]
    assert len(dup_results) == 1
    assert dup_results[0].score == 0.9


def test_search_multi_returns_sorted_by_score_descending() -> None:
    """Merged results are sorted by score descending."""
    from agentrag.server.tools import search_multi

    with patch("agentrag.server.tools.search") as mock_search:
        mock_search.return_value = [
            _make_search_result("c1", 0.5),
            _make_search_result("c2", 0.9),
            _make_search_result("c3", 0.7),
        ]
        results = search_multi(["q"], top_k=5)

    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_search_multi_empty_queries_raises_value_error() -> None:
    """search_multi with empty queries list raises ValueError."""
    from agentrag.server.tools import search_multi

    with pytest.raises(ValueError, match="queries"):
        search_multi([], top_k=5)


# ---------------------------------------------------------------------------
# evaluate_chunks
# ---------------------------------------------------------------------------


def test_evaluate_chunks_delegates_to_evaluator() -> None:
    """evaluate_chunks delegates to evaluator.evaluate and returns EvaluationReport."""
    from agentrag.server.tools import evaluate_chunks

    results = [_make_search_result("c1")]
    expected_report = EvaluationReport(
        query="test",
        scored_chunks=[
            ChunkScore(chunk_id="c1", source_id="src_0", score=0.9, reason="good")
        ],
        sufficient=True,
        suggested_queries=[],
    )

    with patch("agentrag.server.tools.evaluator") as mock_evaluator:
        mock_evaluator.evaluate.return_value = expected_report
        report = evaluate_chunks("test", results)

    assert isinstance(report, EvaluationReport)
    assert report.sufficient is True
    mock_evaluator.evaluate.assert_called_once()


def test_evaluate_chunks_empty_results_returns_not_sufficient() -> None:
    """evaluate_chunks with no results returns EvaluationReport(sufficient=False)."""
    from agentrag.server.tools import evaluate_chunks

    not_sufficient = EvaluationReport(
        query="q",
        scored_chunks=[],
        sufficient=False,
        suggested_queries=[],
    )

    with patch("agentrag.server.tools.evaluator") as mock_evaluator:
        mock_evaluator.evaluate.return_value = not_sufficient
        report = evaluate_chunks("q", [])

    assert report.sufficient is False
