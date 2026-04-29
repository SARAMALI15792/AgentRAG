"""Unit tests for server/tools.py — all dependencies mocked."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentrag.server.tools import (
    delete_source,
    get_document,
    ingest_directory,
    ingest_file,
    list_sources,
    search_by_metadata,
    search_documents,
)
from agentrag.types import (
    IngestResult,
    SearchResult,
    SourceInfo,
)


@pytest.fixture
def mock_pipeline() -> MagicMock:
    """Mock ingestion pipeline."""
    mock = MagicMock()
    mock.return_value = IngestResult(
        source_id="abc123",
        filename="test.txt",
        chunk_count=5,
        status="ok",
        error=None,
    )
    return mock


@pytest.fixture
def mock_searcher() -> MagicMock:
    """Mock searcher.search function."""
    mock = MagicMock()
    mock.return_value = [
        SearchResult(
            chunk_id="abc_0",
            source_id="abc",
            filename="test.txt",
            text="Result text",
            score=0.9,
            metadata={},
        )
    ]
    return mock


@pytest.fixture
def mock_store() -> MagicMock:
    """Mock QdrantStore."""
    store = MagicMock()
    store.list_sources.return_value = [
        SourceInfo(
            source_id="abc",
            filename="test.txt",
            chunk_count=5,
            metadata={},
            ingested_at="2026-04-29T00:00:00Z",
        )
    ]
    store.delete.return_value = 5
    return store


def test_ingest_file_delegates_to_pipeline(mock_pipeline: MagicMock) -> None:
    """ingest_file delegates to pipeline and returns IngestResult."""
    with patch("agentrag.server.tools.ingest", mock_pipeline):
        result = ingest_file(file_path="/tmp/test.txt")

    assert result.status == "ok"
    assert result.chunk_count == 5
    mock_pipeline.assert_called_once()


def test_ingest_file_nonexistent_path_returns_error() -> None:
    """ingest_file with non-existent path returns IngestResult(status='error')."""
    with patch("agentrag.server.tools.ingest") as mock_ingest:
        mock_ingest.return_value = IngestResult(
            source_id="",
            filename="missing.txt",
            chunk_count=0,
            status="error",
            error="File not found",
        )
        result = ingest_file(file_path="/nonexistent/missing.txt")

    assert result.status == "error"
    assert result.error == "File not found"


def test_ingest_directory_delegates_to_pipeline_per_file(
    mock_pipeline: MagicMock,
) -> None:
    """ingest_directory delegates to pipeline for each file."""
    with patch("agentrag.server.tools.ingest", mock_pipeline):
        with patch("agentrag.server.tools.Path") as mock_path_class:
            mock_dir = MagicMock()
            mock_dir.is_dir.return_value = True
            # rglob called 3 times (once per extension), return 1 file per call
            mock_dir.rglob.side_effect = [
                [Path("/tmp/a.txt")],
                [Path("/tmp/b.pdf")],
                [Path("/tmp/c.md")],
            ]
            mock_path_class.return_value = mock_dir

            results = ingest_directory(directory_path="/tmp")

    assert len(results) == 3
    assert all(r.status == "ok" for r in results)
    assert mock_pipeline.call_count == 3


def test_search_documents_delegates_to_searcher(mock_searcher: MagicMock) -> None:
    """search_documents delegates to searcher.search."""
    with patch("agentrag.server.tools.search", mock_searcher):
        results = search_documents(query="test query", top_k=5)

    assert len(results) == 1
    assert results[0].text == "Result text"
    mock_searcher.assert_called_once()


def test_search_documents_empty_query_raises_valueerror() -> None:
    """search_documents with empty string raises ValueError."""
    with pytest.raises(ValueError, match="query must not be empty"):
        search_documents(query="", top_k=5)


def test_search_by_metadata_delegates_to_store(mock_store: MagicMock) -> None:
    """search_by_metadata delegates to store.list_sources with filter."""
    with patch("agentrag.server.tools.QdrantStore", return_value=mock_store):
        results = search_by_metadata(filters={"filename": "test.txt"})

    assert len(results) == 1
    assert results[0].filename == "test.txt"


def test_search_by_metadata_empty_filters_raises_valueerror() -> None:
    """search_by_metadata with empty dict raises ValueError."""
    with pytest.raises(ValueError, match="filters must not be empty"):
        search_by_metadata(filters={})


def test_list_sources_delegates_to_store(mock_store: MagicMock) -> None:
    """list_sources delegates to store.list_sources."""
    with patch("agentrag.server.tools.QdrantStore", return_value=mock_store):
        results = list_sources()

    assert len(results) == 1
    assert results[0].source_id == "abc"
    mock_store.list_sources.assert_called_once()


def test_get_document_delegates_to_store(mock_store: MagicMock) -> None:
    """get_document delegates to store and reconstructs full text."""
    mock_store.query.return_value = [
        SearchResult(
            chunk_id="abc_0",
            source_id="abc",
            filename="test.txt",
            text="First chunk. ",
            score=1.0,
            metadata={},
        ),
        SearchResult(
            chunk_id="abc_1",
            source_id="abc",
            filename="test.txt",
            text="Second chunk.",
            score=1.0,
            metadata={},
        ),
    ]

    with patch("agentrag.server.tools.QdrantStore", return_value=mock_store):
        result = get_document(source_id="abc")

    assert result.source_id == "abc"
    assert result.filename == "test.txt"
    assert result.full_text == "First chunk. Second chunk."


def test_get_document_unknown_source_raises_valueerror(mock_store: MagicMock) -> None:
    """get_document with unknown source_id raises ValueError."""
    mock_store.query.return_value = []

    with patch("agentrag.server.tools.QdrantStore", return_value=mock_store):
        with pytest.raises(ValueError, match="source_id 'unknown' not found"):
            get_document(source_id="unknown")


def test_delete_source_delegates_to_store(mock_store: MagicMock) -> None:
    """delete_source delegates to store.delete."""
    with patch("agentrag.server.tools.QdrantStore", return_value=mock_store):
        result = delete_source(source_id="abc")

    assert result.status == "ok"
    assert result.chunks_deleted == 5
    mock_store.delete.assert_called_once_with("abc")


def test_delete_source_unknown_returns_not_found(mock_store: MagicMock) -> None:
    """delete_source with unknown source_id returns DeleteResult(status='not_found')."""
    mock_store.delete.return_value = 0

    with patch("agentrag.server.tools.QdrantStore", return_value=mock_store):
        result = delete_source(source_id="unknown")

    assert result.status == "not_found"
    assert result.chunks_deleted == 0
