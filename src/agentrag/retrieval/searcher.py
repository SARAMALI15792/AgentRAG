"""Searcher — semantic search over the Qdrant vector store."""

from __future__ import annotations

from typing import Any

from sentence_transformers import SentenceTransformer

from agentrag.config import Settings
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
    model = SentenceTransformer(settings.embed_model)
    vectors = model.encode([query])
    if hasattr(vectors[0], "tolist"):
        query_vector = vectors[0].tolist()
    else:
        query_vector = vectors[0]

    store = QdrantStore(settings)
    results = store.query(vector=query_vector, top_k=top_k, filters=filters)
    return reranker.rerank(query, results, settings)
