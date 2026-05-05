# Phase 4 — Search Quality: Validation Criteria

Phase 4 is complete when **all** criteria below are satisfied and
`scripts/verify_phase4.sh` exits 0.

---

## Gate 1 — Formatting, Linting, Type Checking

| Check | Command | Pass condition |
|---|---|---|
| Black | `uv run black --check .` | Zero reformatting needed |
| Ruff | `uv run ruff check .` | Zero violations |
| mypy | `uv run mypy --strict src/` | Zero errors or warnings |

---

## Gate 2 — Full Test Suite

```
uv run pytest --tb=short -q
```

- Zero failures, zero errors.
- Skips permitted only with documented, approved reason (Article III.4).
- No new `# type: ignore` without inline justification.

---

## Gate 3 — Metadata Filter Integration Tests

`tests/integration/test_search_filters.py` passes all assertions:

- [ ] `search_documents(query, filters={"filename": X})` returns only chunks
      whose `filename` matches X — no results from other sources.
- [ ] `search_by_metadata({"source_id": X})` returns the correct `SourceInfo`
      for that source.
- [ ] `search_by_metadata({"unknown_key": "value"})` returns an empty list
      without raising.
- [ ] At least 3 distinct filter fields exercised in the test file.

---

## Gate 4 — Cross-Encoder Re-Ranker Unit Tests

`tests/unit/test_reranker.py` passes all assertions:

- [ ] With `AGENTRAG_RERANK=false`: `CrossEncoder` constructor is never called.
      Results returned unchanged (identity pass-through).
- [ ] With `AGENTRAG_RERANK=true`: results are sorted by cross-encoder score
      descending. A list in wrong order is corrected after reranking.
- [ ] Re-ranking an empty list returns an empty list without error.
- [ ] Re-ranking a single-item list returns that item unchanged.
- [ ] `CrossEncoder` is mocked in all unit tests — no model download, no network.

---

## Gate 5 — Re-Ranker Phase-Specific Smoke (Exit Gate Script)

```bash
AGENTRAG_RERANK=true uv run pytest tests/unit/test_reranker.py -q
```

- Exits 0. Confirms the `AGENTRAG_RERANK=true` code path is exercised with
  mocked CrossEncoder (no model download in CI).

---

## Gate 6 — SentenceTransformer Caching

`tests/unit/test_embedder.py` caching assertion passes:

- [ ] Two successive calls to `embed()` within the same process use the same
      `SentenceTransformer` instance (constructor called exactly once).
- [ ] The cached instance is keyed on model name: different `embed_model` values
      produce different instances.

---

## Gate 7 — Concurrent Upsert Safety

`tests/integration/test_concurrent_upsert.py` passes:

- [ ] Three threads re-ingest `sample.txt` concurrently.
- [ ] After all threads complete: `list_sources()` returns exactly 1 entry for
      `sample.txt`'s `source_id`.
- [ ] `chunk_count` on that entry is the same integer on every run of the test.
- [ ] Test does not deadlock or hang (completes within 30 seconds).

---

## Gate 8 — Benchmark Script

```
uv run python scripts/benchmark_retrieval.py
```

- [ ] Exits 0 on a clean install (no external corpus required).
- [ ] Stdout shows query text, top-k results with scores, and wall-clock time
      per query for ≥10 queries.
- [ ] No unhandled exceptions.

---

## Gate 9 — Verify Script

```bash
bash scripts/verify_phase4.sh
```

Final output line must be:

```
=== Phase 4 Exit Gate: PASSED ===
```

If any earlier step fails, the script exits non-zero before reaching this line
and the phase is not complete.

---

## What Is NOT Required for Phase 4 Exit

- A real CrossEncoder model download (all reranker tests use mocks).
- PyPI publication or packaging changes (Phase 5).
- Multi-collection or streaming retrieval (Phase 6).
- Benchmark scores meeting any specific threshold (benchmark is informational only).
- Changes to any MCP tool handler in `server/tools.py`.
