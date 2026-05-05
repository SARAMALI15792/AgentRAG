"""Unit tests for retrieval/streaming.py — async generator interface."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agentrag.config import Settings
from agentrag.retrieval.streaming import stream_search
from agentrag.types import SearchResult


@pytest.fixture
def ordered_results() -> list[SearchResult]:
    """Three results in score-descending order."""
    return [
        SearchResult("id_0", "src", "doc.txt", "text 0", 0.9, {}),
        SearchResult("id_1", "src", "doc.txt", "text 1", 0.7, {}),
        SearchResult("id_2", "src", "doc.txt", "text 2", 0.5, {}),
    ]


async def test_stream_search_yields_in_score_descending_order(
    settings: Settings,
    ordered_results: list[SearchResult],
) -> None:
    """stream_search yields results in score-descending order matching searcher."""
    with patch("agentrag.retrieval.streaming.search", return_value=ordered_results):
        results = [r async for r in stream_search("query", 3, settings)]
    scores = [r.score for r in results]
    assert scores == [0.9, 0.7, 0.5]


async def test_stream_search_chunk_ids_match_batch_results(
    settings: Settings,
    ordered_results: list[SearchResult],
) -> None:
    """chunk_ids from stream_search match those from the underlying batch search."""
    with patch("agentrag.retrieval.streaming.search", return_value=ordered_results):
        streamed = [r async for r in stream_search("query", 3, settings)]
    assert [r.chunk_id for r in streamed] == [r.chunk_id for r in ordered_results]


async def test_stream_search_empty_corpus_yields_nothing(
    settings: Settings,
) -> None:
    """stream_search on an empty store yields zero results without raising."""
    with patch("agentrag.retrieval.streaming.search", return_value=[]):
        results = [r async for r in stream_search("query", 5, settings)]
    assert results == []
