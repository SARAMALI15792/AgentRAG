"""Integration tests — metadata filter hardening (Phase 4, Group 1)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from agentrag.config import Settings
from agentrag.ingestion.pipeline import ingest, ingest_raw
from agentrag.server.tools import search_by_metadata, search_documents
from agentrag.types import RawDocument

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _make_source_id(path: Path) -> str:
    """Reproduce the source_id formula from reader.py."""
    return hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]


def test_search_documents_filter_by_filename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """search_documents with filename filter returns only chunks from that file."""
    monkeypatch.setenv("AGENTRAG_DATA_DIR", str(tmp_path))

    settings = Settings(data_dir=tmp_path)
    txt_path = FIXTURES / "sample.txt"
    md_path = FIXTURES / "sample.md"

    r1 = ingest(txt_path, settings)
    r2 = ingest(md_path, settings)
    assert r1.status == "ok", r1.error
    assert r2.status == "ok", r2.error

    results = search_documents(
        "sample content", top_k=20, filters={"filename": "sample.txt"}
    )

    assert len(results) > 0, "Expected at least one chunk from sample.txt"
    filenames = {r.filename for r in results}
    assert filenames == {"sample.txt"}, f"Expected only sample.txt, got {filenames}"


def test_search_by_metadata_source_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """search_by_metadata with source_id filter returns exactly that source."""
    monkeypatch.setenv("AGENTRAG_DATA_DIR", str(tmp_path))

    settings = Settings(data_dir=tmp_path)
    txt_path = FIXTURES / "sample.txt"
    md_path = FIXTURES / "sample.md"

    r1 = ingest(txt_path, settings)
    ingest(md_path, settings)
    assert r1.status == "ok", r1.error

    target_source_id = _make_source_id(txt_path)
    sources = search_by_metadata({"source_id": target_source_id})

    assert len(sources) == 1, f"Expected 1 source, got {len(sources)}"
    assert sources[0].source_id == target_source_id
    assert sources[0].filename == "sample.txt"


def test_search_by_metadata_unknown_key_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """search_by_metadata with unknown key returns empty list, no exception."""
    monkeypatch.setenv("AGENTRAG_DATA_DIR", str(tmp_path))

    settings = Settings(data_dir=tmp_path)
    ingest(FIXTURES / "sample.txt", settings)

    sources = search_by_metadata({"unknown_key": "no_match"})

    assert sources == [], f"Expected empty list, got {sources}"


def test_search_by_metadata_custom_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """search_by_metadata with custom tag key filters by s.metadata.get(k)."""
    monkeypatch.setenv("AGENTRAG_DATA_DIR", str(tmp_path))

    settings = Settings(data_dir=tmp_path)

    science_doc = RawDocument(
        source_id="science_src_001",
        filename="science.txt",
        text="Photosynthesis converts light energy into chemical energy in glucose.",
        metadata={"tag": "science", "filename": "science.txt"},
    )
    other_doc = RawDocument(
        source_id="other_src_002",
        filename="other.txt",
        text="The quick brown fox jumps over the lazy dog every single day.",
        metadata={"tag": "other", "filename": "other.txt"},
    )

    r1 = ingest_raw(science_doc, settings)
    r2 = ingest_raw(other_doc, settings)
    assert r1.status == "ok", r1.error
    assert r2.status == "ok", r2.error

    sources = search_by_metadata({"tag": "science"})

    assert (
        len(sources) == 1
    ), f"Expected 1 source with tag=science, got {len(sources)}: {sources}"
    assert sources[0].source_id == "science_src_001"
    assert sources[0].metadata.get("tag") == "science"
