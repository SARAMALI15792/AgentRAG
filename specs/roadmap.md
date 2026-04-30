# Roadmap

Each phase has a clear entry condition, a set of concrete deliverables, and an
exit condition. No phase begins until the previous phase's exit condition is met.
Phases are not time-boxed — they are scope-boxed.

---

## Phase 1 — Core Ingestion Pipeline — COMPLETE

**Completed:** 2026-04-29 | **PR:** #1 → `main`

**Goal achieved:** Working, tested local ingestion pipeline — read → chunk → embed → persist.

**Shipped:**
- Project skeleton, `pyproject.toml`, pre-commit hook, CI workflow, test fixtures
- `types.py` — 8 domain dataclasses
- `config.py` — pydantic-settings `Settings`
- `store/qdrant.py` — embedded Qdrant (sole importer of `qdrant_client`)
- `ingestion/reader.py` — `.txt`, `.md`, `.pdf` via pymupdf
- `ingestion/chunker.py` — sliding-window tokenizer chunking (512 tokens / 64 overlap)
- `ingestion/embedder.py` — sentence-transformers batch embedding
- `ingestion/pipeline.py` — orchestrates reader → chunker → embedder → store; never raises
- `cli.py` — `agentrag ingest` and `agentrag list`
- `scripts/verify_phase1.sh` — deterministic exit gate
- Unit tests (6 modules) + integration tests (real Qdrant embedded)

**Exit condition met:** `scripts/verify_phase1.sh` exits 0. CI green on `main`. `mypy --strict` passes.

---

## Phase 2 — MCP Server — COMPLETE

**Completed:** 2026-04-29 | **PR:** #3 → `main`

**Goal achieved:** Fully functional MCP server with 7 tools callable from Claude Desktop via stdio.

**Shipped:**
- `retrieval/searcher.py` — embeds query, delegates to QdrantStore
- `retrieval/reranker.py` — identity stub (Phase 5 implementation)
- `server/tools.py` — 7 MCP tool handlers (all ≤15 lines per Article IV.1)
- `server/app.py` — FastAPI + FastMCP with lifespan hook, stdio + HTTP transports
- `cli.py` — `agentrag serve` command with --transport flag
- `store/qdrant.py` — added `get_full_document()` method (Article IV.1 refactor)
- Unit tests (2 modules: test_searcher.py, test_tools.py)
- Integration tests (test_server.py — HTTP transport via httpx.ASGITransport)

**Exit condition met:** All 7 tools registered. `pytest` green. `mypy --strict` passes. CI green on `main`.

---

## Phase 3 — Extended File Support

**Entry condition:** Phase 2 exit condition met.

**Goal:** Support `.docx`, `.html`, `.py`, `.ipynb` ingestion. Extend
`ingest_directory` to handle all supported types recursively.

### Deliverables

- [ ] `python-docx` added to dependencies (with approval)
- [ ] `beautifulsoup4` added to dependencies (with approval)
- [ ] `reader.py` extended: `.docx`, `.html`, `.py`, `.ipynb` readers
- [ ] `ingest_directory` tool: recursive glob, per-extension filtering
- [ ] `tests/unit/` — new reader tests for each file type
- [ ] Update `specs/tech-stack.md` to move Phase 3 libs from "planned" to "active"

**Exit condition:** `agentrag ingest ./my-repo/` recursively ingests a mixed codebase. `pytest` green.

---

## Phase 4 — Agentic Retrieval Loop

**Entry condition:** Phase 3 exit condition met.

**Goal:** Transform AgentRAG from a passive RAG server into an active retrieval
partner. Add three MCP tools that close the single-pass retrieval gap: query
decomposition, relevance evaluation, and multi-query search. After this phase,
Claude can decompose a complex question into sub-queries, search each
independently, evaluate whether the results actually answer the question, and
decide whether to re-search — all through tool calls, without special prompting.

**Dependency:** Requires `AGENTRAG_GOOGLE_API_KEY` env var (free Google AI Studio key). Graceful degradation if key missing or API unreachable.

### Deliverables

Deliverables follow strict TDD execution order. Test file written and
confirmed failing before each implementation file is created.

---

**Step 1 — New domain types** _(no tests — pure dataclasses)_

Add to `src/agentrag/types.py`:

```python
@dataclass
class QueryPlan:
    original_query: str
    sub_queries: list[str]   # 1–4 focused sub-questions derived from original

@dataclass
class ChunkScore:
    chunk_id: str
    source_id: str
    score: float             # 0.0 (irrelevant) → 1.0 (directly answers query)
    reason: str              # one-sentence explanation of the score

@dataclass
class EvaluationReport:
    query: str
    scored_chunks: list[ChunkScore]
    sufficient: bool         # True if at least one chunk scores ≥ 0.7
    suggested_queries: list[str]  # alternative queries if not sufficient
```

---

**Step 2 — Query planner**

- [ ] `tests/unit/test_query_planner.py` ← write first, confirm red
      (Gemini client is mocked — no live API calls in unit tests)
      - simple query → `QueryPlan` with `sub_queries = [original_query]`
      - compound query ("compare X and Y") → `sub_queries` has ≥ 2 items
      - API key missing or Gemini unavailable → degrades gracefully, returns single-item plan
      - `original_query` always preserved in output
