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
- `retrieval/reranker.py` — identity stub (Phase 4 implementation)
- `server/tools.py` — 7 MCP tool handlers (all ≤15 lines per Article IV.1)
- `server/app.py` — FastAPI + FastMCP with lifespan hook, stdio + HTTP transports
- `cli.py` — `agentrag serve` command with --transport flag
- `store/qdrant.py` — added `get_full_document()` method (Article IV.1 refactor)
- Unit tests (2 modules: test_searcher.py, test_tools.py)
- Integration tests (test_server.py — HTTP transport via httpx.ASGITransport)

**Exit condition met:** All 7 tools registered. `pytest` green. `mypy --strict` passes. CI green on `main`.

---

## Phase 3A — Extended File Support — COMPLETE

**Completed:** 2026-04-30 | **Branch:** `phase/3-extended-file-support`

**Goal achieved:** Support `.docx`, `.html`, `.py`, `.ipynb` ingestion. Extend
`ingest_directory` to handle all supported types recursively.

**Shipped:**
- `python-docx` and `beautifulsoup4` added to runtime deps
- `reader.py` extended with 4 new branches (docx, html, py, ipynb)
- `ingest_directory` glob list extended to 7 types
- Test fixtures: `sample.docx`, `sample.html`, `sample.py`, `sample.ipynb`
- Unit tests + integration tests for all new file types

**Exit condition met:** All 7 file types ingest without error. `pytest` green. `mypy --strict` passes.

---

## Phase 3B — Extended Ingestion & Agentic Retrieval

**Entry condition:** Phase 3A exit condition met.

**Goal:** Extend AgentRAG to support all planned file types (office, eBook,
structured data, web, subtitle, email), add URL ingestion, and transform
retrieval from single-pass search into an agentic loop with query
decomposition, multi-query search, and relevance evaluation. After this
phase, AgentRAG ingests 20+ file types and Claude can autonomously plan,
search, evaluate, and re-search — all through native MCP tool calls.

**Dependencies:**
- Optional libraries per format group (office, ebooks, web)
- `AGENTRAG_GOOGLE_API_KEY` env var for agentic retrieval (free Google AI
  Studio key). Graceful degradation if key missing or API unreachable.

### Deliverables

Deliverables follow strict TDD execution order. Test file written and
confirmed failing before each implementation file is created.

---

**Step 0 — Context7 lookups** _(before any code)_

- `openpyxl` — `load_workbook`, sheet iteration, cell value extraction
- `python-pptx` — `Presentation`, slide iteration, text frame extraction
- `ebooklib` — `epub.read_epub`, item iteration, XHTML content
- `PyYAML` — `safe_load`, `dump`
- `google-genai` Python SDK — `Client`, `generate_content`, structured JSON output, error handling

---

**Step 1 — Dependencies (file readers)**

- [ ] Add `openpyxl 3.1.x` to `pyproject.toml` under `[project.optional-dependencies] office`
- [ ] Add `python-pptx 1.0.x` to `pyproject.toml` under `[project.optional-dependencies] office`
- [ ] Add `ebooklib 0.18.x` to `pyproject.toml` under `[project.optional-dependencies] ebooks`
- [ ] Add `mobi 0.3.x` to `pyproject.toml` under `[project.optional-dependencies] ebooks`
- [ ] Add `PyYAML 6.x` to `pyproject.toml` runtime deps
- [ ] Add `pysrt 1.1.x` to `pyproject.toml` optional `web` group
- [ ] Add `webvtt-py 0.5.x` to `pyproject.toml` optional `web` group
- [ ] Move `httpx` to both dev and optional `web` runtime dep
- [ ] Run `uv lock` — commit updated `uv.lock`

---

**Step 2 — Reader plugin registry** _(architectural prerequisite)_

- [ ] `tests/unit/test_reader_registry.py` — test plugin registration, lookup, error on unknown ext
- [ ] `src/agentrag/ingestion/reader_registry.py` — registry dict mapping extensions to reader callables
- [ ] Refactor `reader.py` to use registry instead of if/elif chain
- [ ] All existing readers registered automatically on import

