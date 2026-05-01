"""Integration tests for the agentic retrieval loop (Phase 3B)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from agentrag.config import Settings
from agentrag.ingestion.pipeline import ingest
from agentrag.retrieval.evaluator import evaluate
from agentrag.retrieval.query_planner import plan
from agentrag.server.tools import evaluate_chunks, plan_query, search_multi

FIXTURES = Path("tests/fixtures")


@pytest.fixture
def settings_no_key(tmp_path: Path) -> Settings:
    """Settings with Qdrant in tmp dir and no Gemini key."""
    return Settings(data_dir=tmp_path / "qdrant", google_api_key="")


@pytest.fixture
def populated_settings(tmp_path: Path) -> Settings:
    """Settings with sample.txt ingested into a real Qdrant instance."""
    s = Settings(data_dir=tmp_path / "qdrant", google_api_key="")
    ingest(FIXTURES / "sample.txt", s)
    return s


# ---------------------------------------------------------------------------
# plan_query — graceful degrade path (no API key)
# ---------------------------------------------------------------------------


def test_plan_query_without_api_key_returns_query_plan(
    populated_settings: Settings,
) -> None:
    """plan_query completes without raising even with no API key."""
    os.environ["AGENTRAG_DATA_DIR"] = str(populated_settings.data_dir)
    try:
        result = plan_query("what is AgentRAG?")
    finally:
        del os.environ["AGENTRAG_DATA_DIR"]

    assert result.original_query == "what is AgentRAG?"
    assert isinstance(result.sub_queries, list)
    assert len(result.sub_queries) >= 1
    for sq in result.sub_queries:
        assert isinstance(sq, str)


# ---------------------------------------------------------------------------
# search_multi — real Qdrant, no Gemini needed
# ---------------------------------------------------------------------------


def test_search_multi_returns_results_for_two_queries(
    populated_settings: Settings,
) -> None:
    """search_multi with 2 queries returns results with no duplicate chunk_ids."""
    os.environ["AGENTRAG_DATA_DIR"] = str(populated_settings.data_dir)
    try:
        results = search_multi(["local semantic memory", "vector embeddings"], top_k=3)
    finally:
        del os.environ["AGENTRAG_DATA_DIR"]

    chunk_ids = [r.chunk_id for r in results]
    assert len(chunk_ids) == len(set(chunk_ids)), "Duplicate chunk_ids found"
    assert len(results) <= 3  # bounded by top_k


def test_search_multi_deduplication_correct(populated_settings: Settings) -> None:
    """Passing the same query twice still returns deduplicated results."""
    os.environ["AGENTRAG_DATA_DIR"] = str(populated_settings.data_dir)
    try:
        results = search_multi(["AgentRAG", "AgentRAG"], top_k=5)
    finally:
        del os.environ["AGENTRAG_DATA_DIR"]

    chunk_ids = [r.chunk_id for r in results]
    assert len(chunk_ids) == len(set(chunk_ids))


def test_search_multi_empty_queries_raises(populated_settings: Settings) -> None:
    """search_multi with empty list raises ValueError without crashing Qdrant."""
    os.environ["AGENTRAG_DATA_DIR"] = str(populated_settings.data_dir)
    try:
        with pytest.raises(ValueError):
            search_multi([], top_k=5)
    finally:
        del os.environ["AGENTRAG_DATA_DIR"]


# ---------------------------------------------------------------------------
# evaluate_chunks — graceful degrade path (no API key)
# ---------------------------------------------------------------------------


def test_evaluate_chunks_without_api_key_returns_report(
    populated_settings: Settings,
) -> None:
    """evaluate_chunks completes without raising even with no API key."""
    os.environ["AGENTRAG_DATA_DIR"] = str(populated_settings.data_dir)
    try:
        results = search_multi(["AgentRAG semantic search"], top_k=3)
        report = evaluate_chunks("AgentRAG semantic search", results)
    finally:
        del os.environ["AGENTRAG_DATA_DIR"]

    assert report.query == "AgentRAG semantic search"
    assert len(report.scored_chunks) == len(results)
    assert isinstance(report.sufficient, bool)
    for cs in report.scored_chunks:
        assert 0.0 <= cs.score <= 1.0


# ---------------------------------------------------------------------------
# Full agentic loop: plan → search_multi → evaluate → re-search if needed
# ---------------------------------------------------------------------------


def test_full_agentic_loop_completes_without_error(
    populated_settings: Settings,
) -> None:
    """Full plan→search→evaluate→re-search loop completes without raising."""
    os.environ["AGENTRAG_DATA_DIR"] = str(populated_settings.data_dir)
    try:
        # Step 1: plan
        qplan = plan_query("how does AgentRAG store documents?")
        assert len(qplan.sub_queries) >= 1

        # Step 2: search_multi
        results = search_multi(qplan.sub_queries, top_k=3)

        # Step 3: evaluate
        report = evaluate_chunks(qplan.original_query, results)
        assert isinstance(report.sufficient, bool)

        # Step 4: re-search if not sufficient
        if not report.sufficient and report.suggested_queries:
            follow_up = search_multi(report.suggested_queries, top_k=3)
            assert isinstance(follow_up, list)

    finally:
        del os.environ["AGENTRAG_DATA_DIR"]


# ---------------------------------------------------------------------------
# Direct module tests (bypass tools layer) — graceful degrade verification
# ---------------------------------------------------------------------------


def test_query_planner_degrade_no_key(settings_no_key: Settings) -> None:
    """query_planner.plan returns single-query plan without raising."""
    result = plan("complex multi-part query", settings_no_key)
    assert result.sub_queries == ["complex multi-part query"]


def test_evaluator_degrade_no_key(settings_no_key: Settings) -> None:
    """evaluator.evaluate returns pass-through report without raising."""
    from agentrag.types import SearchResult

    results = [
        SearchResult(
            chunk_id="c0",
            source_id="s0",
            filename="f.txt",
            text="some text",
            score=0.7,
            metadata={},
        )
    ]
    report = evaluate("query", results, settings_no_key)
    assert report.sufficient is True
    assert all(cs.score == 0.5 for cs in report.scored_chunks)
