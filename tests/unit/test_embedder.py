from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from agentrag.config import Settings
from agentrag.ingestion.embedder import embed_chunks
from agentrag.types import Chunk


def test_output_length_matches_input(settings: Settings) -> None:
    """Output list length equals input chunk list length."""
    chunks = [
        Chunk(
            chunk_id=f"test_{i}",
            source_id="test",
            text=f"Sample text {i}",
            start_char=0,
            end_char=10,
            index=i,
        )
        for i in range(3)
    ]
    with patch("agentrag.ingestion.embedder.SentenceTransformer") as mock_st:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.zeros((3, 384), dtype=np.float32)
        mock_st.return_value = mock_model
        result = embed_chunks(chunks, settings)
    assert len(result) == 3


def test_vector_dimension(settings: Settings) -> None:
    """Each vector has length equal to settings.vector_dim."""
    chunks = [
        Chunk(
            chunk_id="test_0",
            source_id="test",
            text="Sample text",
            start_char=0,
            end_char=10,
            index=0,
        )
    ]
    with patch("agentrag.ingestion.embedder.SentenceTransformer") as mock_st:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.zeros((1, 384), dtype=np.float32)
        mock_st.return_value = mock_model
        result = embed_chunks(chunks, settings)
    assert len(result[0].vector) == settings.vector_dim


def test_chunk_fields_preserved(settings: Settings) -> None:
    """chunk_id, source_id, and text are preserved in output."""
    chunks = [
        Chunk(
            chunk_id="test_chunk_0",
            source_id="test_source",
            text="Known text content",
            start_char=0,
            end_char=10,
            index=0,
        )
    ]
    with patch("agentrag.ingestion.embedder.SentenceTransformer") as mock_st:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.zeros((1, 384), dtype=np.float32)
        mock_st.return_value = mock_model
        result = embed_chunks(chunks, settings)
    assert result[0].chunk_id == "test_chunk_0"
    assert result[0].source_id == "test_source"
    assert result[0].text == "Known text content"


def test_metadata_passthrough(settings: Settings) -> None:
    """Metadata dict is passed through to EmbeddedChunk."""
    chunks = [
        Chunk(
            chunk_id="test_0",
            source_id="test",
            text="Sample text",
            start_char=0,
            end_char=10,
            index=0,
        )
    ]
    metadata = {"filename": "test.txt", "extra": "value"}
    with patch("agentrag.ingestion.embedder.SentenceTransformer") as mock_st:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.zeros((1, 384), dtype=np.float32)
        mock_st.return_value = mock_model
        result = embed_chunks(chunks, settings, metadata=metadata)
    assert result[0].metadata == {"filename": "test.txt", "extra": "value"}
