"""Embedder — converts text chunks to dense vector embeddings."""

from __future__ import annotations

import logging
from typing import Any

from sentence_transformers import SentenceTransformer

from agentrag.config import Settings
from agentrag.types import Chunk, EmbeddedChunk

logger = logging.getLogger(__name__)


def embed_chunks(
    chunks: list[Chunk],
    settings: Settings,
    metadata: dict[str, Any] | None = None,
) -> list[EmbeddedChunk]:
    """Embed chunk texts using sentence-transformers model."""
    model = SentenceTransformer(settings.embed_model)
    texts = [chunk.text for chunk in chunks]
    vectors = model.encode(texts)  # returns np.ndarray shape (n, 384)

    embedded_chunks: list[EmbeddedChunk] = []
    for i, chunk in enumerate(chunks):
        embedded_chunks.append(
            EmbeddedChunk(
                chunk_id=chunk.chunk_id,
                source_id=chunk.source_id,
                text=chunk.text,
                vector=vectors[i].tolist(),  # convert ndarray row to list[float]
                metadata=metadata or {},
            )
        )

    return embedded_chunks
