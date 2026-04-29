"""Reranker — re-ranks search results (identity stub in Phase 2)."""

from __future__ import annotations

from agentrag.types import SearchResult


def rerank(results: list[SearchResult]) -> list[SearchResult]:
    """Return results unchanged; real re-ranking is Phase 5."""
    return results
