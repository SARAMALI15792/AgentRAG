# Phase 4 — Search Quality: Implementation Plan

Strict TDD order. Every test file written and confirmed failing before its
implementation file is created. No step is complete until `pytest` is green
for that step.

---

## Group 0 — Context7 Lookups _(before any code)_

**0.1** `resolve-library-id` → `sentence-transformers`
**0.2** `query-docs` on `CrossEncoder`, `predict`, score normalization API
**0.3** Confirm `CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")` constructor and
        `predict(pairs: list[tuple[str, str]]) -> list[float]` signature matches
        current `sentence-transformers` 3.x docs before writing any reranker code.

---

## Group 1 — Metadata Filter Hardening

**1.1** Write `tests/integration/test_search_filters.py` — confirm red:
  - `search_documents` with `filters={"filename": X}` returns only chunks from X
  - `search_by_metadata` with `{"source_id": X}` returns correct `SourceInfo`
  - `search_by_metadata` with unknown key returns empty list, does not raise
  - At least 3 distinct filter fields tested: `filename`, `source_id`, one arbitrary
    metadata key

**1.2** Run `uv run pytest tests/integration/test_search_filters.py` → confirm red.

**1.3** Fix gaps in `searcher.py` and `store/qdrant.py` filter logic until tests green.

**1.4** Run `uv run pytest tests/integration/test_search_filters.py` → confirm green.

---

## Group 2 — Cross-Encoder Re-Ranker

**2.1** Write `tests/unit/test_reranker.py` (replace empty file) — confirm red:
  - `AGENTRAG_RERANK=false` → identity pass-through, `CrossEncoder` never imported/instantiated
  - `AGENTRAG_RERANK=true` → results re-ordered by cross-encoder score descending
  - `CrossEncoder` mocked — no model download in unit tests
  - Re-ranking an already-sorted list returns the same order
  - Re-ranking an empty list returns an empty list

**2.2** Run `uv run pytest tests/unit/test_reranker.py` → confirm red.

**2.3** Implement `src/agentrag/retrieval/reranker.py`:
  - Replace identity stub with real `CrossEncoder` implementation
  - Lazy instantiation: `CrossEncoder` loaded on first `rerank()` call, not at import time
  - `AGENTRAG_RERANK=false` → zero overhead identity pass-through (no model loaded)
  - `AGENTRAG_RERANK=true` → load `"cross-encoder/ms-marco-MiniLM-L-6-v2"`, score pairs,
    return results sorted by cross-encoder score descending

**2.4** Wire reranker into `retrieval/searcher.py`:
  - After `store.query()`, pass results through `reranker.rerank(query, results)`
  - No logic beyond the delegation (Article IV.1)

**2.5** Run `uv run pytest tests/unit/test_reranker.py` → confirm green.

---

## Group 3 — SentenceTransformer Model Caching

_(Pulled forward from Phase 5 — Article XII.5 known issue. Fixing here because
`searcher.py` is already open for reranker wiring.)_

**3.1** Write `tests/unit/test_embedder.py` — extend with caching assertion:
  - Two successive calls to `embed()` use the same `SentenceTransformer` instance
    (mock constructor to count calls — must be called exactly once)

**3.2** Run relevant test → confirm red (constructor currently called per `embed()` call).

**3.3** Fix `src/agentrag/ingestion/embedder.py`:
  - Cache `SentenceTransformer` instance at module level or on first call
  - Constructor called at most once per process lifetime
  - No public API change — `embed(chunks)` signature unchanged

**3.4** Run `uv run pytest tests/unit/test_embedder.py` → confirm green.

---

## Group 4 — Concurrent Upsert Safety

**4.1** Write `tests/integration/test_concurrent_upsert.py` — confirm red:
  - Re-ingest `sample.txt` 3× concurrently via `threading.Thread`
  - After all threads complete: `list_sources()` returns exactly 1 entry for that source
  - `chunk_count` is stable across runs (same integer every time)

**4.2** Run → confirm red (or confirm the current implementation already passes —
        if green, document that upsert was already safe and skip to 4.3).

**4.3** Fix `store/qdrant.py` upsert logic if the test revealed a race condition.

**4.4** Run → confirm green.

---

## Group 5 — Benchmark Script

**5.1** Write `scripts/benchmark_retrieval.py`:
  - Ingest a sample corpus (uses existing `tests/fixtures/sample.txt` or similar)
  - Run 10 representative queries against the ingested corpus
  - Log top-k results and scores for each query to stdout
  - Log total wall-clock time per query
  - Exits 0 regardless of scores (not a gate — Article XII.4)

**5.2** Run `uv run python scripts/benchmark_retrieval.py` → confirm exits 0 and
        produces readable output.

---

## Group 6 — Exit Gate

**6.1** Write `scripts/verify_phase4.sh` following the standard template
        (Article XI.2), with phase-specific step:
  - Black check
  - Ruff check
  - mypy --strict
  - pytest full suite
  - Phase-specific: `AGENTRAG_RERANK=true uv run pytest tests/unit/test_reranker.py -q`
    (reranker mocked — no model download; confirms the env-var flag path is exercised)

**6.2** Run `bash scripts/verify_phase4.sh` → confirm exits 0.
