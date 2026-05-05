"""Integration tests for Phase 6 streaming retrieval."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from agentrag.config import Settings
from agentrag.server import tools


@pytest.fixture(autouse=True)
def ingested_settings(tmp_path: Path) -> Generator[Settings, None, None]:
    """Fresh settings with sample.txt ingested; resets module state after test."""
    settings = Settings(data_dir=tmp_path)
    tools.set_active_settings(settings)
    sample_txt = Path(__file__).parent.parent / "fixtures" / "sample.txt"
    result = tools.ingest_file(str(sample_txt))
    assert result.status == "ok"
    yield settings
    tools.set_active_settings(None)


def test_search_stream_returns_results(ingested_settings: Settings) -> None:
    """search_stream returns at least one result for a broad query."""
    results = tools.search_stream("text", top_k=5)
    assert len(results) > 0
    assert all(hasattr(r, "chunk_id") for r in results)


def test_search_stream_parity_with_batch(ingested_settings: Settings) -> None:
    """search_stream returns identical chunk IDs in the same order as batch."""
    batch = tools.search_documents("text", top_k=5)
    streamed = tools.search_stream("text", top_k=5)
    assert [r.chunk_id for r in batch] == [r.chunk_id for r in streamed]
