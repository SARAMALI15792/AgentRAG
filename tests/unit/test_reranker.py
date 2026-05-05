"""Unit tests for retrieval/reranker.py (Phase 4, Group 2)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from agentrag.config import Settings
from agentrag.types import SearchResult


def _make_result(chunk_id: str, score: float) -> SearchResult:
    """Build a minimal SearchResult for testing."""
    return SearchResult(
        chunk_id=chunk_id,
        source_id="src",
        filename="test.txt",
        text=f"text for {chunk_id}",
        score=score,
        metadata={},
    )


def _settings(rerank: bool) -> Settings:
    """Build Settings with rerank flag set."""
    import tempfile
    from pathlib import Path

    return Settings(data_dir=Path(tempfile.mkdtemp()), rerank=rerank)


def test_identity_when_rerank_false() -> None:
    """AGENTRAG_RERANK=false — returns results unchanged, CrossEncoder never called."""
    import agentrag.retrieval.reranker as reranker_mod

    reranker_mod._cross_encoder = None  # ensure clean state
    results = [_make_result("a", 0.9), _make_result("b", 0.5)]
    settings = _settings(rerank=False)

    with patch("agentrag.retrieval.reranker.CrossEncoder") as mock_ce:
        output = reranker_mod.rerank("query", results, settings)

    mock_ce.assert_not_called()
    assert output == results


def test_reranker_sorts_by_cross_encoder_score() -> None:
    """AGENTRAG_RERANK=true — results re-ordered by cross-encoder score descending."""
    import agentrag.retrieval.reranker as reranker_mod

    reranker_mod._cross_encoder = None

    # Input: chunk_a has low vector score, chunk_b has high vector score.
    # CrossEncoder will assign higher score to chunk_a → order should flip.
    results = [_make_result("a", 0.4), _make_result("b", 0.9)]
    settings = _settings(rerank=True)

    mock_ce_instance = MagicMock()
    # CrossEncoder says chunk_a is more relevant (score 0.8 > 0.2)
    mock_ce_instance.predict.return_value = np.array([0.8, 0.2], dtype=np.float32)

    with patch(
        "agentrag.retrieval.reranker.CrossEncoder", return_value=mock_ce_instance
    ):
        output = reranker_mod.rerank("query", results, settings)

    assert output[0].chunk_id == "a", "chunk_a should be first after reranking"
    assert output[1].chunk_id == "b"


def test_rerank_empty_list() -> None:
    """Re-ranking an empty list returns empty list without error."""
    import agentrag.retrieval.reranker as reranker_mod

    reranker_mod._cross_encoder = None
    settings = _settings(rerank=True)

    with patch("agentrag.retrieval.reranker.CrossEncoder") as mock_ce:
        output = reranker_mod.rerank("query", [], settings)

    assert output == []
    mock_ce.assert_not_called()


def test_rerank_single_item() -> None:
    """Re-ranking a single-item list returns that item unchanged."""
    import agentrag.retrieval.reranker as reranker_mod

    reranker_mod._cross_encoder = None
    results = [_make_result("only", 0.7)]
    settings = _settings(rerank=True)

    mock_ce_instance = MagicMock()
    mock_ce_instance.predict.return_value = np.array([0.6], dtype=np.float32)

    with patch(
        "agentrag.retrieval.reranker.CrossEncoder", return_value=mock_ce_instance
    ):
        output = reranker_mod.rerank("query", results, settings)

    assert len(output) == 1
    assert output[0].chunk_id == "only"


def test_already_sorted_list_unchanged_order() -> None:
    """Re-ranking a correctly sorted list keeps the same order."""
    import agentrag.retrieval.reranker as reranker_mod

    reranker_mod._cross_encoder = None
    results = [_make_result("best", 0.9), _make_result("second", 0.5)]
    settings = _settings(rerank=True)

    mock_ce_instance = MagicMock()
    mock_ce_instance.predict.return_value = np.array([0.9, 0.3], dtype=np.float32)

    with patch(
        "agentrag.retrieval.reranker.CrossEncoder", return_value=mock_ce_instance
    ):
        output = reranker_mod.rerank("query", results, settings)

    assert output[0].chunk_id == "best"
    assert output[1].chunk_id == "second"


def test_cross_encoder_instantiated_once_per_session() -> None:
    """CrossEncoder constructor called once; second call reuses cached instance."""
    import agentrag.retrieval.reranker as reranker_mod

    reranker_mod._cross_encoder = None
    results = [_make_result("x", 0.5)]
    settings = _settings(rerank=True)

    mock_ce_instance = MagicMock()
    mock_ce_instance.predict.return_value = np.array([0.5], dtype=np.float32)

    with patch(
        "agentrag.retrieval.reranker.CrossEncoder", return_value=mock_ce_instance
    ) as mock_ce_cls:
        reranker_mod.rerank("q", results, settings)
        reranker_mod.rerank("q", results, settings)

    assert mock_ce_cls.call_count == 1, "CrossEncoder must be instantiated only once"
