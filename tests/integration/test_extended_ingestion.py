"""Integration tests for extended file type ingestion (Phase 3)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

from agentrag.ingestion.pipeline import ingest
from agentrag.retrieval.searcher import search
from agentrag.server.tools import ingest_directory
from agentrag.store.qdrant import QdrantStore

if TYPE_CHECKING:
    from agentrag.config import Settings


def test_ingest_docx(settings: Settings) -> None:
    """DOCX fixture ingests successfully with at least one chunk stored."""
    result = ingest(Path("tests/fixtures/sample.docx"), settings)
    assert result.status == "ok"
    assert result.chunk_count > 0


def test_ingest_html(settings: Settings) -> None:
    """HTML fixture ingests with body content retrievable, boilerplate absent."""
    result = ingest(Path("tests/fixtures/sample.html"), settings)
    assert result.status == "ok"
    assert result.chunk_count > 0

    # Body content is semantically searchable
    body_results = search("AgentRAG private memory documents", 5, settings)
    assert len(body_results) > 0
    # Tokenizer lowercases — check the lowercased sentinel form is present
    assert any("body" in r.text and "sentinel" in r.text for r in body_results)

    # Boilerplate sentinels must not appear in any stored chunk (tokenizer lowercases)
    store = QdrantStore(settings)
    _, full_text, _, _ = store.get_full_document(result.source_id)
    assert "nav _ sentinel" not in full_text
    assert "header _ sentinel" not in full_text
    assert "footer _ sentinel" not in full_text
    assert "script _ sentinel" not in full_text
    assert "style _ sentinel" not in full_text


def test_ingest_py(settings: Settings) -> None:
    """Python fixture ingests successfully; function names are retrievable."""
    result = ingest(Path("tests/fixtures/sample.py"), settings)
    assert result.status == "ok"
    assert result.chunk_count > 0

    results = search("split text into overlapping chunks", 5, settings)
    assert len(results) > 0
    # chunk_text function name present in at least one chunk (tokenized as chunk _ text)
    store = QdrantStore(settings)
    _, full_text, _, _ = store.get_full_document(result.source_id)
    assert "chunk" in full_text and "text" in full_text


def test_ingest_ipynb(settings: Settings) -> None:
    """Notebook fixture ingests; markdown cell sentinel is stored."""
    result = ingest(Path("tests/fixtures/sample.ipynb"), settings)
    assert result.status == "ok"
    assert result.chunk_count > 0

    results = search("notebook ingestion pipeline demonstration", 5, settings)
    assert len(results) > 0
    # Markdown sentinel stored (tokenized to lowercase with spaces)
    store = QdrantStore(settings)
    _, full_text, _, _ = store.get_full_document(result.source_id)
    assert "markdown" in full_text and "sentinel" in full_text
    # Raw cell sentinel must not appear
    assert "raw _ sentinel" not in full_text


def test_ingest_directory_mixed(settings: Settings) -> None:
    """ingest_directory on fixtures/ returns 7 ok results, one per supported type."""
    with patch("agentrag.server.tools.Settings", return_value=settings):
        results = ingest_directory(directory_path="tests/fixtures")

    assert len(results) == 7
    assert all(r.status == "ok" for r in results)
    assert all(r.chunk_count > 0 for r in results)
