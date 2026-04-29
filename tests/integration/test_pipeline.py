from __future__ import annotations

from pathlib import Path

from agentrag.config import Settings
from agentrag.ingestion.pipeline import ingest
from agentrag.store.qdrant import QdrantStore


def test_ingest_sample_txt(settings: Settings) -> None:
    """Ingest sample.txt produces chunks."""
    txt_path = Path("tests/fixtures/sample.txt")
    result = ingest(txt_path, settings)
    assert result.status == "ok"
    assert result.chunk_count > 0


def test_ingest_sample_pdf(settings: Settings) -> None:
    """Ingest sample.pdf produces chunks."""
    pdf_path = Path("tests/fixtures/sample.pdf")
    result = ingest(pdf_path, settings)
    assert result.status == "ok"
    assert result.chunk_count > 0


def test_reingest_produces_same_count(settings: Settings) -> None:
    """Re-ingesting same file produces identical chunk count (dedup)."""
    txt_path = Path("tests/fixtures/sample.txt")
    result1 = ingest(txt_path, settings)
    result2 = ingest(txt_path, settings)
    assert result1.status == "ok"
    assert result2.status == "ok"
    assert result1.chunk_count == result2.chunk_count


def test_list_sources_after_ingest(settings: Settings) -> None:
    """list_sources returns ingested source after ingest."""
    txt_path = Path("tests/fixtures/sample.txt")
    result = ingest(txt_path, settings)
    assert result.status == "ok"

    store = QdrantStore(settings)
    sources = store.list_sources()
    assert len(sources) > 0
    assert any(s.source_id == result.source_id for s in sources)
