from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from agentrag.config import Settings
from agentrag.ingestion.pipeline import ingest
from agentrag.types import EmbeddedChunk, IngestResult


def test_success_returns_ok_status(settings: Settings, tmp_path: Path) -> None:
    """Successful ingestion returns IngestResult with status='ok'."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Sample content for testing.", encoding="utf-8")

    with (
        patch("agentrag.ingestion.pipeline.read_file") as mock_read,
        patch("agentrag.ingestion.pipeline.chunk_document") as mock_chunk,
        patch("agentrag.ingestion.pipeline.embed_chunks") as mock_embed,
        patch("agentrag.ingestion.pipeline.QdrantStore") as mock_store_cls,
    ):

        mock_read.return_value = MagicMock(source_id="test_id", filename="test.txt")
        mock_chunk.return_value = [MagicMock()] * 3
        mock_embed.return_value = [
            EmbeddedChunk(
                chunk_id=f"test_id_{i}",
                source_id="test_id",
                text=f"chunk {i}",
                vector=[0.0] * 384,
                metadata={"filename": "test.txt"},
            )
            for i in range(3)
        ]
        mock_store = MagicMock()
        mock_store_cls.return_value = mock_store

        result = ingest(txt_file, settings)

    assert isinstance(result, IngestResult)
    assert result.status == "ok"
    assert result.chunk_count == 3
    assert result.source_id == "test_id"
    assert result.filename == "test.txt"
    assert result.error is None


def test_nonexistent_file_returns_error(settings: Settings, tmp_path: Path) -> None:
    """Non-existent file returns IngestResult with status='error'."""
    nonexistent = tmp_path / "does_not_exist.txt"
    result = ingest(nonexistent, settings)
    assert result.status == "error"
    assert result.error is not None
    assert "not found" in result.error.lower() or "filenotfound" in result.error.lower()


def test_unsupported_extension_returns_error(
    settings: Settings, tmp_path: Path
) -> None:
    """Unsupported file extension returns IngestResult with status='error'."""
    unsupported = tmp_path / "test.xyz"
    unsupported.write_text("content", encoding="utf-8")
    result = ingest(unsupported, settings)
    assert result.status == "error"
    assert result.error is not None
    assert "unsupported" in result.error.lower()


def test_embedder_failure_returns_error(settings: Settings, tmp_path: Path) -> None:
    """Embedder failure returns IngestResult with status='error'."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Sample content.", encoding="utf-8")

    with (
        patch("agentrag.ingestion.pipeline.read_file") as mock_read,
        patch("agentrag.ingestion.pipeline.chunk_document") as mock_chunk,
        patch("agentrag.ingestion.pipeline.embed_chunks") as mock_embed,
    ):

        mock_read.return_value = MagicMock(source_id="test_id", filename="test.txt")
        mock_chunk.return_value = [MagicMock()]
        mock_embed.side_effect = RuntimeError("Model loading failed")

        result = ingest(txt_file, settings)

    assert result.status == "error"
    assert result.error is not None
    assert "model loading failed" in result.error.lower()
