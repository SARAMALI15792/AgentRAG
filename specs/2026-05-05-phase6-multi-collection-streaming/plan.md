# Phase 6 — Multi-Collection & Streaming Retrieval: Implementation Plan

Execution order is strict. Each task group must be fully green before the next begins.
TDD applies to all testable deliverables. Verify script is written first (Task Group 1).

---

## Task Group 1 — Exit Gate Script (write first)

1.1. Create `scripts/verify_phase6.sh` with the standard 5-step structure (Article XI.2).
     Phase-specific checks:
     - Ingest a file into collection `workspace_a`, search in collection `workspace_b` → 0 results.
     - Switch to `workspace_a` → results found.
     - Call `list_collections` → `workspace_a` present.
     - Call `search_stream` with any query → returns results without raising.
     - Verify default `documents` collection still returns results (regression check).
1.2. Confirm the script fails on the current state (new tools not yet registered — expected).

---

## Task Group 2 — Multi-Collection Support

### 2A — Store layer

2.1. `tests/unit/test_store.py` — add failing tests:
     - Two distinct collections, same `source_id`, isolated data (search in B returns empty when doc in A).
     - `create_collection(name)` creates a new Qdrant collection if it doesn't exist.
     - `list_collections()` returns all collection names including the default.
     - `create_collection` with an already-existing name is idempotent (no exception).
2.2. `src/agentrag/store/qdrant.py` — implement:
     - Replace hardcoded `_COLLECTION` constant with `settings.collection` everywhere.
     - Add `create_collection(name: str) -> None` — creates Qdrant collection with correct vector params.
     - Add `list_collections() -> list[str]` — delegates to `qdrant_client` collections list.
     - Existing `upsert`, `query`, `delete` all use `settings.collection` dynamically.
2.3. Run `uv run pytest tests/unit/test_store.py` — confirm green.

### 2B — Session-scoped collection state

2.4. `src/agentrag/config.py` — confirm `collection: str` field already present (from `AGENTRAG_COLLECTION`).
     No new env vars needed. Collection switching is in-memory and session-scoped only.
2.5. `src/agentrag/server/app.py` — expose the live `Settings` instance to tool handlers via
     the existing lifespan context (so `switch_collection` can mutate `settings.collection`
     in-process without touching disk).

### 2C — New MCP tool handlers

2.6. `tests/unit/test_tools.py` — add failing tests for all three new tools:
     - `list_collections` → returns list containing the default collection name.
     - `create_collection("new_ws")` → returns confirmation string; subsequent `list_collections` includes it.
     - `switch_collection("new_ws")` → returns confirmation; subsequent searches use that collection.
     - `switch_collection("nonexistent")` → raises `ValueError`.
     - All three handlers ≤15 lines of business logic (Article IV.1).
2.7. `src/agentrag/server/tools.py` — implement three thin handlers:
     - `list_collections() -> list[str]` — delegates to `store.list_collections()`.
     - `create_collection(name: str) -> str` — delegates to `store.create_collection(name)`.
     - `switch_collection(name: str) -> str` — validates collection exists, updates `settings.collection`.
2.8. `src/agentrag/server/app.py` — register all three tools via `@mcp.tool()` decorator.
2.9. Run `uv run pytest tests/unit/test_tools.py` — confirm green.

### 2D — Integration test (multi-collection)

2.10. `tests/integration/test_multi_collection.py` — real Qdrant, real files:
      - Ingest `sample.txt` into collection `ws_alpha`.
      - Search in `ws_beta` (created but empty) → 0 results.
      - `switch_collection("ws_alpha")` → search returns results.
      - `list_collections()` → both `ws_alpha` and `ws_beta` present.
      - Default `documents` collection unaffected (ingest there, search there, results found).
2.11. Run `uv run pytest tests/integration/test_multi_collection.py` — confirm green.

---

## Task Group 3 — Streaming Retrieval

### 3A — Async generator

3.1. `tests/unit/test_streaming.py` — add failing async tests:
     - `stream_search(query, top_k)` yields `SearchResult` objects in score-descending order.
     - Results from `stream_search` match results from `searcher.search` for the same query.
     - Empty corpus yields zero results without raising.
3.2. `src/agentrag/retrieval/streaming.py` — implement:
     - `async def stream_search(query: str, top_k: int, store: QdrantStore, embedder: Embedder, reranker: Reranker) -> AsyncGenerator[SearchResult, None]`
     - Delegates to `searcher.search` internally; yields each `SearchResult` in order.
     - No new external dependencies — uses stdlib `asyncio` only.
3.3. Run `uv run pytest tests/unit/test_streaming.py` — confirm green.

### 3B — search_stream MCP tool

3.4. `tests/unit/test_tools.py` — add failing test for `search_stream`:
     - Returns same results as `search_documents` for the same query (batch fallback parity).
     - Empty query string → raises `ValueError`.
3.5. `src/agentrag/server/tools.py` — implement `search_stream` handler:
     - Calls `streaming.stream_search`, collects results into a list (batch fallback path).
     - If MCP SDK supports `AsyncGenerator` return type, return the generator directly.
     - Falls back to batch silently — no error, no warning to user.
3.6. Register `search_stream` in `src/agentrag/server/app.py`.

### 3C — Integration test (streaming)

3.7. `tests/integration/test_streaming_integration.py` — real Qdrant:
     - Ingest `sample.txt`, call `search_stream("query", top_k=5)` → results returned.
     - Result set matches `search_documents("query", top_k=5)` — same chunk IDs, same order.
3.8. Run full integration suite — confirm green.

---

## Task Group 4 — Exit Gate

4.1. Run `uv run black . && uv run ruff check . && uv run mypy --strict src/` — zero issues.
4.2. Run `uv run pytest --tb=short -q` — zero failures.
4.3. Run `scripts/verify_phase6.sh` locally — confirm exit 0.
4.4. Push branch, verify CI is green on `phase/6-multi-collection-streaming`.
4.5. Open PR → `main`.