---

**Step 3 — Office readers** _(TDD per file type)_

- [ ] `tests/unit/test_reader.py` — extend with `.xlsx`, `.pptx`, `.csv` test cases, confirm red
- [ ] `src/agentrag/ingestion/readers/office.py`:
      - `.xlsx` via `openpyxl`: iterate sheets → rows → cells, join as text
      - `.pptx` via `python-pptx`: iterate slides → shapes → text frames
      - `.csv` via stdlib `csv`: header + rows as text lines
- [ ] Register in reader registry

---

**Step 4 — eBook readers** _(TDD per file type)_

- [ ] `tests/unit/test_reader.py` — extend with `.epub`, `.mobi` test cases, confirm red
- [ ] `src/agentrag/ingestion/readers/ebooks.py`:
      - `.epub` via `ebooklib`: extract XHTML chapters → BeautifulSoup → text
      - `.mobi` via `mobi`: convert to HTML → BeautifulSoup → text
- [ ] Register in reader registry

---

**Step 5 — Structured data readers** _(TDD per file type)_

- [ ] `tests/unit/test_reader.py` — extend with `.json`, `.yaml`, `.xml`, `.toml` test cases, confirm red
- [ ] `src/agentrag/ingestion/readers/structured.py`:
      - `.json` via stdlib: pretty-print as text
      - `.yaml` via PyYAML: `safe_load` → `dump` as text
      - `.xml` via stdlib `xml.etree`: extract all text content
      - `.toml` via stdlib `tomllib`: load → dump as text
- [ ] Register in reader registry

---

**Step 6 — URL reader** _(TDD)_

- [ ] `tests/unit/test_url_reader.py` — mock HTTP responses, confirm red then green
- [ ] `src/agentrag/ingestion/readers/web.py`:
      - Fetch URL via `httpx` → BeautifulSoup → text (reuse `_read_html` logic)
      - Timeout, status code handling, redirect following
      - Register `url://` scheme in reader registry

---

**Step 7 — Subtitle readers** _(TDD per file type)_

- [ ] `tests/unit/test_reader.py` — extend with `.srt`, `.vtt` test cases
- [ ] `src/agentrag/ingestion/readers/media.py`:
      - `.srt` via `pysrt`: extract timestamped text segments
      - `.vtt` via `webvtt-py`: extract cue text
- [ ] Register in reader registry

---

**Step 8 — Email readers** _(TDD per file type)_

- [ ] `tests/unit/test_reader.py` — extend with `.eml`, `.mbox` test cases
- [ ] `src/agentrag/ingestion/readers/email.py`:
      - `.eml` via stdlib `email`: parse headers + body text
      - `.mbox` via stdlib `mailbox`: iterate messages → text
- [ ] Register in reader registry

---

**Step 9 — Extend `ingest_directory` + new `ingest_url` tool**

- [ ] `tests/unit/test_tools.py` — add test: `ingest_directory` with all extension types
- [ ] `src/agentrag/server/tools.py` — extend glob list with all new extensions
- [ ] `tests/unit/test_tools.py` — add `ingest_url` test
- [ ] Add `ingest_url(url: str, metadata: dict) -> IngestResult` tool handler
- [ ] Register `ingest_url` in `app.py`
- [ ] Run `uv run pytest tests/unit/test_tools.py` → green

---

**Step 10 — Integration test (file ingestion)**

- [ ] `tests/integration/test_extended_ingestion_3b.py` — real Qdrant, real files:
      - Ingest one fixture file per new type → `chunk_count > 0`
      - `ingest_directory` on mixed directory → all types ingested
      - Add fixture files to `tests/fixtures/`

---

**Step 11 — New domain types for agentic retrieval** _(no tests — pure dataclasses)_

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
    sufficient: bool         # True if at least one chunk scores >= 0.7
    suggested_queries: list[str]  # alternative queries if not sufficient
