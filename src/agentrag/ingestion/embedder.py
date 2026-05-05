"""Embedder — converts text chunks to dense vector embeddings."""

from __future__ import annotations

import logging
from typing import Any

from sentence_transformers import SentenceTransformer

from agentrag.config import Settings
from agentrag.types import Chunk, EmbeddedChunk

logger = logging.getLogger(__name__)

_model_cache: dict[str, SentenceTransformer] = {}


def _get_model(model_name: str) -> SentenceTransformer:
    """Return cached SentenceTransformer, loading it once per model name."""
    if model_name not in _model_cache:
        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]


def embed_chunks(
    chunks: list[Chunk],
    settings: Settings,
    metadata: dict[str, Any] | None = None,
) -> list[EmbeddedChunk]:
    """Embed chunk texts using sentence-transformers model."""
    model = _get_model(settings.embed_model)
    texts = [chunk.text for chunk in chunks]
    vectors = model.encode(texts)  # returns np.ndarray shape (n, dim)

    embedded_chunks: list[EmbeddedChunk] = []
    for i, chunk in enumerate(chunks):
        embedded_chunks.append(
            EmbeddedChunk(
                chunk_id=chunk.chunk_id,
                source_id=chunk.source_id,
                text=chunk.text,
                vector=vectors[i].tolist(),
                metadata=metadata or {},
            )
        )

    return embedded_chunks
