# Phase 4 — Search Quality: Requirements

---

## Scope

Phase 4 improves retrieval precision through three independent improvements:
metadata filter hardening, cross-encoder re-ranking, and concurrent upsert
safety. It also fixes the SentenceTransformer re-creation bug pulled forward
from Phase 5 (Article XII.5).

**No new external services.** All improvements use the existing stack.
**No new runtime dependencies.** `CrossEncoder` is already available in the
`sentence-transformers` package (already a runtime dep).

---

## In-Scope Deliverables

| Deliverable | Files affected |
|---|---|
| Metadata filter hardening | `retrieval/searcher.py`, `store/qdrant.py` |
| Cross-encoder re-ranker | `retrieval/reranker.py`, `retrieval/searcher.py` |
| SentenceTransformer caching | `ingestion/embedder.py` |
| Concurrent upsert safety | `store/qdrant.py` |
| Benchmark script | `scripts/benchmark_retrieval.py` |
| Exit gate | `scripts/verify_phase4.sh` |
| Tests (new) | `tests/unit/test_reranker.py`, `tests/integration/test_search_filters.py`, `tests/integration/test_concurrent_upsert.py` |
| Tests (extended) | `tests/unit/test_embedder.py` |

---

## Out of Scope

- Any new MCP tools (Phase 4 improves existing tools, does not add new ones)
- Streaming retrieval (Phase 6)
- Multi-collection support (Phase 6)
- Distribution / PyPI packaging (Phase 5)
- Any Gemini API integration beyond what Phase 3B shipped

---

## Cross-Encoder Re-Ranker

### Model

`cross-encoder/ms-marco-MiniLM-L-6-v2` — downloaded from HuggingFace on first
use. Model size: ~90MB. Not downloaded in CI (unit tests mock `CrossEncoder`).

### Activation

Controlled by `AGENTRAG_RERANK` env var (already in `config.py`):
- `false` (default): identity pass-through. Zero overhead. `CrossEncoder` never
  instantiated.
- `true`: cross-encoder scores all (query, chunk-text) pairs, results returned
  sorted by cross-encoder score descending.

### Instantiation — Lazy on First Call

`CrossEncoder` is instantiated the first time `rerank()` is called with
`settings.rerank=True`. It is cached at module level and reused for all
subsequent calls in the same process. This matches the current pattern for
`SentenceTransformer` (after the caching fix in this phase).

**Rationale:** Keeps cold-start fast when `AGENTRAG_RERANK=false`. Avoids
loading a 90MB model for users who never enable reranking.

### Wire-in Point

`retrieval/searcher.py` passes results through `reranker.rerank(query, results)`
after `store.query()`. The reranker call is unconditional — when `AGENTRAG_RERANK=false`
the identity reranker returns the list unchanged in O(1).

---

## SentenceTransformer Model Caching

### Current Bug (Article XII.5)

`SentenceTransformer("all-MiniLM-L6-v2")` is re-instantiated on every call to
`embed()`. Model loading takes 2–5 seconds and allocates ~100MB. For a corpus
of 100 files this wastes ~200–500 seconds and gigabytes of redundant allocation.

### Fix

Cache the `SentenceTransformer` instance. The instance is created once (lazily
on first `embed()` call) and reused for the process lifetime. The `embed()`
function signature is unchanged — no public API break.

### Implementation constraint

The model name comes from `settings.embed_model`. The cache must respect this
value: if two calls use different model names (not a normal use case, but
possible in tests), they must not share the same cached instance.

---

## Metadata Filter Hardening

### Filter fields that must work

The integration test must pass for at minimum:
1. `filename` — filter by ingested filename
2. `source_id` — filter by stable source hash
3. One arbitrary metadata key — any key passed to `ingest_file`'s `metadata`
   argument (e.g., `{"tag": "test"}`)

### Unknown key behaviour

`search_by_metadata` with a key that matches no stored document must return
an empty list without raising. This is already the contract (architecture spec),
but the integration test will verify it explicitly.

---

## Concurrent Upsert Safety

### Scenario

Multiple threads calling `pipeline.ingest()` on the same file simultaneously.
This can happen when `ingest_directory` is parallelised in a future phase, or
when Claude calls `ingest_file` concurrently.

### Required behaviour

After N concurrent upserts of the same source file:
- `list_sources()` returns exactly 1 entry for that source (no duplicates)
- `chunk_count` is deterministic (same value regardless of how many concurrent
  upserts ran)

### Approach

If the current `qdrant_client` embedded mode handles this via its own internal
locking, the integration test may pass without any fix — document it. If not,
add a `threading.Lock` in `store/qdrant.py` guarding the upsert path.

---

## Benchmark Script

- Not a CI gate. Exits 0 regardless of measured scores (Article XII.4).
- Logs query, top-k results, scores, and wall-clock time per query to stdout.
- Uses existing fixture files — no external corpus required.
- Must run to completion without error on a fresh install
  (`uv run python scripts/benchmark_retrieval.py`).

---

## Environment Variables — No Changes

No new env vars are added in Phase 4. `AGENTRAG_RERANK` (already shipped) is
the only variable this phase activates.

---

## Dependency Changes — None

`sentence-transformers` (already a runtime dep) provides `CrossEncoder`.
No `pyproject.toml` changes required.

---

## Architectural Constraints

- `store/qdrant.py` is the only file that imports `qdrant_client` (Article IV.2).
  Lock logic, if added, lives there.
- `retrieval/reranker.py` must not import from `ingestion/` (Article IV.4).
- `retrieval/searcher.py` may import `reranker` — this is already in the
  dependency graph.
- `server/tools.py` handlers remain ≤15 lines of business logic (Article IV.1).
  No changes to `tools.py` are expected in this phase.
