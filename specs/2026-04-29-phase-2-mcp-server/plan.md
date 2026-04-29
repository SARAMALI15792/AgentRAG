# Phase 2 — MCP Server — Execution Plan

Deliverables follow strict TDD order. No implementation file may be created
before its companion test file is written and confirmed failing (red).

---

## Step 0 — Context7 Documentation Lookups

Query Context7 before writing any implementation code. No code may be written
until all lookups are complete.

- 0.1. `mcp` Python SDK (1.27.0) — tool registration decorator API,
        stdio transport runner, HTTP/SSE transport mounting.
- 0.2. `FastAPI` (0.136.x) — lifespan hooks (`@asynccontextmanager`),
        ASGI app factory pattern, router mounting.
- 0.3. `qdrant-client` (1.17.x) — `query_points` / `scroll` API surface
        used by `searcher.py`; confirm parameter names match 1.17.x.

---

## Step 1 — Retrieval

### 1.1 Write `tests/unit/test_searcher.py` — confirm red

Write all tests. Run `uv run pytest tests/unit/test_searcher.py` and confirm
every test fails before touching any implementation.

Tests must cover:
- query string returns `list[SearchResult]` sorted by `score` descending
- `top_k` parameter limits the result count exactly
- store returns empty list → searcher returns empty list, no exception raised
- metadata filters dict is forwarded to store query call unchanged

### 1.2 Implement `src/agentrag/retrieval/searcher.py`

Write minimum code to make test_searcher.py green. Then:

```
uv run pytest tests/unit/test_searcher.py     # must be green
uv run black .
uv run ruff check .
uv run mypy --strict src/                      # zero errors
```

### 1.3 Create `src/agentrag/retrieval/reranker.py` — identity stub

Pure pass-through: accepts `list[SearchResult]`, returns same list unchanged.
No tests required. Run `uv run mypy --strict src/` — confirm no new errors.

---

## Step 2 — MCP Tool Handlers

### 2.1 Write `tests/unit/test_tools.py` — confirm red

Pipeline, searcher, and store are all mocked. Run
`uv run pytest tests/unit/test_tools.py` and confirm every test fails.

Tests must cover:
- `ingest_file` delegates to pipeline; returns `IngestResult`
- `ingest_directory` delegates to pipeline for each file; returns `list[IngestResult]`
- `search_documents` delegates to searcher; returns `list[SearchResult]`
- `search_by_metadata` delegates to store; returns `list[SourceInfo]`
- `list_sources` delegates to store; returns `list[SourceInfo]`
- `get_document` delegates to store; returns `DocumentContent`
- `delete_source` delegates to store; returns `DeleteResult`
- `ingest_file`: non-existent path → error result surfaced as `IngestResult(status="error")`, not raised
- `delete_source`: unknown source_id → `DeleteResult(status="not_found")` returned
- `search_documents`: empty string query → `ValueError` raised
- `get_document`: unknown source_id → `ValueError` raised
- `search_by_metadata`: empty filters dict → `ValueError` raised

### 2.2 Implement `src/agentrag/server/tools.py`

Write all 7 handlers. Each handler ≤ 15 lines of meaningful code (Article IV.1).
Then:

```
uv run pytest tests/unit/test_tools.py        # must be green
uv run black .
uv run ruff check .
uv run mypy --strict src/                      # zero errors
```

---

## Step 3 — Server and CLI

### 3.1 Create `src/agentrag/server/app.py`

FastAPI app factory. Registers all 7 MCP tools via the SDK decorator API.
Stdio transport (primary) and HTTP/SSE transport (secondary). Lifespan hook
initializes pipeline, searcher, and store at startup using `Settings`.

### 3.2 Add `agentrag serve` to `cli.py`

Extend existing typer app. Flags: `--data-dir`, `--transport`, `--port`,
`--embed-model`. Delegates to `server/app.py`. No business logic in CLI.

### 3.3 Write and pass `tests/integration/test_server.py`

`pytest-asyncio` + `httpx`. Tests each of the 7 tools over HTTP transport.
Each test asserts the correct response shape and status code. Then:

```
uv run pytest tests/integration/test_server.py   # must be green
uv run pytest --tb=short                          # full suite green
uv run black .
uv run ruff check .
uv run mypy --strict src/                         # zero errors
```

---

## Step 4 — Manual Claude Desktop Verification

- Start server: `agentrag serve --transport stdio`
- Connect Claude Desktop via stdio config (see `specs/architecture.md`)
- Execute the scripted checklist in `validation.md` for all 7 tools
- Confirm all happy-path and all error-path responses match specification

---

## Step 5 — Post-Implementation Review

- Invoke `coderabbit:code-review` on all changed files (Article III.7)
- Resolve all blocking issues before staging
- `uv run pytest --tb=short` — zero failures, zero errors
- Commit all changes; push to `phase/2-mcp-server`
- Open PR targeting `main`
