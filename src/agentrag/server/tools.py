"""MCP tool handlers — thin delegates to ingestion, retrieval, and store."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentrag.config import Settings
from agentrag.ingestion import reader_registry
from agentrag.ingestion.pipeline import ingest
from agentrag.ingestion.pipeline import ingest_url as _ingest_url
from agentrag.retrieval import evaluator, query_planner
from agentrag.retrieval.searcher import search
from agentrag.store.qdrant import QdrantStore
from agentrag.types import (
    DeleteResult,
    DocumentContent,
    EvaluationReport,
    IngestResult,
    QueryPlan,
    SearchResult,
    SourceInfo,
)

# Session-scoped shared settings — mutated by switch_collection.
_active_settings: Settings | None = None


def set_active_settings(settings: Settings | None) -> None:
    """Set or clear the shared settings instance used by all tool handlers."""
    global _active_settings
    _active_settings = settings


def _get_settings() -> Settings:
    """Return the shared settings instance, or a fresh one if not set."""
    return _active_settings if _active_settings is not None else Settings()


def _is_valid_collection_name(name: str) -> bool:
    """Return True if name contains only alphanumeric characters and underscores."""
    return bool(name) and all(c.isalnum() or c == "_" for c in name)


def ingest_file(file_path: str) -> IngestResult:
    """Ingest a single file into the vector store."""
    path = Path(file_path)
    return ingest(path, _get_settings())


def ingest_directory(directory_path: str) -> list[IngestResult]:
    """Ingest all supported files in a directory recursively."""
    settings = _get_settings()
    dir_path = Path(directory_path)

    if not dir_path.is_dir():
        return []

    results: list[IngestResult] = []
    for ext in reader_registry.supported_extensions():
        for file_path in dir_path.rglob(f"*{ext}"):
            result = ingest(file_path, settings)
            results.append(result)

    return results


def plan_query(query: str) -> QueryPlan:
    """Decompose a query into focused sub-queries via Gemini."""
    return query_planner.plan(query, _get_settings())


def search_multi(queries: list[str], top_k: int = 5) -> list[SearchResult]:
    """Search with multiple queries and deduplicate results by chunk_id."""
    if not queries:
        raise ValueError("queries list must not be empty")
    settings = _get_settings()
    seen: dict[str, SearchResult] = {}
    for q in queries:
        for result in search(q, top_k, settings):
            existing = seen.get(result.chunk_id)
            if existing is None or result.score > existing.score:
                seen[result.chunk_id] = result
    return sorted(seen.values(), key=lambda r: r.score, reverse=True)


def evaluate_chunks(query: str, results: list[SearchResult]) -> EvaluationReport:
    """Score each chunk's relevance to the query."""
    return evaluator.evaluate(query, results, _get_settings())


def ingest_url(url: str, metadata: dict[str, str] | None = None) -> IngestResult:
    """Fetch a web page and ingest its text content."""
    return _ingest_url(url, _get_settings(), metadata)


def search_documents(
    query: str, top_k: int = 5, filters: dict[str, Any] | None = None
) -> list[SearchResult]:
    """Search documents by semantic similarity."""
    if not query.strip():
        raise ValueError("query must not be empty")
    return search(query, top_k, _get_settings(), filters)


def search_by_metadata(filters: dict[str, Any]) -> list[SourceInfo]:
    """Search sources by metadata filters."""
    if not filters:
        raise ValueError("filters must not be empty")
    store = QdrantStore(_get_settings())
    return store.filter_sources(filters)


def list_sources() -> list[SourceInfo]:
    """List all ingested sources."""
    store = QdrantStore(_get_settings())
    return store.list_sources()


def get_document(source_id: str) -> DocumentContent:
    """Retrieve full document text by source_id."""
    store = QdrantStore(_get_settings())
    filename, full_text, source_id, metadata = store.get_full_document(source_id)
    return DocumentContent(
        source_id=source_id,
        filename=filename,
        full_text=full_text,
        metadata=metadata,
    )


def delete_source(source_id: str) -> DeleteResult:
    """Delete all chunks for a source."""
    store = QdrantStore(_get_settings())
    chunks_deleted = store.delete(source_id)
    if chunks_deleted == 0:
        return DeleteResult(source_id=source_id, chunks_deleted=0, status="not_found")
    return DeleteResult(source_id=source_id, chunks_deleted=chunks_deleted, status="ok")


# Phase 6 — multi-collection tools


def list_collections() -> list[str]:
    """List all named Qdrant collections."""
    store = QdrantStore(_get_settings())
    return store.list_collections()


def create_collection(name: str) -> str:
    """Create a new named collection (idempotent)."""
    if not _is_valid_collection_name(name):
        raise ValueError(
            f"Collection name '{name}' contains invalid characters. "
            "Use alphanumeric characters and underscores only."
        )
    store = QdrantStore(_get_settings())
    existing = store.list_collections()
    if name in existing:
        return f"Collection '{name}' already exists."
    store.create_collection(name)
    return f"Collection '{name}' created."


def switch_collection(name: str) -> str:
    """Set the active collection for this session."""
    settings = _get_settings()
    store = QdrantStore(settings)
    existing = store.list_collections()
    if name not in existing:
        raise ValueError(
            f"Collection '{name}' does not exist. "
            f"Create it first with: create_collection('{name}')"
        )
    settings.collection = name
    return f"Active collection set to '{name}'."


def search_stream(query: str, top_k: int = 5) -> list[SearchResult]:
    """Streaming search — batch fallback (MCP SDK does not support async generators)."""
    if not query.strip():
        raise ValueError("query must not be empty")
    return search(query, top_k, _get_settings())
