"""Integration tests for Phase 3B extended file type ingestion."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentrag.config import Settings
from agentrag.ingestion.pipeline import ingest

FIXTURES = Path("tests/fixtures")


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Settings backed by a temp Qdrant directory."""
    return Settings(data_dir=tmp_path / "qdrant")


@pytest.mark.parametrize(
    "filename",
    [
        "sample.xlsx",
        "sample.pptx",
        "sample.csv",
        "sample.epub",
        "sample.json",
        "sample.yaml",
        "sample.xml",
        "sample.toml",
        "sample.srt",
        "sample.eml",
    ],
)
def test_ingest_new_file_type_produces_chunks(
    filename: str, settings: Settings
) -> None:
    """Each new Phase 3B file type ingests into real Qdrant with chunk_count > 0."""
    result = ingest(FIXTURES / filename, settings)
    assert result.status == "ok", f"{filename} ingestion failed: {result.error}"
    assert result.chunk_count > 0, f"{filename} produced 0 chunks"
    assert len(result.source_id) == 16


def test_ingest_directory_mixed_types(settings: Settings, tmp_path: Path) -> None:
    """ingest_directory on a mixed directory ingests all supported new types."""
    import os
    import shutil

    from agentrag.server.tools import ingest_directory

    mixed_dir = tmp_path / "mixed"
    mixed_dir.mkdir()

    for name in [
        "sample.xlsx",
        "sample.pptx",
        "sample.csv",
        "sample.epub",
        "sample.json",
        "sample.yaml",
        "sample.xml",
        "sample.toml",
        "sample.srt",
        "sample.eml",
    ]:
        shutil.copy(FIXTURES / name, mixed_dir / name)

    # Override settings so tools create their own store in the same tmp dir
    os.environ["AGENTRAG_DATA_DIR"] = str(tmp_path / "qdrant")
    try:
        results = ingest_directory(str(mixed_dir))
    finally:
        del os.environ["AGENTRAG_DATA_DIR"]

    ok_results = [r for r in results if r.status == "ok"]
    assert len(ok_results) == 10, (
        f"Expected 10 ok results, got {len(ok_results)}. "
        f"Errors: {[r for r in results if r.status == 'error']}"
    )
    assert all(r.chunk_count > 0 for r in ok_results)


def test_ingest_same_file_twice_is_idempotent(settings: Settings) -> None:
    """Re-ingesting a file updates chunks without duplicating the source."""
    from agentrag.store.qdrant import QdrantStore

    result1 = ingest(FIXTURES / "sample.json", settings)
    result2 = ingest(FIXTURES / "sample.json", settings)

    assert result1.status == "ok"
    assert result2.status == "ok"
    assert result1.source_id == result2.source_id

    store = QdrantStore(settings)
    sources = store.list_sources()
    json_sources = [s for s in sources if s.filename == "sample.json"]
    assert len(json_sources) == 1, "Re-ingestion must not duplicate the source"
