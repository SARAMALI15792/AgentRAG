# Phase 2 — MCP Server — Validation

A phase is complete only when every gate below is checked. Gates are ordered:
automated first, manual last. A failure at any gate blocks progression.

---

## Gate 1 — Automated: Full Test Suite Green

```bash
uv run pytest --tb=short
```

Expected outcome:
- Zero failures
- Zero errors
- All unit tests in `tests/unit/` pass (including new `test_searcher.py` and `test_tools.py`)
- All integration tests in `tests/integration/` pass (including new `test_server.py`)
- Skips permitted only with documented, approved reason

---

## Gate 2 — Automated: Type Checker Clean

```bash
uv run mypy --strict src/
```

Expected outcome: zero errors, zero warnings.

---

## Gate 3 — Automated: Formatter and Linter Clean

```bash
uv run black --check .
uv run ruff check .
```

Expected outcome: both exit 0 with no output.

---

## Gate 4 — Manual: Claude Desktop Stdio Verification

Start the server in stdio mode:

```bash
agentrag serve --transport stdio --data-dir ~/.agentrag
```

Add to Claude Desktop config and connect. Run each item below in order. A
checkmark means the tool returned the expected response.

### Precondition

- [ ] Ingest a test file so the store is non-empty:
      Call `ingest_file` with an existing `.txt` or `.pdf` path.
      Expect: `IngestResult(status="ok", chunk_count > 0)`.

---

### Tool 1 — `ingest_file`

| # | Input | Expected response |
|---|-------|-------------------|
| 1a | Existing `.txt` file path | `IngestResult(status="ok", chunk_count ≥ 1)` |
| 1b | Existing `.pdf` file path | `IngestResult(status="ok", chunk_count ≥ 1)` |
| 1c | Non-existent path | `IngestResult(status="error", error contains "not found" or similar)` |
| 1d | Re-ingest same file (idempotent) | `IngestResult(status="ok")` — no duplicate chunks |

### Tool 2 — `ingest_directory`

| # | Input | Expected response |
|---|-------|-------------------|
| 2a | Directory containing `.txt` and `.pdf` files | `list[IngestResult]` — one entry per file, all `status="ok"` |
| 2b | Directory with mixed types (`.docx` present) | `.docx` skipped silently; only `.txt`/`.md`/`.pdf` ingested |

### Tool 3 — `search_documents`

| # | Input | Expected response |
|---|-------|-------------------|
| 3a | Relevant query string, `top_k=3` | `list[SearchResult]`, length ≤ 3, scores descending |
| 3b | Query with no matches | Empty `list[SearchResult]` — no exception |
| 3c | Empty string query | MCP error response (Claude surfaces "query must not be empty") |

### Tool 4 — `search_by_metadata`

| # | Input | Expected response |
|---|-------|-------------------|
| 4a | `{"filename": "<ingested filename>"}` | `list[SourceInfo]` containing that source |
| 4b | `{"filename": "nonexistent.txt"}` | Empty `list[SourceInfo]` |
| 4c | Empty dict `{}` | MCP error response ("filters must not be empty") |

### Tool 5 — `list_sources`

| # | Input | Expected response |
|---|-------|-------------------|
| 5a | (none — no input) | `list[SourceInfo]` with at least the files ingested above |
| 5b | After fresh store (nothing ingested) | Empty `list[SourceInfo]` — no exception |

### Tool 6 — `get_document`

| # | Input | Expected response |
|---|-------|-------------------|
| 6a | `source_id` from a `list_sources` call | `DocumentContent` with non-empty `full_text` |
| 6b | Made-up `source_id` like `"deadbeef00000000"` | MCP error response ("source_id ... not found") |

### Tool 7 — `delete_source`

| # | Input | Expected response |
|---|-------|-------------------|
| 7a | `source_id` from a `list_sources` call | `DeleteResult(status="ok", chunks_deleted ≥ 1)` |
| 7b | Same `source_id` again (already deleted) | `DeleteResult(status="not_found", chunks_deleted=0)` |
| 7c | Made-up `source_id` | `DeleteResult(status="not_found", chunks_deleted=0)` |

---

## Gate 5 — Post-Delete Consistency Check

After running Tool 7 (delete), call `list_sources` again.

- [ ] The deleted source no longer appears in the list.
- [ ] Other sources (if any) are unaffected.

---

## Phase Exit Declaration

Phase 2 is complete and the PR may be merged when:

- [ ] Gate 1: `pytest` exits 0
- [ ] Gate 2: `mypy --strict src/` exits 0
- [ ] Gate 3: `black --check` and `ruff check` both exit 0
- [ ] Gate 4: All 7 tools verified manually in Claude Desktop — all rows checked
- [ ] Gate 5: Post-delete consistency confirmed
- [ ] `coderabbit:code-review` run; all blocking issues resolved (Article III.7)
- [ ] All changes committed and pushed to `phase/2-mcp-server` (Article IX.2)
- [ ] PR opened targeting `main`
