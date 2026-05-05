"""Unit tests for retrieval/searcher.py — store and embedder are mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agentrag.config import Settings
from agentrag.retrieval.searcher import search
from agentrag.types import SearchResult


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Test settings with temp data dir."""
    return Settings(data_dir=tmp_path / "qdrant")


@pytest.fixture
def mock_store() -> MagicMock:
    """Mock QdrantStore with query method."""
    store = MagicMock()
    store.query.return_value = [
        SearchResult(
            chunk_id="abc_0",
            source_id="abc",
            filename="test.txt",
            text="First result",
            score=0.95,
            metadata={},
        ),
        SearchResult(
            chunk_id="abc_1",
            source_id="abc",
            filename="test.txt",
            text="Second result",
            score=0.85,
            metadata={},
        ),
        SearchResult(
            chunk_id="def_0",
            source_id="def",
            filename="other.txt",
            text="Third result",
            score=0.75,
            metadata={},
        ),
    ]
    return store


def _mock_model() -> MagicMock:
    """Shared model mock returning a deterministic query vector."""
    model = MagicMock()
    model.encode.return_value = [[0.1] * 384]
    return model


def test_search_returns_results_sorted_by_score_descending(
    settings: Settings, mock_store: MagicMock
) -> None:
    """Query returns list[SearchResult] sorted by score descending."""
    with patch("agentrag.retrieval.searcher.QdrantStore", return_value=mock_store):
        with patch(
            "agentrag.retrieval.searcher._get_model", return_value=_mock_model()
        ):
            results = search("test query", top_k=10, settings=settings)

    assert len(results) == 3
    assert results[0].score == 0.95
    assert results[1].score == 0.85
    assert results[2].score == 0.75
    assert results[0].text == "First result"


def test_search_respects_top_k_limit(settings: Settings, mock_store: MagicMock) -> None:
    """top_k parameter limits result count exactly."""
    with patch("agentrag.retrieval.searcher.QdrantStore", return_value=mock_store):
        with patch(
            "agentrag.retrieval.searcher._get_model", return_value=_mock_model()
        ):
            search("test query", top_k=2, settings=settings)

    mock_store.query.assert_called_once()
    call_args = mock_store.query.call_args
    assert call_args[1]["top_k"] == 2


def test_search_empty_store_returns_empty_list(settings: Settings) -> None:
    """Store returns empty list → searcher returns empty list, no exception."""
    empty_store = MagicMock()
    empty_store.query.return_value = []

    with patch("agentrag.retrieval.searcher.QdrantStore", return_value=empty_store):
        with patch(
            "agentrag.retrieval.searcher._get_model", return_value=_mock_model()
        ):
            results = search("test query", top_k=5, settings=settings)

    assert results == []


def test_search_forwards_metadata_filters_unchanged(
    settings: Settings, mock_store: MagicMock
) -> None:
    """Metadata filters dict is forwarded to store query unchanged."""
    filters = {"filename": "test.txt", "source_id": "abc"}

    with patch("agentrag.retrieval.searcher.QdrantStore", return_value=mock_store):
        with patch(
            "agentrag.retrieval.searcher._get_model", return_value=_mock_model()
        ):
            search("test query", top_k=5, settings=settings, filters=filters)

    mock_store.query.assert_called_once()
    call_args = mock_store.query.call_args
    assert call_args[1]["filters"] == filters
