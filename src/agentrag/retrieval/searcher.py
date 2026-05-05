"""Searcher — semantic search over the Qdrant vector store."""

from __future__ import annotations

from typing import Any

from agentrag.config import Settings
from agentrag.ingestion.embedder import _get_model
from agentrag.retrieval import reranker
from agentrag.store.qdrant import QdrantStore
from agentrag.types import SearchResult


def search(
    query: str,
    top_k: int,
    settings: Settings,
    filters: dict[str, Any] | None = None,
) -> list[SearchResult]:
    """Embed query, retrieve top_k results, and rerank if enabled."""
    model = _get_model(settings.embed_model)
    vectors = model.encode([query])
    raw = vectors[0]
    query_vector: list[float] = raw.tolist() if hasattr(raw, "tolist") else list(raw)

    store = QdrantStore(settings)
    results = store.query(vector=query_vector, top_k=top_k, filters=filters)
    return reranker.rerank(query, results, settings)
