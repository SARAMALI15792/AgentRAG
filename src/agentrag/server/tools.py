"""MCP tool handlers — thin delegates to ingestion, retrieval, and store."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentrag.config import Settings
from agentrag.ingestion.pipeline import ingest
from agentrag.retrieval.searcher import search
from agentrag.store.qdrant import QdrantStore
from agentrag.types import (
    DeleteResult,
    DocumentContent,
    IngestResult,
    SearchResult,
    SourceInfo,
)


def ingest_file(file_path: str) -> IngestResult:
    """Ingest a single file into the vector store."""
    settings = Settings()
    path = Path(file_path)
    return ingest(path, settings)


def ingest_directory(directory_path: str) -> list[IngestResult]:
    """Ingest all supported files in a directory recursively."""
    settings = Settings()
    dir_path = Path(directory_path)

    if not dir_path.is_dir():
        return []

    results: list[IngestResult] = []
    # Phase 2: only .txt, .md, .pdf (Phase 1 file types)
    for ext in ["*.txt", "*.md", "*.pdf"]:
        for file_path in dir_path.rglob(ext):
            result = ingest(file_path, settings)
            results.append(result)

    return results


def search_documents(
    query: str, top_k: int = 5, filters: dict[str, Any] | None = None
) -> list[SearchResult]:
    """Search documents by semantic similarity."""
    if not query.strip():
        raise ValueError("query must not be empty")

    settings = Settings()
    return search(query, top_k, settings, filters)


def search_by_metadata(filters: dict[str, Any]) -> list[SourceInfo]:
    """Search sources by metadata filters."""
    if not filters:
        raise ValueError("filters must not be empty")

    settings = Settings()
    store = QdrantStore(settings)
    # Filter list_sources results by matching metadata
    all_sources = store.list_sources()

    matched: list[SourceInfo] = []
    for source in all_sources:
        # Check if all filter key-value pairs match
        if all(
            source.metadata.get(k) == v or getattr(source, k, None) == v
            for k, v in filters.items()
        ):
            matched.append(source)

    return matched


def list_sources() -> list[SourceInfo]:
    """List all ingested sources."""
    settings = Settings()
    store = QdrantStore(settings)
    return store.list_sources()


def get_document(source_id: str) -> DocumentContent:
    """Retrieve full document text by source_id."""
    settings = Settings()
    store = QdrantStore(settings)

    # Query all chunks for this source_id, sorted by chunk_id (which includes index)
    results = store.query(
        vector=[0.0] * settings.vector_dim,  # dummy vector — we filter by source_id
        top_k=10000,  # large limit to get all chunks
        filters={"source_id": source_id},
    )

    if not results:
        raise ValueError(f"source_id {source_id!r} not found")

    # Sort by chunk_id to preserve order (chunk_id format: "{source_id}_{index}")
    results.sort(key=lambda r: r.chunk_id)

    full_text = "".join(r.text for r in results)

    return DocumentContent(
        source_id=source_id,
        filename=results[0].filename,
        full_text=full_text,
        metadata=results[0].metadata,
    )


def delete_source(source_id: str) -> DeleteResult:
    """Delete all chunks for a source."""
    settings = Settings()
    store = QdrantStore(settings)

    chunks_deleted = store.delete(source_id)

    if chunks_deleted == 0:
        return DeleteResult(source_id=source_id, chunks_deleted=0, status="not_found")

    return DeleteResult(source_id=source_id, chunks_deleted=chunks_deleted, status="ok")
