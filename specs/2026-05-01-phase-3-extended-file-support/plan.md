# Phase 3 — Extended File Support — Execution Plan

Execution order is strict. Each step must be complete and green before the next begins.
TDD rule: test written and confirmed **red** before any implementation file is touched.

---

## Step 0 — Context7 Lookups _(before any code)_

- [ ] Resolve Context7 library ID for `python-docx`
- [ ] Query `python-docx` docs: `Document`, paragraph iteration, `paragraph.text` API
- [ ] Resolve Context7 library ID for `beautifulsoup4`
- [ ] Query `beautifulsoup4` docs: `BeautifulSoup`, `decompose()`, `get_text(separator=)` API

---

## Step 1 — Dependencies

- [ ] Obtain user approval to add `python-docx 1.1.x` to `[project.dependencies]`
- [ ] Obtain user approval to add `beautifulsoup4 4.12.x` to `[project.dependencies]`
- [ ] Add `python-docx>=1.1,<1.2` to `pyproject.toml` runtime deps
- [ ] Add `beautifulsoup4>=4.12,<4.13` to `pyproject.toml` runtime deps
- [ ] Run `uv lock` — verify `uv.lock` updates cleanly, no conflicts
- [ ] Update `specs/tech-stack.md`: move both libs from "Phase 3 planned" notes to active runtime table row
- [ ] Commit: `chore: add python-docx and beautifulsoup4 runtime dependencies`

---

## Step 2 — New Readers _(TDD per file type)_

### 2a — `.docx`

- [ ] `tests/unit/test_reader.py`: add `test_read_docx`
      — `.docx` path → `RawDocument`
      — `text` is non-empty string
      — `filename` matches the fixture filename
      — `source_id` is a 16-char hex string
- [ ] Run `uv run pytest tests/unit/test_reader.py::test_read_docx` → confirm **red**
- [ ] Create `tests/fixtures/sample.docx` via `python-docx`: ≥3 paragraphs, ≥50 words
- [ ] `src/agentrag/ingestion/reader.py`: add `.docx` branch
      — `Document(path)`, iterate `doc.paragraphs`, join `p.text` with `\n`
      — skip empty paragraphs
- [ ] Run `uv run pytest tests/unit/test_reader.py::test_read_docx` → **green**

### 2b — `.html`

- [ ] `tests/unit/test_reader.py`: add `test_read_html`
      — `.html` path → `RawDocument`
      — `text` contains no raw `<` or `>` characters
      — boilerplate tag text (nav/header/footer/script/style contents) absent from `text`
      — body content text present in `text`
- [ ] Run `uv run pytest tests/unit/test_reader.py::test_read_html` → confirm **red**
- [ ] Create `tests/fixtures/sample.html`: includes `<nav>`, `<header>`, `<footer>`,
      `<script>`, `<style>`, and `<main>` with ≥3 paragraphs of body content
- [ ] `src/agentrag/ingestion/reader.py`: add `.html` branch
      — `BeautifulSoup(path.read_text(), "html.parser")`
      — `.decompose()` on each of: `nav`, `header`, `footer`, `script`, `style`
      — `soup.get_text(separator="\n", strip=True)`
- [ ] Run `uv run pytest tests/unit/test_reader.py::test_read_html` → **green**

### 2c — `.py`

- [ ] `tests/unit/test_reader.py`: add `test_read_py`
      — `.py` path → `RawDocument`
      — `text` equals raw file source (no transformation)
      — `filename` ends with `.py`
- [ ] Run `uv run pytest tests/unit/test_reader.py::test_read_py` → confirm **red**
- [ ] Create `tests/fixtures/sample.py`: ≥3 functions with docstrings, ≥30 lines
- [ ] `src/agentrag/ingestion/reader.py`: add `.py` branch
      — plain `path.read_text(encoding="utf-8")`
- [ ] Run `uv run pytest tests/unit/test_reader.py::test_read_py` → **green**

### 2d — `.ipynb`

- [ ] `tests/unit/test_reader.py`: add `test_read_ipynb`
      — `.ipynb` path → `RawDocument`
      — text contains source from both `code` and `markdown` cell types
      — text from a known markdown cell string is present in output
      — text from a known code cell string is present in output
