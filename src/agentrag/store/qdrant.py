from __future__ import annotations

import uuid
from datetime import UTC, datetime
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

_COLLECTION = "documents"  # single Qdrant collection for all ingested content


class QdrantStore:
    """Persistent vector store backed by Qdrant embedded (in-process, no server)."""

    def __init__(self, settings: Settings) -> None:
        """Open or create the Qdrant collection at settings.data_dir/qdrant."""
        qdrant_path = settings.data_dir / "qdrant"
        qdrant_path.mkdir(parents=True, exist_ok=True)
        self._client = QdrantClient(path=str(qdrant_path))
        self._vector_dim = settings.vector_dim
        # Create collection only on first run; leave existing data intact on restart.
        if not self._client.collection_exists(_COLLECTION):
            self._client.create_collection(
                _COLLECTION,
                vectors_config=VectorParams(
                    size=self._vector_dim, distance=Distance.COSINE
                ),
            )

    def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        """Replace all stored chunks for the source with the new set (idempotent)."""
        if not chunks:
            return
        # Delete first so re-ingesting the same file never accumulates duplicates.
        self._delete_by_source(chunks[0].source_id)
        ingested_at = datetime.now(UTC).isoformat()
        points = [
            PointStruct(
                # uuid5: deterministic ID per chunk_id — stable across re-ingests.
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
        self._client.upsert(_COLLECTION, points=points, wait=True)

    def query(
        self,
        vector: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Return up to top_k chunks ranked by cosine similarity to vector."""
        query_filter: Filter | None = None
        if filters:
            # Each key-value pair in filters becomes a must-match condition.
            query_filter = Filter(
                must=[
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filters.items()
                ]
            )
        response = self._client.query_points(
            _COLLECTION,
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

    def delete(self, source_id: str) -> int:
        """Delete all chunks for source_id and return the count removed."""
        # Count first so the caller knows whether the source existed.
        count_result = self._client.count(
            _COLLECTION,
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
            # Paginate with scroll; next_offset is None when the last page is reached.
            points, next_offset = self._client.scroll(
                _COLLECTION,
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

    def get_full_document(
        self, source_id: str
    ) -> tuple[str, str, str, dict[str, Any]]:
        """Retrieve all chunks for source_id and return assembled document."""
        # Query all chunks for this source_id
        results = self.query(
            vector=[0.0] * self._vector_dim,  # dummy vector — filter by source_id
            top_k=10000,  # large limit to get all chunks
            filters={"source_id": source_id},
        )

        if not results:
            raise ValueError(f"source_id {source_id!r} not found")

        # Sort by chunk_id to preserve order (chunk_id format: "{source_id}_{index}")
        results.sort(key=lambda r: r.chunk_id)

        full_text = "".join(r.text for r in results)

        return results[0].filename, full_text, source_id, results[0].metadata

    def _delete_by_source(self, source_id: str) -> None:
        """Remove all Qdrant points whose payload source_id matches."""
        self._client.delete(
            _COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(key="source_id", match=MatchValue(value=source_id))
                ]
            ),
            wait=True,
        )