- [ ] `src/agentrag/retrieval/query_planner.py` ← implement to make tests green
      Calls Gemini 2.0 Flash via `google-genai` SDK (`AGENTRAG_GOOGLE_API_KEY`).
      Prompt instructs the model to return a JSON list of sub-questions.
      Graceful degradation: if API key missing, quota exceeded, or response is invalid JSON,
      returns `QueryPlan(original_query, sub_queries=[original_query])`.

---

**Step 3 — Chunk evaluator**

- [ ] `tests/unit/test_evaluator.py` ← write first, confirm red
      (Gemini client mocked — no live API calls in unit tests)
      - all chunks score ≥ 0.7 → `sufficient = True`
      - all chunks score < 0.7 → `sufficient = False`, `suggested_queries` non-empty
      - empty chunk list → `sufficient = False`
      - each `ChunkScore.score` is in `[0.0, 1.0]`
- [ ] `src/agentrag/retrieval/evaluator.py` ← implement to make tests green
      Calls Gemini 2.0 Flash to score each chunk's relevance to the query.
      Graceful degradation: if API key missing or Gemini unavailable, scores all chunks at `0.5`
      and sets `sufficient = True` (pass-through — does not block retrieval).

---

**Step 4 — New MCP tool handlers**

- [ ] `tests/unit/test_agentic_tools.py` ← write first, confirm red
      (query_planner, evaluator, searcher all mocked)
      - `search_multi`: merges results from 3 queries, deduplicates by `chunk_id`
      - `search_multi`: empty `queries` list raises `ValueError`
      - `evaluate_chunks`: delegates to evaluator, returns `EvaluationReport`
      - `plan_query`: delegates to query_planner, returns `QueryPlan`
      - all handlers ≤ 15 lines of meaningful code (Article IV.1)
- [ ] Add to `src/agentrag/server/tools.py`:
      - `search_multi(queries: list[str], top_k: int) -> list[SearchResult]`
        Calls `searcher.search` for each query, deduplicates by `chunk_id`
        (keeping highest score), returns merged list sorted by score descending.
      - `evaluate_chunks(query: str, results: list[SearchResult]) -> EvaluationReport`
        Thin delegate to `evaluator.evaluate`.
      - `plan_query(query: str) -> QueryPlan`
        Thin delegate to `query_planner.plan`.

---

**Step 5 — Integration**

- [ ] `tests/integration/test_agentic_retrieval.py` — real Qdrant, Gemini optional:
      - ingest `sample.txt`, call `plan_query` → verify sub-queries are strings
      - call `search_multi` with 2 queries → result count ≤ `top_k`, no duplicates
      - call `evaluate_chunks` on results → `EvaluationReport` returned without error
      - full loop: `plan_query` → `search_multi` → `evaluate_chunks` → if not
        sufficient → `search_multi` with `suggested_queries` → verify second pass
        returns results
      - `AGENTRAG_GOOGLE_API_KEY` absent: all three tools complete without raising (graceful degrade)

---

**Exit condition:** `search_multi`, `evaluate_chunks`, and `plan_query` are
callable from Claude Desktop. Full agentic loop test passes. Gemini graceful-degrade
verified. `pytest` green. `mypy --strict` passes.

---

## Phase 5 — Search Quality

**Entry condition:** Phase 4 exit condition met.

**Goal:** Improve retrieval precision. Add metadata-driven filtering, optional
re-ranking, and deduplication on re-ingest.

**Dependency:** None. All improvements use existing stack.

### Deliverables

- [ ] Metadata filter logic in `searcher.py` — all filter keys in
      `search_documents` and `search_by_metadata` are applied correctly;
      at least 3 filter fields covered by integration tests
- [ ] Cross-encoder re-ranker in `reranker.py` — real implementation
      (optional, activated via `AGENTRAG_RERANK=true` config flag);
      identity reranker remains the default
- [ ] Concurrent upsert safety: verify that re-ingesting the same file
      from two simultaneous calls does not produce duplicate or corrupt
      chunks (basic stress test, not a strict concurrency guarantee)
- [ ] `search_by_metadata` tool fully functional with at least 3 filter fields
- [ ] Benchmarks: retrieval quality tested on a sample corpus (results logged,
      not gated on a score threshold)

**Exit condition:** Metadata filters work end-to-end. Re-ranker activates via
config. `pytest` green. `mypy --strict` passes.

---

## Phase 6 — Distribution

**Entry condition:** Phase 5 exit condition met.

**Goal:** AgentRAG is installable from PyPI. A new user can go from zero to a
running MCP server in under 60 seconds.

### Deliverables

- [ ] `pyproject.toml` finalized for PyPI: classifiers, license, description, URLs
- [ ] `agentrag serve` works via `uvx agentrag serve` (zero-install)
- [ ] `README.md` with: 60-second quickstart, Claude Desktop config snippet, all CLI flags
- [ ] GitHub Actions CI: established in Phase 1 — verify it is still green;
      extend `.github/workflows/ci.yml` with matrix testing across Python 3.12+
      if needed
- [ ] GitHub Actions release workflow: add publish job to existing
      `.github/workflows/ci.yml` triggered on version tag → PyPI publish
- [ ] `CHANGELOG.md` with `v0.1.0` entry
- [ ] PyPI package published and installable

**Exit condition:** `pip install agentrag && agentrag serve` works on a clean machine. CI is green.
