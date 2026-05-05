"""Integration tests for Phase 6 multi-collection support."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from agentrag.config import Settings
from agentrag.server import tools


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path: Path) -> Generator[Settings, None, None]:
    """Provide a fresh settings instance and reset module state after each test."""
    settings = Settings(data_dir=tmp_path)
    tools.set_active_settings(settings)
    yield settings
    tools.set_active_settings(None)


_SAMPLE_TXT = Path(__file__).parent.parent / "fixtures" / "sample.txt"


def test_search_in_empty_collection_returns_nothing(
    isolated_settings: Settings,
) -> None:
    """Searching in an empty collection returns zero results."""
    tools.create_collection("empty_ws")
    tools.switch_collection("empty_ws")
    results = tools.search_documents("text query", top_k=5)
    assert results == []


def test_data_in_collection_a_not_visible_from_collection_b(
    isolated_settings: Settings,
) -> None:
    """Data ingested into ws_alpha is not returned when searching ws_beta."""
    tools.create_collection("ws_alpha")
    tools.switch_collection("ws_alpha")
    result = tools.ingest_file(str(_SAMPLE_TXT))
    assert result.status == "ok"

    tools.create_collection("ws_beta")
    tools.switch_collection("ws_beta")
    results_b = tools.search_documents("text", top_k=5)
    assert results_b == []

    tools.switch_collection("ws_alpha")
    results_a = tools.search_documents("text", top_k=5)
    assert len(results_a) > 0


def test_list_collections_shows_all_created(isolated_settings: Settings) -> None:
    """list_collections returns both ws_alpha and ws_beta after creation."""
    tools.create_collection("ws_alpha")
    tools.create_collection("ws_beta")
    collections = tools.list_collections()
    assert "ws_alpha" in collections
    assert "ws_beta" in collections


def test_list_sources_scoped_to_active_collection(
    isolated_settings: Settings,
) -> None:
    """list_sources returns only sources in the active collection."""
    tools.create_collection("ws_alpha")
    tools.switch_collection("ws_alpha")
    tools.ingest_file(str(_SAMPLE_TXT))
    sources_alpha = tools.list_sources()
    assert len(sources_alpha) >= 1

    tools.create_collection("ws_beta")
    tools.switch_collection("ws_beta")
    sources_beta = tools.list_sources()
    assert len(sources_beta) == 0


def test_default_documents_collection_unaffected(
    isolated_settings: Settings,
) -> None:
    """Default 'documents' collection remains accessible after workspace switching."""
    tools.ingest_file(str(_SAMPLE_TXT))  # ingests into "documents" (default)
    results_before = tools.search_documents("text", top_k=5)
    assert len(results_before) > 0

    tools.create_collection("side_ws")
    tools.switch_collection("side_ws")
    results_other = tools.search_documents("text", top_k=5)
    assert results_other == []

    tools.switch_collection("documents")
    results_after = tools.search_documents("text", top_k=5)
    assert len(results_after) > 0
