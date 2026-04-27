# Roadmap

Each phase has a clear entry condition, a set of concrete deliverables, and an
exit condition. No phase begins until the previous phase's exit condition is met.
Phases are not time-boxed — they are scope-boxed.

---

## Phase 1 — Core Ingestion Pipeline

**Entry condition:** Empty repository. Constitution and specs written.

**Goal:** A working, tested local ingestion pipeline that can read a file,
chunk it, embed it locally, and persist it to Qdrant. No MCP server yet —
just the core data pipeline verified through tests and a minimal CLI command.

### Deliverables

Deliverables follow strict TDD execution order. For every implementation
module, the test file is written and confirmed **failing** before the
implementation file is created. No implementation file is opened until its
test file exists and its tests are red.

---

**Step 1 — Skeleton and fixtures** _(no tests required — no logic)_

- [ ] Full directory skeleton — all packages created first so imports resolve:
      `src/agentrag/__init__.py`, `src/agentrag/ingestion/__init__.py`,
      `src/agentrag/retrieval/__init__.py`, `src/agentrag/store/__init__.py`,
      `src/agentrag/server/__init__.py`, `tests/unit/`, `tests/integration/`
- [ ] `tests/fixtures/sample.txt` — plain-text fixture with ≥ 600 words
      (enough to produce multiple chunks at 512-token chunk size)
- [ ] `tests/fixtures/sample.pdf` — single-page PDF fixture committed as binary,
      produced once via a helper script and never regenerated automatically
- [ ] `pyproject.toml` — all Phase 1 runtime and dev dependencies, entry points,
      and full tool config:
      black `line-length = 88`; ruff extends black; mypy `strict = true`;
      pytest `asyncio_mode = "auto"`; coverage source = `["src"]`

---

**Step 2 — Domain types** _(no tests — pure dataclasses, zero logic)_

- [ ] `src/agentrag/types.py` — every cross-module dataclass lives here and
      nowhere else:
      `RawDocument`, `Chunk`, `EmbeddedChunk`, `SearchResult`, `SourceInfo`,
      `IngestResult`, `DeleteResult`, `DocumentContent`

---

**Step 3 — Config**

- [ ] `tests/unit/test_config.py` ← write first, confirm red
      - default values load without env vars set
      - env var `AGENTRAG_DATA_DIR` overrides `data_dir`
      - `data_dir` is created on disk when it does not exist
      - `vector_dim` defaults to `384`
- [ ] `src/agentrag/config.py` ← implement to make tests green
      `Settings` via `pydantic-settings`. Auto-creates `data_dir` on
      instantiation. Includes `vector_dim: int = 384` (output dimension of
      `all-MiniLM-L6-v2` — must match the Qdrant collection vector size).

---

**Step 4 — Vector store**

- [ ] `tests/unit/test_store.py` ← write first, confirm red
      - `upsert` then `query` returns the inserted chunks
      - `upsert` same `source_id` twice → chunk count unchanged (dedup)
      - `delete(source_id)` removes all points for that source
      - `list_sources()` returns correct `SourceInfo` after upsert
      - `query` on empty collection returns `[]`, does not raise
      - `list_sources()` on empty store returns `[]`
- [ ] `src/agentrag/store/qdrant.py` ← implement to make tests green
      Qdrant embedded client. Collection created on init with
      `vector_size = settings.vector_dim`, distance = Cosine.
      `upsert`: deletes all existing points for `source_id` before inserting
      (dedup by source). Only file in the codebase permitted to import
      `qdrant_client`.

---

**Step 5 — Reader**

- [ ] `tests/unit/test_reader.py` ← write first, confirm red
      - `.txt` path → `RawDocument` with correct `text` and `filename`
      - `.md` path → `RawDocument`
      - `.pdf` path → `RawDocument` with non-empty `text`
      - `source_id` is a 16-char hex string (SHA-256 of resolved path)
      - non-existent path raises `FileNotFoundError`
      - unsupported extension raises `ValueError`
      - empty file raises `ValueError`
- [ ] `src/agentrag/ingestion/reader.py` ← implement to make tests green
      `source_id = hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]`
      Supports `.pdf` (pymupdf/fitz), `.md` and `.txt` (plain `read_text`).

---

**Step 6 — Chunker**

- [ ] `tests/unit/test_chunker.py` ← write first, confirm red
      - long text → multiple chunks, each ≤ `chunk_size` tokens
      - consecutive chunks overlap by `overlap` tokens
      - text shorter than `chunk_size` → exactly one chunk
      - `chunk_id` format is `"{source_id}_{index}"`
      - `index` is zero-based and contiguous
- [ ] `src/agentrag/ingestion/chunker.py` ← implement to make tests green
      Uses `AutoTokenizer.from_pretrained(settings.embed_model)` for all token
      counting so chunk boundaries align exactly with the embedder's vocabulary.
      Sliding window: `chunk_size = 512` tokens, `overlap = 64` tokens.

---

**Step 7 — Embedder**

- [ ] `tests/unit/test_embedder.py` ← write first, confirm red
      (SentenceTransformer is mocked — no model download in unit tests)
      - output list length equals input chunk list length
      - each vector has length `settings.vector_dim`
      - `chunk_id`, `source_id`, and `text` are preserved in output
      - `metadata` dict is passed through unchanged
- [ ] `src/agentrag/ingestion/embedder.py` ← implement to make tests green
      Loads `SentenceTransformer(settings.embed_model)`. Batch-encodes all
      chunk texts in one call. Returns `List[EmbeddedChunk]`.

---

**Step 8 — Pipeline**

