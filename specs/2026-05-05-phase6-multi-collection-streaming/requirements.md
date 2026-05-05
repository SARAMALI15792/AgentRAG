# Phase 6 — Multi-Collection & Streaming Retrieval: Requirements

## Scope

Add workspace isolation via named Qdrant collections and an async streaming
retrieval path. Users can maintain separate knowledge bases per project, client,
or topic. Claude receives results via the `search_stream` tool, with automatic
fallback to batch mode if the MCP SDK does not support streaming.

No new external dependencies. All capabilities use existing `qdrant-client`
and stdlib `asyncio`.

---

## Spec Discrepancy Notice

`tech-stack.md` and `architecture.md` both label streaming retrieval as Phase 7.
`roadmap.md` places it in Phase 6. This document treats `roadmap.md` as
authoritative (it defines scope by phase). The Phase 7 labels in
`tech-stack.md` and `architecture.md` are stale and should be updated to
reflect Phase 6 in a follow-up amendment.

---

## Decisions

### switch_collection — Session-Scoped Only

**Decision:** `switch_collection` mutates `settings.collection` in-process.
State resets to `AGENTRAG_COLLECTION` (default: `"documents"`) on every
server restart. No state is written to disk.

**Rationale:** Stateless design eliminates file I/O and race conditions.
Users who want a persistent default collection set `AGENTRAG_COLLECTION`
in their `.env`. Session switching is a convenience for within-session
workspace hopping, not a persistent preference.

**Contract:** `switch_collection(name)` validates the collection exists in
Qdrant before mutating settings. Raises `ValueError` with actionable message
if the collection is unknown: `"Collection 'X' does not exist. Create it
first with: create_collection('X')"`.

---

### Streaming Retrieval — Ship with Graceful Fallback

**Decision:** `search_stream` is implemented and registered as an MCP tool.
If the MCP SDK does not support `AsyncGenerator` return types, the handler
collects the generator into a list and returns batch results. The tool ships
regardless.

**Rationale:** The streaming async generator in `retrieval/streaming.py` is
correct and testable regardless of MCP SDK support. Shipping the tool now
keeps the interface stable. When the MCP SDK adds streaming, only the handler
return type needs updating — no architectural change.

---

### Collection Creation — Idempotent

**Decision:** `create_collection(name)` is idempotent. If the collection
already exists, it returns a confirmation string without raising. No error.

**Rationale:** Claude may call `create_collection` before `switch_collection`
as a safety step. Raising on duplicate would require Claude to call
`list_collections` first — unnecessary round-trip.

---

### Store Layer — Dynamic Collection Name

**Decision:** Replace every hardcoded `_COLLECTION` reference in
`store/qdrant.py` with `settings.collection`. All store operations (`upsert`,
`query`, `delete`, `get_full_document`, `list_sources`, `search_by_metadata`)
read the active collection from the live `settings` instance at call time.

**Rationale:** This is the minimal change that enables multi-collection
without restructuring the store interface. The `QdrantStore` does not take
a collection argument per-call — it reads from settings, which the server
mutates on `switch_collection`. This keeps tool handlers thin (Article IV.1).

---

## New MCP Tools

### `list_collections`

```
Purpose : List all named Qdrant collections.
Input   : (none)
Output  : list[str] — collection names, alphabetically sorted
Notes   : Always returns at least the default collection if any data has been
          ingested. Returns empty list if Qdrant has no collections yet.
```

### `create_collection`

```
Purpose : Create a new named collection for workspace isolation.
Input   : name (str) — collection name, alphanumeric + underscores only
Output  : str — confirmation: "Collection '{name}' created."
          If already exists: "Collection '{name}' already exists."
Errors  : ValueError if name contains invalid characters
Notes   : Idempotent. Vector parameters (dimension, distance metric) are
          inherited from settings (AGENTRAG_VECTOR_DIM, cosine distance).
```

### `switch_collection`

```
Purpose : Set the active collection for all subsequent operations this session.
Input   : name (str)
Output  : str — confirmation: "Active collection set to '{name}'."
Errors  : ValueError if collection does not exist
Notes   : Session-scoped only. Resets to AGENTRAG_COLLECTION on restart.
          All subsequent calls to ingest_file, search_documents, list_sources,
          etc. operate on the newly active collection.
```

### `search_stream`

```
Purpose : Streaming semantic search — results yielded as they score.
Input   : query (str), top_k (int, default 5)
Output  : list[SearchResult] (batch fallback) or AsyncIterator[SearchResult]
          (if MCP SDK supports streaming)
Errors  : ValueError if query is empty string
Notes   : Internally uses retrieval/streaming.py async generator.
          Falls back to batch if SDK does not support async return types.
          Result set and ordering are identical to search_documents.
```

---

## Unchanged Behaviour

All Phase 1–5 tools (`ingest_file`, `ingest_directory`, `search_documents`,
`search_by_metadata`, `list_sources`, `get_document`, `delete_source`,
`plan_query`, `search_multi`, `evaluate_chunks`) continue to operate exactly
as before against whatever `settings.collection` is currently set to. No
interface changes. No breaking changes.

---

## New Files

| Path | Purpose |
|------|---------|
| `src/agentrag/retrieval/streaming.py` | Async generator yielding `SearchResult` |
| `tests/unit/test_streaming.py` | Unit tests for the streaming generator |
| `tests/integration/test_multi_collection.py` | Integration: collection isolation |
| `tests/integration/test_streaming_integration.py` | Integration: stream vs batch parity |
| `scripts/verify_phase6.sh` | Phase 6 exit gate |

---

## Modified Files

| Path | Change |
|------|--------|
| `src/agentrag/store/qdrant.py` | Replace `_COLLECTION` with `settings.collection`; add `create_collection`, `list_collections` |
| `src/agentrag/server/tools.py` | Add `list_collections`, `create_collection`, `switch_collection`, `search_stream` handlers |
| `src/agentrag/server/app.py` | Register 4 new tools; expose settings instance to tool context |
| `tests/unit/test_store.py` | Extend: two-collection isolation, new store methods |
| `tests/unit/test_tools.py` | Extend: 4 new tool handler tests |

---

## Out of Scope

- Persistent collection switching (disk-backed active collection state).
- Collection deletion (no `delete_collection` tool — avoid accidental data loss).
- Per-collection embedding model configuration (all collections share `settings.embed_model`).
- Cross-collection search (search operates on the active collection only).
- Merging or copying collections.
- Any cloud sync functionality (Phase 7).
- Any new ingestion features.
