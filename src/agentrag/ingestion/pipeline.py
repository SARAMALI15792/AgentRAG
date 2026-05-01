"""Ingestion pipeline — orchestrates reader → chunker → embedder ��� store."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from agentrag.config import Settings
from agentrag.ingestion.chunker import chunk_document
from agentrag.ingestion.embedder import embed_chunks
from agentrag.ingestion.reader import read_file
from agentrag.store.qdrant import QdrantStore
from agentrag.types import IngestResult, RawDocument

logger = logging.getLogger(__name__)


def ingest(path: Path, settings: Settings) -> IngestResult:
    """Ingest a file: read → chunk → embed → store. Never raises."""
    try:
        # Read file
        doc = read_file(path)

        # Chunk text
        chunks = chunk_document(doc, settings)

        # Embed chunks
        metadata = {"filename": doc.filename}
        embedded_chunks = embed_chunks(chunks, settings, metadata=metadata)

        # Store in Qdrant
        store = QdrantStore(settings)
        store.upsert(embedded_chunks)

        return IngestResult(
            source_id=doc.source_id,
            filename=doc.filename,
            chunk_count=len(embedded_chunks),
            status="ok",
            error=None,
        )

    except Exception as e:
        # Catch all exceptions and surface as IngestResult(status="error")
        logger.exception("Ingestion failed for %s", path)
        return IngestResult(
            source_id="",
            filename=path.name,
            chunk_count=0,
            status="error",
            error=str(e),
        )


def ingest_raw(doc: RawDocument, settings: Settings) -> IngestResult:
    """Ingest a pre-built RawDocument: chunk → embed → store. Never raises."""
    try:
        chunks = chunk_document(doc, settings)
        metadata = {"filename": doc.filename}
        embedded_chunks = embed_chunks(chunks, settings, metadata=metadata)
        store = QdrantStore(settings)
        store.upsert(embedded_chunks)
        return IngestResult(
            source_id=doc.source_id,
            filename=doc.filename,
            chunk_count=len(embedded_chunks),
            status="ok",
        )
    except Exception as e:
        logger.exception("Ingestion failed for raw doc %s", doc.source_id)
        return IngestResult(
            source_id=doc.source_id,
            filename=doc.filename,
            chunk_count=0,
            status="error",
            error=str(e),
        )


def ingest_url(
    url: str, settings: Settings, metadata: dict[str, str] | None = None
) -> IngestResult:
    """Fetch a URL and ingest its text content. Never raises."""
    try:
        from agentrag.ingestion.readers.web import read_url

        text = read_url(url)
        normalized = url.lower().rstrip("/")
        source_id = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        extra: dict[str, str] = {"source_url": url}
        if metadata:
            extra.update(metadata)
        doc = RawDocument(source_id=source_id, filename=url, text=text, metadata=extra)
        return ingest_raw(doc, settings)
    except Exception as e:
        logger.exception("URL ingestion failed for %s", url)
        return IngestResult(
            source_id="",
            filename=url,
            chunk_count=0,
            status="error",
            error=str(e),
        )
