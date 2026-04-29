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

_COLLECTION = "documents"


class QdrantStore:
    def __init__(self, settings: Settings) -> None:
        qdrant_path = settings.data_dir / "qdrant"
        qdrant_path.mkdir(parents=True, exist_ok=True)
        self._client = QdrantClient(path=str(qdrant_path))
        self._vector_dim = settings.vector_dim
        if not self._client.collection_exists(_COLLECTION):
            self._client.create_collection(
                _COLLECTION,
                vectors_config=VectorParams(
                    size=self._vector_dim, distance=Distance.COSINE
                ),
            )

    def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        if not chunks:
            return
        self._delete_by_source(chunks[0].source_id)
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
        self._client.upsert(_COLLECTION, points=points, wait=True)

    def query(
        self,
        vector: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        query_filter: Filter | None = None
        if filters:
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
        sources: dict[str, SourceInfo] = {}
        offset: Any = None
        while True:
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

    def _delete_by_source(self, source_id: str) -> None:
        self._client.delete(
            _COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(key="source_id", match=MatchValue(value=source_id))
                ]
            ),
            wait=True,
        )