```

---

**Step 12 — Query planner**

- [ ] `tests/unit/test_query_planner.py` ← write first, confirm red
      (Gemini client is mocked — no live API calls in unit tests)
      - simple query → `QueryPlan` with `sub_queries = [original_query]`
      - compound query ("compare X and Y") → `sub_queries` has >= 2 items
      - API key missing or Gemini unavailable → degrades gracefully, returns single-item plan
      - `original_query` always preserved in output
- [ ] `src/agentrag/retrieval/query_planner.py` ← implement to make tests green
      Calls Gemini 2.0 Flash via `google-genai` SDK (`AGENTRAG_GOOGLE_API_KEY`).
      Prompt instructs the model to return a JSON list of sub-questions.
      Graceful degradation: if API key missing, quota exceeded, or response is invalid JSON,
      returns `QueryPlan(original_query, sub_queries=[original_query])`.

---

**Step 13 — Chunk evaluator**

- [ ] `tests/unit/test_evaluator.py` ← write first, confirm red
      (Gemini client mocked — no live API calls in unit tests)
      - all chunks score >= 0.7 → `sufficient = True`
      - all chunks score < 0.7 → `sufficient = False`, `suggested_queries` non-empty
      - empty chunk list → `sufficient = False`
      - each `ChunkScore.score` is in `[0.0, 1.0]`
- [ ] `src/agentrag/retrieval/evaluator.py` ← implement to make tests green
      Calls Gemini 2.0 Flash to score each chunk's relevance to the query.
      Graceful degradation: if API key missing or Gemini unavailable, scores all chunks at `0.5`
      and sets `sufficient = True` (pass-through — does not block retrieval).

---

**Step 14 — Agentic MCP tool handlers**

- [ ] `tests/unit/test_agentic_tools.py` ← write first, confirm red
      (query_planner, evaluator, searcher all mocked)
      - `search_multi`: merges results from 3 queries, deduplicates by `chunk_id`
      - `search_multi`: empty `queries` list raises `ValueError`
      - `evaluate_chunks`: delegates to evaluator, returns `EvaluationReport`
      - `plan_query`: delegates to query_planner, returns `QueryPlan`
      - all handlers <= 15 lines of meaningful code (Article IV.1)
- [ ] Add to `src/agentrag/server/tools.py`:
      - `search_multi(queries: list[str], top_k: int) -> list[SearchResult]`
        Calls `searcher.search` for each query, deduplicates by `chunk_id`
        (keeping highest score), returns merged list sorted by score descending.
      - `evaluate_chunks(query: str, results: list[SearchResult]) -> EvaluationReport`
        Thin delegate to `evaluator.evaluate`.
      - `plan_query(query: str) -> QueryPlan`
        Thin delegate to `query_planner.plan`.
- [ ] Register all 3 new tools in `src/agentrag/server/app.py` via `@mcp.tool()` decorator,
      same pattern as the 7 existing tools.

---

**Step 15 — Integration test (agentic retrieval)**

- [ ] `tests/integration/test_agentic_retrieval.py` — real Qdrant, Gemini optional:
      - ingest `sample.txt`, call `plan_query` → verify sub-queries are strings
      - call `search_multi` with 2 queries → result count <= `top_k`, no duplicates
      - call `evaluate_chunks` on results → `EvaluationReport` returned without error
      - full loop: `plan_query` → `search_multi` → `evaluate_chunks` → if not
        sufficient → `search_multi` with `suggested_queries` → verify second pass
        returns results
      - `AGENTRAG_GOOGLE_API_KEY` absent: all three tools complete without raising (graceful degrade)

---

**Step 16 — Exit gate**

- [ ] `scripts/verify_phase3b.sh`

**Exit condition:** All 20+ file types ingest without error. Reader plugin
registry works. `ingest_url` MCP tool callable. `search_multi`,
`evaluate_chunks`, and `plan_query` callable from Claude Desktop. Full agentic
loop test passes. Gemini graceful-degrade verified. URL, subtitle, and email
ingestion work. `pytest` green. `mypy --strict` passes.

---

## Phase 4 — Search Quality

**Entry condition:** Phase 3B exit condition met.

**Goal:** Improve retrieval precision. Activate the cross-encoder re-ranker stub
(already stubbed in Phase 2 `reranker.py`), harden metadata filtering, and verify
concurrent upsert safety. No new external services.

**Dependency:** None. All improvements use existing stack.

### Deliverables

Deliverables follow strict TDD execution order.

---

**Step 0 — Context7 lookup** _(before any code)_

- `sentence-transformers` — `CrossEncoder`, `predict`, score normalization API

---

**Step 1 — Metadata filter hardening**

- [ ] `tests/integration/test_search_filters.py` — confirm red, then green:
      - `search_documents` with `filters={"filename": X}` returns only chunks from X
      - `search_by_metadata` with `{"source_id": X}` returns correct `SourceInfo`
      - `search_by_metadata` with unknown key returns empty list, does not raise
      - At least 3 distinct filter fields tested (filename, source_id, one metadata key)
- [ ] Fix any gaps in `searcher.py` and `store/qdrant.py` filter logic found by the tests

---

**Step 2 — Cross-encoder re-ranker**

- [ ] `tests/unit/test_reranker.py` — extend (currently empty; identity stub has no tests):
      - `AGENTRAG_RERANK=false` → identity pass-through, no CrossEncoder loaded
      - `AGENTRAG_RERANK=true` → results re-ordered by cross-encoder score descending
      - CrossEncoder mocked in unit tests — no model download in CI
- [ ] `src/agentrag/retrieval/reranker.py` — replace identity stub with real implementation:
      - Load `CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")` when `settings.rerank=True`
      - Identity pass-through when `settings.rerank=False` (zero overhead default)
