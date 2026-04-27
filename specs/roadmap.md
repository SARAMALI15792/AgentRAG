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

- [ ] `pyproject.toml` with all Phase 1 dependencies, entry points, and tool config
- [ ] `src/agentrag/config.py` — typed `Settings` via `pydantic-settings`
- [ ] `src/agentrag/store/qdrant.py` — Qdrant embedded client wrapper
      - `upsert(chunks)`, `query(vector, top_k, filters)`, `delete(source_id)`, `list_sources()`
- [ ] `src/agentrag/ingestion/reader.py` — file → raw text
      - Supports: `.pdf` (pymupdf), `.md` (plain), `.txt` (plain)
      - Returns: `RawDocument(source_id, filename, text, metadata)`
- [ ] `src/agentrag/ingestion/chunker.py` — text → `List[Chunk]`
      - Sliding window: `chunk_size=512` tokens, `overlap=64` tokens
      - Returns: `List[Chunk(chunk_id, source_id, text, start, end)]`
- [ ] `src/agentrag/ingestion/embedder.py` — `List[Chunk]` → `List[EmbeddedChunk]`
      - Uses `sentence-transformers`, model from `Settings`
      - Returns: `List[EmbeddedChunk(chunk_id, source_id, vector, text, metadata)]`
- [ ] `src/agentrag/ingestion/pipeline.py` — orchestrates reader → chunker → embedder → store
      - `ingest(path: Path, metadata: dict) -> IngestResult`
- [ ] `src/agentrag/cli.py` — `agentrag ingest <file>` command (manual testing)
- [ ] `tests/unit/` — full unit test coverage for reader, chunker, embedder, store wrapper
- [ ] `tests/integration/test_pipeline.py` — end-to-end ingest of a real PDF and TXT file

**Exit condition:** `pytest` is green. `agentrag ingest <file>` stores chunks in Qdrant. `mypy --strict` passes.

---

## Phase 2 — MCP Server

**Entry condition:** Phase 1 exit condition met.

**Goal:** A fully functional MCP server exposing all 7 tools. Claude Desktop
can connect to it and call all tools successfully.

### Deliverables

- [ ] `src/agentrag/server/app.py` — FastAPI app with MCP SDK integration
- [ ] `src/agentrag/server/tools.py` — all 7 MCP tool handlers (thin delegation only)
      - `ingest_file`, `ingest_directory`, `search_documents`, `search_by_metadata`,
        `list_sources`, `get_document`, `delete_source`
- [ ] `src/agentrag/retrieval/searcher.py` — query → `List[SearchResult]`
      - Embeds query, calls Qdrant nearest-neighbor, applies metadata filters
- [ ] `src/agentrag/retrieval/reranker.py` — stub (identity reranker for now)
- [ ] `agentrag serve` CLI command — starts MCP server on stdio or HTTP
- [ ] Claude Desktop integration: manual verification that all 7 tools are callable
- [ ] `tests/unit/test_tools.py` — unit tests for each tool handler (mocked store)
- [ ] `tests/integration/test_server.py` — HTTP endpoint integration tests via `pytest-asyncio`

**Exit condition:** All 7 MCP tools callable from Claude Desktop. `pytest` green. `mypy --strict` passes.

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

- [ ] Metadata filter logic in `searcher.py` (all `search_documents` filter keys work)
- [ ] Cross-encoder re-ranker in `reranker.py` (optional, activated via config)
- [ ] Source deduplication: re-ingesting the same file updates chunks, does not duplicate
- [ ] `search_by_metadata` tool fully functional with at least 3 filter fields
- [ ] Benchmarks: retrieval quality tested on a sample corpus (results logged, not gated)

**Exit condition:** Re-ingest is idempotent. Metadata filters work end-to-end. `pytest` green.

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
