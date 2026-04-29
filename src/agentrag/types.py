from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class RawDocument:
    source_id: str
    filename: str
    text: str
    metadata: dict[str, Any]


@dataclass
class Chunk:
    chunk_id: str
    source_id: str
    text: str
    start_char: int
    end_char: int
    index: int


@dataclass
class EmbeddedChunk:
    chunk_id: str
    source_id: str
    text: str
    vector: list[float]
    metadata: dict[str, Any]


@dataclass
class SearchResult:
    chunk_id: str
    source_id: str
    filename: str
    text: str
    score: float
    metadata: dict[str, Any]


@dataclass
class SourceInfo:
    source_id: str
    filename: str
    chunk_count: int
    metadata: dict[str, Any]
    ingested_at: str


@dataclass
class IngestResult:
    source_id: str
    filename: str
    chunk_count: int
    status: Literal["ok", "error"]
    error: str | None = None


@dataclass
class DeleteResult:
    source_id: str
    chunks_deleted: int
    status: Literal["ok", "not_found", "error"]


@dataclass
class DocumentContent:
    source_id: str
    filename: str
    full_text: str
    metadata: dict[str, Any]
