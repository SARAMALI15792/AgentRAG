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
