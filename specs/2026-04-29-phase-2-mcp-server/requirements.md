# Phase 2 — MCP Server — Requirements

This document records the full scope, locked decisions, and context for Phase 2.
It governs the implementation session. If `specs/roadmap.md` and this file
conflict on any point, this file is authoritative for the duration of Phase 2.

---

## Scope

### In Scope

- `src/agentrag/retrieval/searcher.py` — semantic search over the Qdrant store
- `src/agentrag/retrieval/reranker.py` — identity pass-through stub (no real ranking)
- `src/agentrag/server/tools.py` — all 7 MCP tool handlers
- `src/agentrag/server/app.py` — FastAPI app with MCP SDK tool registration
- `cli.py` — `agentrag serve` subcommand added to the existing typer app
- `tests/unit/test_searcher.py`, `test_tools.py`
- `tests/integration/test_server.py`
- Manual verification against Claude Desktop via stdio transport

### Out of Scope

- No cross-encoder re-ranking (Phase 5)
- No Gemini integration (Phase 4)
- No `.docx`, `.html`, `.py`, `.ipynb` ingestion (Phase 4) — `ingest_directory`
  supports Phase 1 file types only (`.pdf`, `.md`, `.txt`)
- No authentication, rate limiting, or multi-user support

---

## Locked Decision 1 — MCP SDK Tool Registration Pattern

The `mcp` Python SDK (1.27.0) is used in decorator mode via a `FastMCP` or
`Server` instance. The chosen pattern:

- A single MCP server instance is created in `server/app.py` at module level.
- Each of the 7 tools is registered using the SDK's tool decorator
  (`@mcp.tool()` or equivalent per the 1.27.0 API confirmed via Context7).
- Tool handlers in `tools.py` are plain Python functions; `app.py` imports and
  registers them — no business logic leaks into `app.py`.
- The MCP server instance is the **only** place where tool registration occurs.
  Handlers in `tools.py` must not contain any SDK-specific imports or decorators.

**Why:** Separating handler logic (tools.py) from registration (app.py) keeps
handlers unit-testable without importing the MCP SDK in tests. It also enforces
Article IV.1 — tools.py stays a thin delegate with no framework coupling.

---

## Locked Decision 2 — FastAPI App Structure

- `server/app.py` exports a factory function `create_app() -> tuple[FastAPI, FastMCP]`.
- A lifespan context manager (`@asynccontextmanager`) initializes shared objects
  (Settings, QdrantStore) at startup and yields an `AppContext` dataclass.
- FastMCP instance is created with the lifespan hook: `mcp = FastMCP("AgentRAG", lifespan=app_lifespan)`.
- Tool handlers are registered via `@mcp.tool()` decorator and return `dict[str, Any]`
  for JSON serialization (not dataclass instances — FastMCP requires dict).
- HTTP/SSE transport is mounted at `/sse` via `mcp.get_sse_app()`.
- Stdio transport bypasses FastAPI and is run via `mcp.run(transport="stdio")`.
- The FastAPI app has a single `/health` GET endpoint returning `{"status": "ok"}`
  for integration test readiness probing.

**Why:** Factory function pattern allows integration tests to instantiate the app
with isolated state. Lifespan hook ensures resources are initialized once and
shared across all tool calls. FastMCP 1.27.0 requires dict return values, not
dataclass instances.

---

## Locked Decision 3 — Error Serialization Contract

Tool handlers in `tools.py` follow this error contract, which tests must assert:

| Situation | Handler behaviour |
|---|---|
| File path does not exist (`ingest_file`) | Return `IngestResult(status="error", error="<message>")` — never raise |
| Directory path does not exist (`ingest_directory`) | Return `[]` (empty list) — never raise |
| Unknown `source_id` (`delete_source`) | Return `DeleteResult(status="not_found", chunks_deleted=0)` — never raise |
| Empty string query (`search_documents`) | Raise `ValueError("query must not be empty")` |
| Unknown `source_id` (`get_document`) | Raise `ValueError(f"source_id {source_id!r} not found")` |
| Empty filters dict (`search_by_metadata`) | Raise `ValueError("filters must not be empty")` |

**Serialization rule:** Tool handlers registered with `@mcp.tool()` must return
`dict[str, Any]`, not dataclass instances. Convert dataclass results to dict
using `{"field": result.field, ...}` pattern. FastMCP 1.27.0 requires dict
return values for JSON serialization.

**Why:** Distinguishing "surfaced error" (returns a typed result) from "contract
violation" (raises `ValueError`) matches the roadmap spec exactly and gives Claude
actionable information. `ValueError` propagates as an MCP error response the
Claude UI surfaces to the user; a typed result is returned as a tool output.

---

## Locked Decision 4 — Reranker Stub Contract

`src/agentrag/retrieval/reranker.py` in Phase 2 is a pure identity function:

```python
def rerank(results: list[SearchResult]) -> list[SearchResult]:
    """Return results unchanged; real re-ranking is Phase 5."""
    return results
```

Rules:
- No configuration parameters.
- No imports beyond `agentrag.types`.
- No tests required (testing identity is testing Python, not our logic).
- `mypy --strict` must pass (type annotations are required).
- This stub is replaced in Phase 5 when `AGENTRAG_RERANK=true` is implemented.

---

## Key Dependencies on Phase 1

Phase 2 builds directly on Phase 1 deliverables. The following are assumed
correct and must not be reimplemented:

| Phase 1 artifact | Used by Phase 2 |
|---|---|
| `store/qdrant.py` | `searcher.py` (query), `tools.py` (list, delete, get) |
| `ingestion/pipeline.py` | `tools.py` (ingest_file, ingest_directory) |
| `ingestion/embedder.py` | `searcher.py` (query embedding only) |
| `config.py` / `Settings` | `server/app.py` (lifespan init) |
| `types.py` | All new modules |

If any Phase 1 artifact is found to be broken during Phase 2 implementation,
stop and fix it first — do not work around it.

---

## Dependency Direction Constraints (Article IV)

New modules must respect the dependency graph:

```
server/app.py      → server/tools.py, config.py
server/tools.py    → ingestion/pipeline.py, retrieval/searcher.py, store/qdrant.py
retrieval/searcher.py → store/qdrant.py, ingestion/embedder.py
retrieval/reranker.py → agentrag.types (only)
```

Forbidden in Phase 2:
- `retrieval/` importing from `server/`
- `store/` importing from `retrieval/` or `ingestion/`
- `tools.py` containing any logic beyond input validation and delegation
