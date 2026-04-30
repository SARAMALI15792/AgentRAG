# Phase 3B — Plan

> Extended Ingestion & Agentic Retrieval

---

## Group A — Infrastructure & Dependencies

**Goal:** Reader plugin registry and all new dependencies installed.

| # | Task | Files | TDD |
|---|------|-------|-----|
| A1 | Add office deps (`openpyxl`, `python-pptx`) to `pyproject.toml` `[office]` group | `pyproject.toml` | — |
| A2 | Add ebook deps (`ebooklib`, `mobi`) to `pyproject.toml` `[ebooks]` group | `pyproject.toml` | — |
| A3 | Add `PyYAML` to runtime deps | `pyproject.toml` | — |
| A4 | Add web deps (`pysrt`, `webvtt-py`) to `pyproject.toml` `[web]` group; promote `httpx` to optional `[web]` runtime dep | `pyproject.toml` | — |
| A5 | Create `[all]` optional group combining office + ebooks + web | `pyproject.toml` | — |
| A6 | Run `uv lock` — commit updated `uv.lock` | `uv.lock` | — |
| A7 | Write failing tests for reader registry (register, lookup, unknown ext error) | `tests/unit/test_reader_registry.py` | RED |
| A8 | Implement reader registry | `src/agentrag/ingestion/reader_registry.py` | GREEN |
| A9 | Refactor `reader.py` to dispatch via registry instead of if/elif chain | `src/agentrag/ingestion/reader.py` | GREEN |
| A10 | Register all existing Tier 1 readers (txt, md, pdf, docx, html, py, ipynb) | `reader.py` / `reader_registry.py` | GREEN |

**Checkpoint A:** `uv run pytest tests/unit/test_reader_registry.py` green. All existing readers still pass via registry dispatch.

---

## Group B — File Readers (Office, eBook, Structured)

**Goal:** 9 new file types readable and registered.

| # | Task | Files | TDD |
|---|------|-------|-----|
| B1 | Context7 lookups: `openpyxl`, `python-pptx`, `ebooklib`, `PyYAML` | — | — |
| B2 | Create test fixtures: `sample.xlsx`, `sample.pptx`, `sample.csv` | `tests/fixtures/` | — |
| B3 | Write failing tests for `.xlsx`, `.pptx`, `.csv` readers | `tests/unit/test_reader.py` | RED |
| B4 | Implement office readers + register | `src/agentrag/ingestion/readers/office.py` | GREEN |
| B5 | Create test fixtures: `sample.epub`, `sample.json`, `sample.yaml`, `sample.xml`, `sample.toml` | `tests/fixtures/` | — |
| B6 | Write failing tests for `.epub`, `.mobi` readers | `tests/unit/test_reader.py` | RED |
| B7 | Implement ebook readers + register | `src/agentrag/ingestion/readers/ebooks.py` | GREEN |
| B8 | Write failing tests for `.json`, `.yaml`, `.xml`, `.toml` readers | `tests/unit/test_reader.py` | RED |
| B9 | Implement structured data readers + register | `src/agentrag/ingestion/readers/structured.py` | GREEN |

**Checkpoint B:** `uv run pytest tests/unit/test_reader.py` green for all 9 new file types.

---

## Group C — Web, Subtitle, and Email Readers

**Goal:** URL ingestion, subtitle parsing, email parsing — all registered.

| # | Task | Files | TDD |
|---|------|-------|-----|
| C1 | Create test fixtures: `sample.srt`, `sample.eml` | `tests/fixtures/` | — |
| C2 | Write failing tests for URL reader (mock httpx responses) | `tests/unit/test_url_reader.py` | RED |
| C3 | Implement URL reader + register | `src/agentrag/ingestion/readers/web.py` | GREEN |
| C4 | Write failing tests for `.srt`, `.vtt` readers | `tests/unit/test_reader.py` | RED |
| C5 | Implement subtitle readers + register | `src/agentrag/ingestion/readers/media.py` | GREEN |
| C6 | Write failing tests for `.eml`, `.mbox` readers | `tests/unit/test_reader.py` | RED |
| C7 | Implement email readers + register | `src/agentrag/ingestion/readers/email.py` | GREEN |
| C8 | Extend `ingest_directory` glob list (or use `supported_extensions()`) | `server/tools.py` | GREEN |
| C9 | Add `ingest_url` MCP tool handler + register in `app.py` | `server/tools.py`, `server/app.py` | GREEN |

