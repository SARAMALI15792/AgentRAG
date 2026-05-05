"""Reranker — re-ranks search results using a cross-encoder model."""

from __future__ import annotations

from typing import Any

from sentence_transformers import CrossEncoder

from agentrag.config import Settings
from agentrag.types import SearchResult

_cross_encoder: CrossEncoder | None = None


def rerank(
    query: str,
    results: list[SearchResult],
    settings: Settings,
) -> list[SearchResult]:
    """Return results sorted by cross-encoder score; identity when disabled."""
    if not results or not settings.rerank:
        return results
    ce = _load_cross_encoder()
    pairs: Any = [
        [query, r.text] for r in results
    ]  # stub type too broad; list[list[str]] works
    scores = ce.predict(pairs)
    ranked = sorted(
        zip(results, scores, strict=False), key=lambda x: float(x[1]), reverse=True
    )
    return [r for r, _ in ranked]


def _load_cross_encoder() -> CrossEncoder:
    """Load and cache CrossEncoder on first call."""
    global _cross_encoder
    if _cross_encoder is None:
        _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder
