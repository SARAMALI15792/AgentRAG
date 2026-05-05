"""Async generator interface for streaming retrieval."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from agentrag.config import Settings
from agentrag.retrieval.searcher import search
from agentrag.types import SearchResult


async def stream_search(
    query: str, top_k: int, settings: Settings
) -> AsyncGenerator[SearchResult, None]:
    """Yield SearchResult objects in score-descending order."""
    results = search(query, top_k, settings)
    for result in results:
        yield result