- [ ] `searcher.py` — pass results through `rerank()` after `store.query()`

---

**Step 3 — Concurrent upsert safety**

- [ ] `tests/integration/test_concurrent_upsert.py`:
      - Re-ingest `sample.txt` 3x concurrently via `threading.Thread`
      - After all threads complete: `list_sources()` returns exactly 1 entry for that source
      - `chunk_count` is stable (same value on every run)

---

**Step 4 — Benchmarks**

- [ ] `scripts/benchmark_retrieval.py` — ingest sample corpus, run 10 queries,
      log top-k results and scores. Exit 0. Not gated on score threshold.

---

**Step 5 — Exit gate**

- [ ] `scripts/verify_phase4.sh`

**Exit condition:** Metadata filters pass integration tests with >=3 fields. Re-ranker
activates via `AGENTRAG_RERANK=true`. Concurrent upsert test passes. `pytest` green.
`mypy --strict` passes.

---

## Phase 5 — Distribution

**Entry condition:** Phase 4 exit condition met.

**Goal:** AgentRAG is installable from PyPI. A new user can go from zero to a
running MCP server in under 60 seconds.

### Deliverables

---

**Step 1 — Package metadata**

- [ ] `pyproject.toml` finalized: classifiers, license (`MIT`), description, homepage URL,
      `[project.urls]` with GitHub and docs links
- [ ] Version pinned at `0.1.0` in `pyproject.toml`
- [ ] `uv run python -m build` produces a clean wheel with no warnings

---

**Step 2 — Zero-install entry point**

- [ ] `agentrag serve` works via `uvx agentrag serve` on a clean machine (no `pip install`)
- [ ] Claude Desktop config snippet verified: `"command": "uvx", "args": ["agentrag", "serve"]`

---

**Step 3 — Documentation**

- [ ] `README.md` with:
      - 60-second quickstart (install → set `AGENTRAG_GOOGLE_API_KEY` → `agentrag serve`)
      - Claude Desktop JSON config block (copy-paste ready)
      - Full table of all CLI flags and env vars
      - All MCP tools listed with one-line descriptions
      - Supported file types table with optional dependency groups
- [ ] `CHANGELOG.md` with `v0.1.0` entry summarising all phases

---

**Step 4 — CI hardening**

- [ ] `.github/workflows/ci.yml` — extend with Python matrix: `[3.12, 3.13]`
- [ ] GitHub Actions release workflow — new `publish` job triggered on `v*` tag push:
      `uv build` → `uv publish` → PyPI

