# Phase 3B — Validation Criteria

> Extended Ingestion & Agentic Retrieval

---

## Gate Structure

Each task group has an intermediate validation gate. The phase is complete
only when all gates pass AND the final exit gate script exits 0.

### Skill Invocation Verification

At each gate, verify the following skills were invoked before the code
they govern was written. A gate fails if a skill was skipped.

| Gate | Required Skill Invocations |
|------|---------------------------|
| A | `python-testing-patterns` (registry tests), `pydantic` (config changes) |
| B | `python-testing-patterns` (parameterized reader tests) |
| C | `python-testing-patterns` (URL/subtitle/email tests), `fastapi-python` (tool handlers) |
| D | `python-testing-patterns` (integration test patterns) |
| E | `pydantic` (domain types), `machine-learning` (embedding context), `python-testing-patterns` (mock patterns) |
| F | `fastapi-python` (tool registration), `python-testing-patterns` (integration tests) |

---

## Gate A — Infrastructure & Registry

- [ ] `openpyxl`, `python-pptx`, `ebooklib`, `mobi`, `PyYAML`, `pysrt`,
      `webvtt-py`, `httpx`, `google-genai` all resolvable in `uv.lock`
- [ ] `uv pip install -e ".[dev,office,ebooks,web]"` succeeds without errors
- [ ] `uv pip install -e ".[all]"` succeeds without errors
- [ ] `reader_registry.register()` maps extensions to callables
- [ ] `reader_registry.get_reader()` returns correct reader for known extensions
- [ ] `reader_registry.get_reader()` raises `ValueError` for unknown extensions
- [ ] `reader_registry.supported_extensions()` returns complete set
- [ ] All 7 Tier 1 readers (txt, md, pdf, docx, html, py, ipynb) still pass
      through registry dispatch — no regressions
- [ ] `uv run pytest tests/unit/test_reader_registry.py` exits 0

---

## Gate B — Office, eBook, and Structured Readers

- [ ] `.xlsx` reader extracts text from all sheets, preserves headers
- [ ] `.pptx` reader extracts text from all slides including speaker notes
- [ ] `.csv` reader extracts header + all data rows
- [ ] `.epub` reader extracts text from all XHTML chapters
- [ ] `.mobi` reader extracts text (or raises actionable `ImportError`)
- [ ] `.json` reader produces pretty-printed text
- [ ] `.yaml` reader loads safely (`safe_load`) and dumps as text
- [ ] `.xml` reader extracts all text content, strips tags
- [ ] `.toml` reader loads and dumps as text
- [ ] All readers raise `ValueError` on empty extraction
- [ ] All optional-dep readers raise `ImportError` with `pip install agentrag[group]` message
- [ ] `uv run pytest tests/unit/test_reader.py` exits 0 for all 9 new types

---

## Gate C — Web, Subtitle, and Email Readers

- [ ] URL reader fetches HTML, extracts text via BeautifulSoup
- [ ] URL reader handles timeout, 4xx, 5xx with actionable errors
- [ ] `.srt` reader extracts timestamped text segments
- [ ] `.vtt` reader extracts cue text
- [ ] `.eml` reader parses headers + body text
- [ ] `.mbox` reader iterates messages and extracts text
- [ ] `ingest_url` MCP tool registered and callable
- [ ] `ingest_directory` picks up all new extensions
- [ ] `uv run pytest tests/unit/test_url_reader.py` exits 0
- [ ] `uv run pytest tests/unit/test_reader.py` exits 0 for subtitle + email types

---

## Gate D — File Ingestion Integration

- [ ] Each new file type ingested into real Qdrant → `chunk_count > 0`
- [ ] `ingest_directory` on a mixed directory ingests all supported types
- [ ] No file type causes a hang or unhandled exception
- [ ] `uv run pytest tests/integration/test_extended_ingestion_3b.py` exits 0

---

## Gate E — Agentic Retrieval Modules

- [ ] `QueryPlan`, `ChunkScore`, `EvaluationReport` dataclasses exist in `types.py`
- [ ] `query_planner.plan()` with Gemini → returns `QueryPlan` with ≥1 sub-queries
- [ ] `query_planner.plan()` without API key → returns single-query plan (no raise)
- [ ] `query_planner.plan()` with bad API response → returns single-query plan
- [ ] `evaluator.evaluate()` with Gemini → returns `EvaluationReport` with scores in [0, 1]
- [ ] `evaluator.evaluate()` without API key → scores 0.5, `sufficient=True`
- [ ] `evaluator.evaluate()` with empty chunk list → `sufficient=False`
- [ ] `uv run pytest tests/unit/test_query_planner.py tests/unit/test_evaluator.py` exits 0

---

## Gate F — Agentic MCP Tools & Integration

- [ ] `plan_query` tool registered in MCP server, delegates to `query_planner`
- [ ] `search_multi` tool merges results from N queries, deduplicates by `chunk_id`
- [ ] `search_multi` with empty queries → `ValueError`
- [ ] `evaluate_chunks` tool delegates to `evaluator`, returns `EvaluationReport`
- [ ] All 3 tool handlers ≤15 lines of business logic
- [ ] Full agentic loop integration test: plan → search_multi → evaluate → re-search
- [ ] All 3 tools work when `AGENTRAG_GOOGLE_API_KEY` is absent (graceful degrade)
- [ ] `uv run pytest tests/unit/test_agentic_tools.py` exits 0
- [ ] `uv run pytest tests/integration/test_agentic_retrieval.py` exits 0

---

## Final Exit Gate — `scripts/verify_phase3b.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Phase 3B Exit Gate ==="

echo "[1/5] Black..."
uv run black --check .

echo "[2/5] Ruff..."
uv run ruff check .

echo "[3/5] Mypy..."
uv run mypy --strict src/

echo "[4/5] Pytest..."
uv run pytest --tb=short -q

echo "[5/5] Phase-specific smoke tests..."
# Ingest one file of each new type via CLI
uv run agentrag ingest tests/fixtures/sample.xlsx
uv run agentrag ingest tests/fixtures/sample.pptx
uv run agentrag ingest tests/fixtures/sample.csv
uv run agentrag ingest tests/fixtures/sample.epub
uv run agentrag ingest tests/fixtures/sample.json
uv run agentrag ingest tests/fixtures/sample.yaml
uv run agentrag ingest tests/fixtures/sample.xml
uv run agentrag ingest tests/fixtures/sample.toml
uv run agentrag ingest tests/fixtures/sample.srt
uv run agentrag ingest tests/fixtures/sample.eml

echo "=== Phase 3B Exit Gate: PASSED ==="
```

- [ ] `scripts/verify_phase3b.sh` exits 0
- [ ] CodeRabbit review completed, all blocking issues resolved
- [ ] All changes committed and pushed to `phase/3b-extended-ingestion-agentic`
- [ ] PR opened to `main`

---

## Phase Complete When

All seven gates (A through G) pass. The verify script is the final arbiter.
No human judgment substitutes for a green exit gate.
