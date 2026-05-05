#!/usr/bin/env python3
"""Phase 6 smoke tests — validates multi-collection and streaming retrieval."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def run_smoke_tests() -> None:
    """Run all Phase 6 smoke tests via direct Python API calls."""
    fixtures = Path(__file__).parent.parent / "tests" / "fixtures"
    sample_txt = fixtures / "sample.txt"

    tmp = tempfile.mkdtemp()
    try:
        tmp_path = Path(tmp)

        from agentrag.config import Settings
        from agentrag.server import tools

        settings = Settings(data_dir=tmp_path)
        tools.set_active_settings(settings)

        # S1 — Collection isolation roundtrip
        tools.create_collection("smoke_ws_a")
        tools.switch_collection("smoke_ws_a")
        ingest_result = tools.ingest_file(str(sample_txt))
        assert ingest_result.status == "ok", f"S1: ingest failed: {ingest_result.error}"

        tools.create_collection("smoke_ws_b")
        tools.switch_collection("smoke_ws_b")
        results_b = tools.search_documents("test query", top_k=5)
        assert (
            results_b == []
        ), f"S1: expected empty in smoke_ws_b, got {len(results_b)}"

        tools.switch_collection("smoke_ws_a")
        results_a = tools.search_documents("test query", top_k=5)
        assert len(results_a) > 0, "S1: expected results in smoke_ws_a"
        print("[S1] Collection isolation: PASS")

        # S2 — Create, list, and switch tool calls
        create_msg = tools.create_collection("smoke_verify")
        assert "smoke_verify" in create_msg, f"S2: create response: {create_msg!r}"

        collections = tools.list_collections()
        assert "smoke_verify" in collections, f"S2: list_collections: {collections}"

        switch_msg = tools.switch_collection("smoke_verify")
        assert "smoke_verify" in switch_msg, f"S2: switch response: {switch_msg!r}"

        try:
            tools.switch_collection("collection_that_does_not_exist_xyz")
            print("S2: FAIL — expected ValueError not raised", file=sys.stderr)
            sys.exit(1)
        except ValueError:
            pass
        print("[S2] Create/list/switch: PASS")

        # S3 — Streaming parity with batch
        settings.collection = "documents"
        from agentrag.store.qdrant import QdrantStore

        QdrantStore(settings)  # ensure documents collection exists
        tools.ingest_file(str(sample_txt))

        batch_results = tools.search_documents("documents text", top_k=5)
        stream_results = tools.search_stream("documents text", top_k=5)
        batch_ids = [r.chunk_id for r in batch_results]
        stream_ids = [r.chunk_id for r in stream_results]
        assert batch_ids == stream_ids, f"S3: batch {batch_ids} != stream {stream_ids}"
        print("[S3] Streaming parity: PASS")

        # S4 — Default collection regression
        sources = tools.list_sources()
        sample_source = next((s for s in sources if "sample" in s.filename), None)
        assert sample_source is not None, "S4: sample.txt not found in list_sources"

        del_result = tools.delete_source(sample_source.source_id)
        assert del_result.status == "ok", f"S4: delete failed: {del_result}"

        sources_after = tools.list_sources()
        still_there = any(s.source_id == sample_source.source_id for s in sources_after)
        assert not still_there, "S4: source still present after delete"
        print("[S4] Default collection regression: PASS")
    finally:
        # Close Qdrant clients before deleting the temp directory.
        # Required on Windows where SQLite files remain locked until the client closes.
        from agentrag.store.qdrant import _close_all_clients

        _close_all_clients()
        import shutil

        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    try:
        run_smoke_tests()
        print("=== All Phase 6 smoke tests PASSED ===")
    except AssertionError as exc:
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