---

**Step 5 — Publish**

- [ ] `git tag v0.1.0 && git push origin v0.1.0` → triggers CI publish job
- [ ] `pip install agentrag` on a clean machine → `agentrag serve` starts without error
- [ ] `uvx agentrag serve` on a clean machine → server starts without error

---

**Step 6 — Exit gate**

- [ ] `scripts/verify_phase5.sh`

**Exit condition:** `pip install agentrag && agentrag serve` works on a clean machine.
`uvx agentrag serve` works. CI matrix green across Python 3.12 and 3.13.
PyPI package published at `https://pypi.org/project/agentrag/`.

---

## Phase 6 — Multi-Collection & Streaming Retrieval

**Entry condition:** Phase 5 exit condition met.

**Goal:** Add workspace isolation via named Qdrant collections and async
streaming retrieval. Users can maintain separate knowledge bases (e.g., one
per project) and Claude receives results as they score rather than waiting for
the full top-k set.

**Dependency:** None. All capabilities use existing `qdrant-client` and stdlib `asyncio`.

### Deliverables

---

**Step 1 — Multi-collection support**

- [ ] `AGENTRAG_COLLECTION` env var (default: `documents`) — configures active collection
- [ ] `tests/unit/test_store.py` — extend: two collections, same source_id, isolated data
- [ ] `store/qdrant.py` — replace hardcoded `_COLLECTION` with `settings.collection`
- [ ] New MCP tools:
      - `list_collections() -> list[str]` — list all Qdrant collections
      - `switch_collection(name: str) -> str` — set active collection for subsequent calls
      - `create_collection(name: str) -> str` — create new named collection
- [ ] Integration test: ingest into collection A, search in collection B → empty results.
      Switch to A → results found.

---

**Step 2 — Streaming retrieval**

- [ ] `src/agentrag/retrieval/streaming.py` — async generator yielding `SearchResult` as scored
- [ ] `tests/unit/test_streaming.py` — async test consuming generator, verify order
- [ ] New MCP tool: `search_stream(query: str, top_k: int) -> AsyncIterator[SearchResult]`
      (depends on MCP SDK support for streaming — if not available, falls back to batch)
- [ ] Integration test: streaming search returns same results as batch search

---

**Step 3 — Exit gate**

- [ ] `scripts/verify_phase6.sh`

**Exit condition:** Named collections work. Streaming search works or gracefully
falls back. `pytest` green. `mypy --strict` passes.

---

## Phase 7 — Cloud Sync (Optional, User Opt-In)

**Entry condition:** Phase 6 exit condition met.

**Goal:** Optional cloud sync for the vector store. Users can back up and
restore their Qdrant data to cloud storage. Privacy-preserving: encrypted
at rest, user-controlled keys, explicit opt-in only.

**Dependency:** Cloud storage library (S3, GDrive, or Azure Blob — chosen at
phase start with user approval). User must provide credentials.

### Deliverables

---

**Step 1 — Sync abstraction layer**

- [ ] `src/agentrag/sync/base.py` — `SyncBackend` protocol: `push()`, `pull()`, `status()`
- [ ] `src/agentrag/sync/local.py` — local directory backup (always available, no cloud)

---

**Step 2 — Cloud backend** _(library chosen at phase start)_

- [ ] `src/agentrag/sync/cloud.py` — implements `SyncBackend` for chosen provider
- [ ] Encryption at rest using user-provided key
- [ ] New env vars: `AGENTRAG_SYNC_BACKEND`, `AGENTRAG_SYNC_ENDPOINT`, `AGENTRAG_SYNC_KEY`

---

**Step 3 — CLI commands**

- [ ] `agentrag sync push` — upload current Qdrant snapshot
- [ ] `agentrag sync pull` — restore from latest snapshot
- [ ] `agentrag sync status` — show last sync time and diff

---

**Step 4 — Exit gate**

- [ ] `scripts/verify_phase7.sh`

**Exit condition:** Local backup works. Cloud sync works with chosen provider.
No data syncs without explicit user action. `pytest` green. `mypy --strict` passes.
