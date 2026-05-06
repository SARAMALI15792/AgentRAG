from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class RawDocument:
    """Raw text extracted from a file before chunking."""

    source_id: str  # stable SHA-256 hex of resolved file path (16 chars)
    filename: str
    text: str
    metadata: dict[str, Any]


@dataclass
class Chunk:
    """A single sliding-window text slice of a RawDocument."""

    chunk_id: str  # format: "{source_id}_{index}"
    source_id: str
    text: str
    start_char: int
    end_char: int
    index: int  # zero-based position within the source


@dataclass
class EmbeddedChunk:
    """A Chunk paired with its dense embedding vector."""

    chunk_id: str
    source_id: str
    text: str
    vector: list[float]  # length must equal Settings.vector_dim (384)
    metadata: dict[str, Any]  # carries "filename" key set by the pipeline


@dataclass
class SearchResult:
    """A single ranked retrieval result returned to the caller."""

    chunk_id: str
    source_id: str
    filename: str
    text: str
    score: float  # cosine similarity in [0.0, 1.0]
    metadata: dict[str, Any]


@dataclass
class SourceInfo:
    """Summary metadata for one ingested source file."""

    source_id: str
    filename: str
    chunk_count: int
    metadata: dict[str, Any]
    ingested_at: str  # ISO 8601 UTC timestamp set at upsert time


@dataclass
class IngestResult:
    """Outcome of a single file ingestion attempt."""

    source_id: str
    filename: str
    chunk_count: int
    status: Literal["ok", "error"]
    error: str | None = None  # populated only when status == "error"


@dataclass
class DeleteResult:
    """Outcome of a delete-source operation."""

    source_id: str
    chunks_deleted: int
    status: Literal["ok", "not_found", "error"]


@dataclass
class DocumentContent:
    """Full reconstructed text of an ingested source (chunks joined in order)."""

    source_id: str
    filename: str
    full_text: str
    metadata: dict[str, Any]


@dataclass
class QueryPlan:
    """A decomposed query plan produced by the query planner."""

    original_query: str
    sub_queries: list[str]  # 1–4 focused sub-questions; always includes original


@dataclass
class ChunkScore:
    """Relevance score for one chunk against a query."""

    chunk_id: str
    source_id: str
    score: float  # 0.0 (irrelevant) → 1.0 (directly answers query)
    reason: str  # one-sentence explanation


@dataclass
class EvaluationReport:
    """Chunk relevance evaluation report produced by the evaluator."""

    query: str
    scored_chunks: list[ChunkScore]
    sufficient: bool  # True if any chunk scores >= 0.7
    suggested_queries: list[str]  # alternative queries when not sufficient


@dataclass
class SyncResult:
    """Outcome of a sync push or pull operation."""

    status: Literal["ok", "error"]
    message: str
    snapshot_id: str | None = None  # set on successful push


@dataclass
class SyncStatus:
    """Current state of the sync backend."""

    backend: str  # "local" or "s3"
    last_push: str | None  # ISO 8601 or None
    last_pull: str | None  # ISO 8601 or None
    snapshot_count: int
