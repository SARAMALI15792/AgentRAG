from __future__ import annotations

import logging
import shutil
import tarfile
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from agentrag.config import Settings
from agentrag.types import EmbeddedChunk, SearchResult, SourceInfo

logger = logging.getLogger(__name__)

# One QdrantClient per path — Linux portalocker forbids multiple clients on same path.
_client_cache: dict[str, QdrantClient] = {}
_cache_lock = threading.Lock()

# Per-path lock serialises delete+upsert so concurrent ingests stay idempotent.
_upsert_locks: dict[str, threading.Lock] = {}


def _close_all_clients() -> None:
    """Close all cached Qdrant clients and clear the cache (test/cleanup helper)."""
    with _cache_lock:
        for client in list(_client_cache.values()):
            try:
                client.close()
            except Exception as exc:
                logger.warning("Failed to close Qdrant client: %s", exc)
        _client_cache.clear()
        _upsert_locks.clear()


class QdrantStore:
    """Persistent vector store backed by Qdrant embedded (in-process, no server)."""

    def __init__(self, settings: Settings) -> None:
        """Open or create the Qdrant collection named by settings.collection."""
        from pathlib import Path

        qdrant_path = str((settings.data_dir / "qdrant").resolve())
        with _cache_lock:
            if qdrant_path not in _client_cache:
                Path(qdrant_path).mkdir(parents=True, exist_ok=True)
                _client_cache[qdrant_path] = QdrantClient(path=qdrant_path)
            if qdrant_path not in _upsert_locks:
                _upsert_locks[qdrant_path] = threading.Lock()
        self._client = _client_cache[qdrant_path]
        self._upsert_lock = _upsert_locks[qdrant_path]
        self._settings = settings  # live reference — collection name read at call time
        self._vector_dim = settings.vector_dim
        if not self._client.collection_exists(settings.collection):
            self._client.create_collection(
                settings.collection,
                vectors_config=VectorParams(
                    size=self._vector_dim, distance=Distance.COSINE
                ),
            )

    @property
    def _active_collection(self) -> str:
        """Current collection name from live settings."""
        return self._settings.collection

    def create_collection(self, name: str) -> None:
        """Create a named collection if it does not already exist (idempotent)."""
        if not self._client.collection_exists(name):
            self._client.create_collection(
                name,
                vectors_config=VectorParams(
                    size=self._vector_dim, distance=Distance.COSINE
                ),
            )

    def list_collections(self) -> list[str]:
        """Return alphabetically sorted list of all collection names."""
        return sorted(c.name for c in self._client.get_collections().collections)

    def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        """Replace all stored chunks for the source with the new set (idempotent)."""
        if not chunks:
            return
        ingested_at = datetime.now(UTC).isoformat()
        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id)),
                vector=chunk.vector,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "source_id": chunk.source_id,
                    "text": chunk.text,
                    "filename": chunk.metadata.get("filename", ""),
                    "ingested_at": ingested_at,
                    "metadata": chunk.metadata,
                },
            )
            for chunk in chunks
        ]
        with self._upsert_lock:
            self._delete_by_source(chunks[0].source_id)
            self._client.upsert(self._active_collection, points=points, wait=True)

    def query(
        self,
        vector: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Return up to top_k chunks ranked by cosine similarity to vector."""
        query_filter: Filter | None = None
        if filters:
            query_filter = Filter(
                must=[
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filters.items()
                ]
            )
        response = self._client.query_points(
            self._active_collection,
            query=vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        results: list[SearchResult] = []
        for point in response.points:
            payload: dict[str, Any] = point.payload or {}
            results.append(
                SearchResult(
                    chunk_id=str(payload.get("chunk_id", "")),
                    source_id=str(payload.get("source_id", "")),
                    filename=str(payload.get("filename", "")),
                    text=str(payload.get("text", "")),
                    score=point.score,
                    metadata=dict(payload.get("metadata") or {}),
                )
            )
        return results

    def filter_sources(self, filters: dict[str, Any]) -> list[SourceInfo]:
        """Return sources where every filter key-value pair matches."""
        return [
            s
            for s in self.list_sources()
            if all(
                s.metadata.get(k) == v or getattr(s, k, None) == v
                for k, v in filters.items()
            )
        ]

    def delete(self, source_id: str) -> int:
        """Delete all chunks for source_id and return the count removed."""
        count_result = self._client.count(
            self._active_collection,
            count_filter=Filter(
                must=[
                    FieldCondition(key="source_id", match=MatchValue(value=source_id))
                ]
            ),
            exact=True,
        )
        n = count_result.count
        if n > 0:
            self._delete_by_source(source_id)
        return n

    def list_sources(self) -> list[SourceInfo]:
        """Return one SourceInfo per unique source_id across all stored chunks."""
        sources: dict[str, SourceInfo] = {}
        offset: Any = None  # Any: PointId union type varies by qdrant-client version
        while True:
            points, next_offset = self._client.scroll(
                self._active_collection,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in points:
                payload: dict[str, Any] = point.payload or {}
                sid = str(payload.get("source_id", ""))
                if sid not in sources:
                    sources[sid] = SourceInfo(
                        source_id=sid,
                        filename=str(payload.get("filename", "")),
                        chunk_count=1,
                        metadata=dict(payload.get("metadata") or {}),
                        ingested_at=str(payload.get("ingested_at", "")),
                    )
                else:
                    sources[sid].chunk_count += 1
            if next_offset is None:
                break
            offset = next_offset
        return list(sources.values())

    def get_full_document(self, source_id: str) -> tuple[str, str, str, dict[str, Any]]:
        """Retrieve all chunks for source_id and return assembled document."""
        results = self.query(
            vector=[0.0] * self._vector_dim,
            top_k=10000,
            filters={"source_id": source_id},
        )
        if not results:
            raise ValueError(f"source_id {source_id!r} not found")
        results.sort(key=lambda r: r.chunk_id)
        full_text = "".join(r.text for r in results)
        return results[0].filename, full_text, source_id, results[0].metadata

    def create_snapshot(self, dest_dir: Path) -> Path:
        """Close client, archive Qdrant data directory, reopen client."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        qdrant_path_str = str((self._settings.data_dir / "qdrant").resolve())
        qdrant_dir = Path(qdrant_path_str)
        # Close client to release file locks before archiving (required on Windows)
        with _cache_lock:
            client = _client_cache.pop(qdrant_path_str, None)
            _upsert_locks.pop(qdrant_path_str, None)
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
        try:
            ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            snapshot_path = dest_dir / f"snapshot_{ts}.snapshot"
            with tarfile.open(snapshot_path, "w:gz") as tf:
                tf.add(str(qdrant_dir), arcname="qdrant")
        finally:
            # Always reopen so the store remains usable
            with _cache_lock:
                new_client = QdrantClient(path=qdrant_path_str)
                _client_cache[qdrant_path_str] = new_client
                _upsert_locks[qdrant_path_str] = threading.Lock()
            self._client = new_client
            self._upsert_lock = _upsert_locks[qdrant_path_str]
        return snapshot_path

    def recover_snapshot(self, snapshot_path: Path) -> None:
        """Close client, replace data directory from snapshot, reopen."""
        qdrant_path_str = str((self._settings.data_dir / "qdrant").resolve())
        qdrant_dir = Path(qdrant_path_str)
        with _cache_lock:
            client = _client_cache.pop(qdrant_path_str, None)
            _upsert_locks.pop(qdrant_path_str, None)
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
        if qdrant_dir.exists():
            shutil.rmtree(qdrant_dir)
        with tarfile.open(snapshot_path, "r:gz") as tf:
            tf.extractall(str(self._settings.data_dir), filter="data")
        with _cache_lock:
            new_client = QdrantClient(path=qdrant_path_str)
            _client_cache[qdrant_path_str] = new_client
            _upsert_locks[qdrant_path_str] = threading.Lock()
        self._client = new_client
        self._upsert_lock = _upsert_locks[qdrant_path_str]

    def _delete_by_source(self, source_id: str) -> None:
        """Remove all Qdrant points whose payload source_id matches."""
        self._client.delete(
            self._active_collection,
            points_selector=Filter(
                must=[
                    FieldCondition(key="source_id", match=MatchValue(value=source_id))
                ]
            ),
            wait=True,
        )
