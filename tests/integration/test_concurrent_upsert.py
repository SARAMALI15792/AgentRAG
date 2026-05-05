"""Integration tests — concurrent upsert safety (Phase 4, Group 4)."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from agentrag.config import Settings
from agentrag.ingestion.pipeline import ingest

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_concurrent_upsert_yields_single_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Three concurrent ingest calls on same file produce exactly 1 source entry."""
    monkeypatch.setenv("AGENTRAG_DATA_DIR", str(tmp_path))
    settings = Settings(data_dir=tmp_path)
    txt_path = FIXTURES / "sample.txt"

    errors: list[str] = []

    def _ingest() -> None:
        result = ingest(txt_path, settings)
        if result.status != "ok":
            errors.append(result.error or "unknown error")

    threads = [threading.Thread(target=_ingest) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert not errors, f"Ingest errors: {errors}"

    from agentrag.store.qdrant import QdrantStore

    store = QdrantStore(settings)
    sources = store.list_sources()

    assert (
        len(sources) == 1
    ), f"Expected 1 source after 3 concurrent ingests, got {len(sources)}"
    assert sources[0].filename == "sample.txt"
    assert sources[0].chunk_count > 0


def test_concurrent_upsert_chunk_count_stable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """chunk_count is deterministic across multiple concurrent ingest runs."""
    monkeypatch.setenv("AGENTRAG_DATA_DIR", str(tmp_path))
    settings = Settings(data_dir=tmp_path)
    txt_path = FIXTURES / "sample.txt"

    # Single ingest first to get reference chunk count
    ref = ingest(txt_path, settings)
    assert ref.status == "ok", ref.error
    expected_chunk_count = ref.chunk_count

    def _ingest() -> None:
        ingest(txt_path, settings)

    threads = [threading.Thread(target=_ingest) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    from agentrag.store.qdrant import QdrantStore

    store = QdrantStore(settings)
    sources = store.list_sources()

    assert len(sources) == 1
    assert (
        sources[0].chunk_count == expected_chunk_count
    ), f"Expected {expected_chunk_count} chunks, got {sources[0].chunk_count}"