**Checkpoint C:** All reader unit tests green. `ingest_url` tool registered and unit-tested.

---

## Group D — Integration Tests (File Ingestion)

**Goal:** End-to-end proof that every new file type ingests through the full pipeline into real Qdrant.

| # | Task | Files | TDD |
|---|------|-------|-----|
| D1 | Write integration tests: ingest one fixture per new type, verify `chunk_count > 0` | `tests/integration/test_extended_ingestion_3b.py` | GREEN |
| D2 | Write integration test: `ingest_directory` on mixed directory → all types ingested | `tests/integration/test_extended_ingestion_3b.py` | GREEN |

**Checkpoint D:** `uv run pytest tests/integration/test_extended_ingestion_3b.py` green.

---

## Group E — Agentic Retrieval Types & Modules

**Goal:** Query decomposition, multi-query search, chunk evaluation — all working with Gemini graceful degradation.

| # | Task | Files | TDD |
|---|------|-------|-----|
| E1 | Context7 lookup: `google-genai` SDK (`Client`, `generate_content`, structured JSON output) | — | — |
| E2 | Add `QueryPlan`, `ChunkScore`, `EvaluationReport` dataclasses | `src/agentrag/types.py` | — |
| E3 | Write failing tests for query planner (mock Gemini client) | `tests/unit/test_query_planner.py` | RED |
| E4 | Implement query planner with Gemini + graceful degrade | `src/agentrag/retrieval/query_planner.py` | GREEN |
| E5 | Write failing tests for chunk evaluator (mock Gemini client) | `tests/unit/test_evaluator.py` | RED |
| E6 | Implement chunk evaluator with Gemini + graceful degrade | `src/agentrag/retrieval/evaluator.py` | GREEN |

**Checkpoint E:** `uv run pytest tests/unit/test_query_planner.py tests/unit/test_evaluator.py` green. Graceful degrade paths tested.

---

## Group F — Agentic MCP Tools & Integration

**Goal:** Three new MCP tools (`plan_query`, `search_multi`, `evaluate_chunks`) registered and integration-tested.

| # | Task | Files | TDD |
|---|------|-------|-----|
| F1 | Write failing tests for agentic tool handlers (planner, evaluator, searcher mocked) | `tests/unit/test_agentic_tools.py` | RED |
| F2 | Implement `plan_query`, `search_multi`, `evaluate_chunks` handlers (≤15 lines each) | `src/agentrag/server/tools.py` | GREEN |
| F3 | Register all 3 new tools in `app.py` | `src/agentrag/server/app.py` | GREEN |
| F4 | Write integration tests: full agentic loop (plan → search_multi → evaluate → re-search) | `tests/integration/test_agentic_retrieval.py` | GREEN |
| F5 | Write integration test: all 3 tools work with `AGENTRAG_GOOGLE_API_KEY` absent | `tests/integration/test_agentic_retrieval.py` | GREEN |

**Checkpoint F:** All agentic tools registered and green. Graceful degrade confirmed in integration.

---

## Group G — Exit Gate

| # | Task | Files |
|---|------|-------|
| G1 | Write `scripts/verify_phase3b.sh` | `scripts/verify_phase3b.sh` |
| G2 | Run full verification: `black --check`, `ruff check`, `mypy --strict`, `pytest`, phase-specific smoke tests | — |
| G3 | CodeRabbit review on all changed files | — |
| G4 | Final commit + push + PR to `main` | — |