- [ ] `tests/unit/test_pipeline.py` ← write first, confirm red
      (store and embedder are mocked — no Qdrant or model in unit tests)
      - success: returns `IngestResult(status="ok", chunk_count > 0)`
      - non-existent file: returns `IngestResult(status="error")`, does not raise
      - unsupported extension: returns `IngestResult(status="error")`
      - embedder failure: returns `IngestResult(status="error")`
- [ ] `src/agentrag/ingestion/pipeline.py` ← implement to make tests green
      `ingest(path: Path, metadata: dict[str, Any]) -> IngestResult`
      Orchestrates reader → chunker → embedder → store. All exceptions are
      caught and surfaced as `IngestResult(status="error", error=str(e))` —
      the pipeline never raises.

---

**Step 9 — CLI**

- [ ] `src/agentrag/cli.py` — typer app, two commands:
      - `agentrag ingest <file>` — calls `pipeline.ingest`, prints `IngestResult`
      - `agentrag list` — calls `store.list_sources()`, prints a source table
      This is the only file that calls `logging.basicConfig()`.

---

**Step 10 — Integration**

- [ ] `tests/integration/test_pipeline.py` — real Qdrant (embedded), real files:
      - ingest `tests/fixtures/sample.txt` → `chunk_count > 0`
      - ingest `tests/fixtures/sample.pdf` → `chunk_count > 0`
      - re-ingest `sample.txt` → `chunk_count` identical to first ingest (dedup)
      - `list_sources()` returns the ingested source after ingest

---

**Exit condition:** `pytest` is green with zero failures. `agentrag ingest
<file>` followed by `agentrag list` shows the ingested source with correct
chunk count. `mypy --strict` passes on `src/` with zero errors.

---

## Phase 2 — MCP Server

**Entry condition:** Phase 1 exit condition met.

**Goal:** A fully functional MCP server exposing all 7 tools. Claude Desktop
can connect to it and call all tools successfully.

### Deliverables

Deliverables follow strict TDD execution order. Test file written and
confirmed failing before each implementation file is created.

---

**Step 1 — Retrieval**

- [ ] `tests/unit/test_searcher.py` ← write first, confirm red
      (store mocked — no Qdrant in unit tests)
      - query returns `List[SearchResult]` ranked by score descending
      - `top_k` parameter limits result count
      - empty result from store → empty list returned, no exception
      - metadata filters are forwarded to the store query unchanged
- [ ] `src/agentrag/retrieval/searcher.py` ← implement to make tests green
      Embeds query via `embedder.py` (query embedding only — permitted cross-
      boundary per architecture), calls `store.query`, applies `reranker`.
- [ ] `src/agentrag/retrieval/reranker.py` — identity stub: returns input
      unchanged. No tests needed for an identity function.

---

**Step 2 — MCP tools**

- [ ] `tests/unit/test_tools.py` ← write first, confirm red
      (pipeline, searcher, store all mocked)
      - each of the 7 handlers delegates to the correct backing function
      - `ingest_file`: non-existent path → error result surfaced, not raised
      - `delete_source`: unknown source_id → `status="not_found"` returned
      - `search_documents`: empty query raises `ValueError`
      - `get_document`: unknown source_id raises `ValueError`
      - `search_by_metadata`: empty filters raises `ValueError`
- [ ] `src/agentrag/server/tools.py` ← implement to make tests green
      All 7 handlers: `ingest_file`, `ingest_directory`, `search_documents`,
      `search_by_metadata`, `list_sources`, `get_document`, `delete_source`.
      `ingest_directory` in Phase 2 supports Phase 1 file types only
      (`.pdf`, `.md`, `.txt`) — Phase 3 extends it to additional types.
      Each handler is ≤ 15 lines of meaningful code (Article IV.1).

---

**Step 3 — Server**

- [ ] `src/agentrag/server/app.py` — FastAPI app with MCP SDK tool registration.
      Transport priority: **stdio first** (Claude Desktop is the exit condition),
      HTTP second. Both must function.
- [ ] `agentrag serve` added to `cli.py` — starts the MCP server.
- [ ] `tests/integration/test_server.py` — HTTP transport tests via
      `pytest-asyncio` + `httpx`. Tests each of the 7 tools over HTTP.

---

**Step 4 — Manual verification**

- [ ] Claude Desktop integration: connect via stdio, call all 7 tools manually,
      confirm correct responses for both happy-path and error inputs.

---

**Exit condition:** All 7 MCP tools callable from Claude Desktop via stdio.
`pytest` green. `mypy --strict` passes on `src/` with zero errors.

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

## Phase 4 — Search Quality

**Entry condition:** Phase 3 exit condition met.

**Goal:** Improve retrieval precision. Add metadata-driven filtering, optional
re-ranking, and deduplication on re-ingest.

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

## Phase 5 — Distribution

**Entry condition:** Phase 4 exit condition met.

**Goal:** AgentRAG is installable from PyPI. A new user can go from zero to a
running MCP server in under 60 seconds.

### Deliverables

- [ ] `pyproject.toml` finalized for PyPI: classifiers, license, description, URLs
- [ ] `agentrag serve` works via `uvx agentrag serve` (zero-install)
- [ ] `README.md` with: 60-second quickstart, Claude Desktop config snippet, all CLI flags
- [ ] GitHub Actions CI: lint + type check + test on push to `main`
- [ ] GitHub Actions release workflow: tag → PyPI publish
- [ ] `CHANGELOG.md` with `v0.1.0` entry
- [ ] PyPI package published and installable

**Exit condition:** `pip install agentrag && agentrag serve` works on a clean machine. CI is green.
