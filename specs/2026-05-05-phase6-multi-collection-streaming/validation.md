# Phase 6 — Multi-Collection & Streaming Retrieval: Validation Criteria

Phase 6 is complete when **all** criteria below are satisfied.
The authoritative check is `scripts/verify_phase6.sh` exiting 0.

---

## Automated Gate — verify_phase6.sh

```
scripts/verify_phase6.sh exits 0
```

The script runs in order and fails fast on the first failing check:

| Step | Check |
|------|-------|
| 1 | `uv run black --check .` — zero formatting issues |
| 2 | `uv run ruff check .` — zero lint errors |
| 3 | `uv run mypy --strict src/` — zero type errors |
| 4 | `uv run pytest --tb=short -q` — zero failures, zero errors |
| 5 | Phase-specific smoke tests (see below) |

### Phase-Specific Smoke Tests (Step 5)

All smoke tests run via a small Python harness that starts the MCP server
in HTTP transport mode (`agentrag serve --transport http`) and calls tools
over the API. The harness exits non-zero if any assertion fails.

**S1 — Collection isolation roundtrip**
1. Ingest `tests/fixtures/sample.txt` into collection `smoke_ws_a`.
2. Create collection `smoke_ws_b` (empty).
3. Switch to `smoke_ws_b`, call `search_documents("test query", top_k=5)`.
4. Assert: result list is empty.
5. Switch to `smoke_ws_a`, call `search_documents("test query", top_k=5)`.
6. Assert: result list is non-empty.

**S2 — Create, list, and switch tool calls**
1. Call `create_collection("smoke_verify")`.
2. Assert: response contains `"smoke_verify"`.
3. Call `list_collections()`.
4. Assert: `"smoke_verify"` present in returned list.
5. Call `switch_collection("smoke_verify")`.
6. Assert: response contains `"smoke_verify"`.
7. Call `switch_collection("collection_that_does_not_exist")`.
8. Assert: `ValueError` raised (or error response returned).

**S3 — Streaming parity with batch**
1. Ingest `tests/fixtures/sample.txt` into `documents` collection.
2. Call `search_documents("query", top_k=5)` → capture result chunk IDs.
3. Call `search_stream("query", top_k=5)` → capture result chunk IDs.
4. Assert: both lists contain the same chunk IDs in the same order.

**S4 — Default collection regression**
1. Ingest `tests/fixtures/sample.txt` into the default `documents` collection.
2. Call `search_documents("test", top_k=3)` → assert non-empty results.
3. Call `list_sources()` → assert `sample.txt` source present.
4. Call `delete_source(source_id)` → assert `status="ok"`.
5. Call `list_sources()` → assert source no longer present.
6. Assert all Phase 1–5 tool signatures are unchanged (no regressions).

---

## Functional Checks

These must pass before the PR is opened. Confirmed locally and documented
in the PR description.

### F1 — mypy --strict passes on all new files

```
uv run mypy --strict src/agentrag/retrieval/streaming.py
uv run mypy --strict src/agentrag/store/qdrant.py
uv run mypy --strict src/agentrag/server/tools.py
```

Zero errors. Every new function fully annotated including `-> None` returns.

### F2 — tools.py handlers stay within 15-line limit

All four new handlers (`list_collections`, `create_collection`,
`switch_collection`, `search_stream`) contain ≤15 lines of business logic
each (Article IV.1). Verified by manual review before commit.

### F3 — No cross-layer imports introduced

No new import in `store/qdrant.py` from `ingestion/` or `retrieval/`.
No new import in `retrieval/streaming.py` from `server/` or `ingestion/`
(except `ingestion/embedder.py` for query embedding — already permitted).
Verify with: `uv run python -c "import agentrag.store.qdrant"` (no import errors).

### F4 — Streaming fallback is silent

When MCP SDK does not support `AsyncGenerator` return types:
- `search_stream` returns a `list[SearchResult]` without logging a warning.
- No exception is raised.
- Confirmed by unit test in `test_tools.py`.

---

## Test Coverage Requirements

| Module | Minimum new tests |
|--------|------------------|
| `test_store.py` | 4 new unit tests (two-collection isolation, `create_collection` idempotent, `list_collections` return type, `create_collection` unknown params) |
| `test_tools.py` | 6 new unit tests (one per tool call path + error path per tool where applicable) |
| `test_streaming.py` | 3 new unit tests (yield order, parity with batch, empty corpus) |
| `test_multi_collection.py` | Integration: 5 assertions covering isolation, switching, listing |
| `test_streaming_integration.py` | Integration: 2 assertions (results returned, parity with batch) |

---

## Merge Condition

PR to `main` may be merged when:

1. `scripts/verify_phase6.sh` exits 0 locally.
2. CI is green on `phase/6-multi-collection-streaming` (both Python 3.12 and 3.13).
3. F1–F4 functional checks confirmed and documented in the PR description.
4. CodeRabbit review completed; all blocking issues resolved (Article III.7).
5. No regressions in existing Phase 1–5 tool contracts (S4 smoke test passing).
