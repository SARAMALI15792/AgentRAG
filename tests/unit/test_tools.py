"""Unit tests for server/tools.py — all dependencies mocked."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentrag.config import Settings
from agentrag.server.tools import (
    create_collection,
    delete_source,
    get_document,
    ingest_directory,
    ingest_file,
    list_collections,
    list_sources,
    search_by_metadata,
    search_documents,
    search_stream,
    switch_collection,
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
    """ingest_directory delegates to pipeline for each matched file."""
    _file_map = {
        "*.txt": [Path("/tmp/a.txt")],
        "*.md": [Path("/tmp/b.md")],
        "*.pdf": [Path("/tmp/c.pdf")],
    }

    with patch("agentrag.server.tools.ingest", mock_pipeline):
        with patch("agentrag.server.tools.Path") as mock_path_class:
            mock_dir = MagicMock()
            mock_dir.is_dir.return_value = True
            mock_dir.rglob.side_effect = lambda pat: _file_map.get(pat, [])
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
    """search_by_metadata delegates to store.filter_sources."""
    mock_store.filter_sources.return_value = [
        SourceInfo(
            source_id="abc",
            filename="test.txt",
            chunk_count=5,
            metadata={},
            ingested_at="2026-04-29T00:00:00Z",
        )
    ]
    with patch("agentrag.server.tools.QdrantStore", return_value=mock_store):
        results = search_by_metadata(filters={"filename": "test.txt"})

    assert len(results) == 1
    assert results[0].filename == "test.txt"
    mock_store.filter_sources.assert_called_once_with({"filename": "test.txt"})


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
    """get_document delegates to store.get_full_document."""
    mock_store.get_full_document.return_value = (
        "test.txt",
        "First chunk. Second chunk.",
        "abc",
        {},
    )

    with patch("agentrag.server.tools.QdrantStore", return_value=mock_store):
        result = get_document(source_id="abc")

    assert result.source_id == "abc"
    assert result.filename == "test.txt"
    assert result.full_text == "First chunk. Second chunk."
    mock_store.get_full_document.assert_called_once_with("abc")


def test_get_document_unknown_source_raises_valueerror(mock_store: MagicMock) -> None:
    """get_document with unknown source_id raises ValueError."""
    mock_store.get_full_document.side_effect = ValueError(
        "source_id 'unknown' not found"
    )

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


def test_ingest_directory_all_seven_types(
    mock_pipeline: MagicMock, tmp_path: Path
) -> None:
    """ingest_directory processes all 7 supported extensions, one file each."""
    for ext in ["txt", "md", "pdf", "docx", "html", "py", "ipynb"]:
        (tmp_path / f"sample.{ext}").write_bytes(b"placeholder")

    with patch("agentrag.server.tools.ingest", mock_pipeline):
        results = ingest_directory(directory_path=str(tmp_path))

    assert len(results) == 7
    assert mock_pipeline.call_count == 7
    assert all(r.status == "ok" for r in results)


# Phase 6 — multi-collection and streaming tool tests


@pytest.fixture
def mock_store_with_collections() -> MagicMock:
    """Mock QdrantStore with list_collections and create_collection support."""
    store = MagicMock()
    store.list_collections.return_value = ["documents"]
    store.create_collection.return_value = None
    return store


def test_list_collections_returns_list(
    mock_store_with_collections: MagicMock,
) -> None:
    """list_collections delegates to store.list_collections."""
    with patch(
        "agentrag.server.tools.QdrantStore", return_value=mock_store_with_collections
    ):
        result = list_collections()
    assert isinstance(result, list)
    assert "documents" in result
    mock_store_with_collections.list_collections.assert_called_once()


def test_create_collection_returns_created_message(
    mock_store_with_collections: MagicMock,
) -> None:
    """create_collection returns 'created' message for a new collection name."""
    mock_store_with_collections.list_collections.return_value = ["documents"]
    with patch(
        "agentrag.server.tools.QdrantStore", return_value=mock_store_with_collections
    ):
        result = create_collection("new_ws")
    assert "new_ws" in result
    assert "created" in result.lower()


def test_create_collection_returns_exists_message_when_duplicate(
    mock_store_with_collections: MagicMock,
) -> None:
    """create_collection returns 'already exists' when name is already present."""
    mock_store_with_collections.list_collections.return_value = ["documents", "new_ws"]
    with patch(
        "agentrag.server.tools.QdrantStore", return_value=mock_store_with_collections
    ):
        result = create_collection("new_ws")
    assert "already exists" in result.lower()
    mock_store_with_collections.create_collection.assert_not_called()


def test_create_collection_invalid_name_raises_valueerror() -> None:
    """create_collection raises ValueError for names with invalid characters."""
    with pytest.raises(ValueError, match="invalid characters"):
        create_collection("invalid name!")


def test_switch_collection_returns_confirmation(
    mock_store_with_collections: MagicMock,
    settings: Settings,
) -> None:
    """switch_collection mutates settings.collection and returns confirmation."""
    import agentrag.server.tools as tools_module

    original = settings.collection
    mock_store_with_collections.list_collections.return_value = ["documents", "ws_x"]
    with patch(
        "agentrag.server.tools.QdrantStore", return_value=mock_store_with_collections
    ):
        with patch.object(tools_module, "_active_settings", settings):
            result = switch_collection("ws_x")
    assert "ws_x" in result
    assert settings.collection == "ws_x"
    settings.collection = original  # restore


def test_switch_collection_nonexistent_raises_valueerror(
    mock_store_with_collections: MagicMock,
    settings: Settings,
) -> None:
    """switch_collection raises ValueError when collection does not exist."""
    import agentrag.server.tools as tools_module

    mock_store_with_collections.list_collections.return_value = ["documents"]
    with patch(
        "agentrag.server.tools.QdrantStore", return_value=mock_store_with_collections
    ):
        with patch.object(tools_module, "_active_settings", settings):
            with pytest.raises(ValueError, match="does not exist"):
                switch_collection("nonexistent_xyz")


def test_search_stream_returns_same_as_search_documents(
    mock_searcher: MagicMock,
) -> None:
    """search_stream returns same results as search_documents (batch fallback)."""
    with patch("agentrag.server.tools.search", mock_searcher):
        batch = search_documents(query="test", top_k=3)
    with patch("agentrag.server.tools.search", mock_searcher):
        streamed = search_stream(query="test", top_k=3)
    assert [r.chunk_id for r in batch] == [r.chunk_id for r in streamed]


def test_search_stream_empty_query_raises_valueerror() -> None:
    """search_stream raises ValueError on empty query string."""
    with pytest.raises(ValueError, match="query must not be empty"):
        search_stream(query="", top_k=5)
