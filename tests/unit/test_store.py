from __future__ import annotations

from agentrag.config import Settings
from agentrag.store.qdrant import QdrantStore
from agentrag.types import EmbeddedChunk, SearchResult, SourceInfo


def _make_chunks(
    source_id: str, n: int, filename: str = "test.txt"
) -> list[EmbeddedChunk]:
    chunks = []
    for i in range(n):
        v = [0.0] * 384
        v[i % 384] = 1.0
        chunks.append(
            EmbeddedChunk(
                chunk_id=f"{source_id}_{i}",
                source_id=source_id,
                text=f"chunk {i}",
                vector=v,
                metadata={"filename": filename},
            )
        )
    return chunks


def test_upsert_then_query_returns_chunks(settings: Settings) -> None:
    store = QdrantStore(settings)
    chunks = _make_chunks("src1", 3)
    store.upsert(chunks)
    results = store.query(chunks[0].vector, top_k=3)
    assert len(results) > 0
    assert all(isinstance(r, SearchResult) for r in results)


def test_upsert_same_source_id_twice_no_duplication(settings: Settings) -> None:
    store = QdrantStore(settings)
    chunks = _make_chunks("src1", 3)
    store.upsert(chunks)
    store.upsert(chunks)
    sources = store.list_sources()
    assert len(sources) == 1
    assert sources[0].chunk_count == 3


def test_delete_removes_all_points_for_source(settings: Settings) -> None:
    store = QdrantStore(settings)
    chunks = _make_chunks("src1", 3)
    store.upsert(chunks)
    count = store.delete("src1")
    assert count == 3
    results = store.query(chunks[0].vector, top_k=10)
    assert results == []


def test_list_sources_returns_correct_source_info(settings: Settings) -> None:
    store = QdrantStore(settings)
    chunks = _make_chunks("src1", 3)
    store.upsert(chunks)
    sources = store.list_sources()
    assert len(sources) == 1
    assert isinstance(sources[0], SourceInfo)
    assert sources[0].source_id == "src1"
    assert sources[0].chunk_count == 3
    assert sources[0].filename == "test.txt"


def test_query_empty_collection_returns_empty_list(settings: Settings) -> None:
    store = QdrantStore(settings)
    results = store.query([0.1] * 384, top_k=5)
    assert results == []


def test_list_sources_empty_store_returns_empty_list(settings: Settings) -> None:
    store = QdrantStore(settings)
    sources = store.list_sources()
    assert sources == []


def test_filter_sources_by_filename(settings: Settings) -> None:
    """filter_sources with filename filter returns only matching source."""
    store = QdrantStore(settings)
    store.upsert(_make_chunks("src1", 2, filename="doc.txt"))
    store.upsert(_make_chunks("src2", 2, filename="other.txt"))
    results = store.filter_sources({"filename": "doc.txt"})
    assert len(results) == 1
    assert results[0].source_id == "src1"


def test_filter_sources_by_source_id(settings: Settings) -> None:
    """filter_sources with source_id filter returns correct source."""
    store = QdrantStore(settings)
    store.upsert(_make_chunks("src1", 2))
    store.upsert(_make_chunks("src2", 2))
    results = store.filter_sources({"source_id": "src1"})
    assert len(results) == 1
    assert results[0].source_id == "src1"


def test_filter_sources_no_match_returns_empty(settings: Settings) -> None:
    """filter_sources with no matching source returns empty list."""
    store = QdrantStore(settings)
    store.upsert(_make_chunks("src1", 2, filename="doc.txt"))
    results = store.filter_sources({"filename": "nonexistent.txt"})
    assert results == []


def test_filter_sources_multiple_criteria(settings: Settings) -> None:
    """filter_sources with two conditions returns only source matching both."""
    store = QdrantStore(settings)
    store.upsert(_make_chunks("src1", 2, filename="doc.txt"))
    store.upsert(_make_chunks("src2", 2, filename="doc.txt"))
    results = store.filter_sources({"filename": "doc.txt", "source_id": "src1"})
    assert len(results) == 1
    assert results[0].source_id == "src1"