- [ ] Run `uv run pytest tests/unit/test_reader.py::test_read_ipynb` → confirm **red**
- [ ] Create `tests/fixtures/sample.ipynb`: valid JSON with 2 code cells + 2 markdown cells,
      each cell `source` is a non-empty string
- [ ] `src/agentrag/ingestion/reader.py`: add `.ipynb` branch
      — `json.loads(path.read_text(encoding="utf-8"))`
      — extract `"".join(cell["source"])` for each cell where
        `cell["cell_type"] in {"code", "markdown"}`
      — join all cell texts with `"\n\n"`
- [ ] Run `uv run pytest tests/unit/test_reader.py::test_read_ipynb` → **green**

### 2e — Full reader suite

- [ ] Run `uv run pytest tests/unit/test_reader.py` → **all tests green**
- [ ] Run `uv run black . && uv run ruff check . && uv run mypy --strict src/` → zero errors
- [ ] Commit: `feat: extend reader with docx, html, py, ipynb support`

---

## Step 3 — Extend `ingest_directory`

- [ ] `tests/unit/test_tools.py`: add `test_ingest_directory_all_types`
      — mock pipeline, directory contains one file of each of 7 types
      — verify `pipeline.ingest_file` called once per file
      — verify no file is silently skipped
- [ ] Run `uv run pytest tests/unit/test_tools.py::test_ingest_directory_all_types` → confirm **red**
- [ ] `src/agentrag/server/tools.py`: extend `ingest_directory` glob list to include
      `*.docx`, `*.html`, `*.py`, `*.ipynb` alongside existing `*.txt`, `*.md`, `*.pdf`
- [ ] Run `uv run pytest tests/unit/test_tools.py` → **all tests green**
- [ ] Run `uv run black . && uv run ruff check . && uv run mypy --strict src/` → zero errors
- [ ] Commit: `feat: extend ingest_directory to support all 7 file types`

---

## Step 4 — Integration Tests

- [ ] Create `tests/integration/test_extended_ingestion.py` with 5 tests:

  - `test_ingest_docx`
    — real embedded Qdrant, ingest `tests/fixtures/sample.docx`
    — `IngestResult.chunk_count > 0`, `status == "ok"`

  - `test_ingest_html`
    — real embedded Qdrant, ingest `tests/fixtures/sample.html`
    — `chunk_count > 0`
    — search results for body content text returns ≥1 result
    — nav/script/style text does NOT appear in any `SearchResult.text`

  - `test_ingest_py`
    — real embedded Qdrant, ingest `tests/fixtures/sample.py`
    — `chunk_count > 0`, function names from fixture present in at least one chunk

  - `test_ingest_ipynb`
    — real embedded Qdrant, ingest `tests/fixtures/sample.ipynb`
    — `chunk_count > 0`
    — known markdown cell string present in at least one `SearchResult.text`

  - `test_ingest_directory_mixed`
    — real embedded Qdrant, `ingest_directory` on `tests/fixtures/`
    — returns 7 `IngestResult` entries (one per type)
    — every result has `status == "ok"` and `chunk_count > 0`

- [ ] Run `uv run pytest tests/integration/test_extended_ingestion.py` → **all green**
- [ ] Run full suite `uv run pytest --tb=short` → zero failures
- [ ] Run `uv run mypy --strict src/` → zero errors
- [ ] Invoke `coderabbit:code-review` on all new/changed files; resolve all blocking issues
- [ ] Commit: `test: integration tests for extended file ingestion`

---

## Step 5 — Exit Gate Script

- [ ] Create `scripts/verify_phase3.sh`:
      - `set -e`
      - `uv run pytest --tb=short`
      - `uv run mypy --strict src/`
      - ingest each of 7 fixture files via `agentrag ingest` CLI, assert exit 0
- [ ] Run `bash scripts/verify_phase3.sh` → exit 0
- [ ] Commit: `chore: add verify_phase3.sh exit gate script`

---

## Step 6 — PR

- [ ] `git push origin phase/3-extended-file-support`
- [ ] Open PR: `phase/3-extended-file-support` → `main`
- [ ] Title: `Phase 3: Extended File Support (.docx, .html, .py, .ipynb)`
- [ ] CI green on PR branch before merge
