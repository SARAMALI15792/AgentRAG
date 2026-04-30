# Phase 3 — Extended File Support — Execution Plan

Execution order is strict. Each step must complete before the next begins.
Every implementation step is preceded by a failing test that specifies what
the code must do. Tests prove the implementation — but the implementation is
the deliverable.

---

## Step 0 — Context7 Lookups _(before any code)_

Look up current API docs for the two new libraries before writing a single line.

- [ ] Resolve Context7 library ID for `python-docx`
- [ ] Query `python-docx` docs — topic: `"Document paragraph iteration text extraction"`
- [ ] Resolve Context7 library ID for `beautifulsoup4`
- [ ] Query `beautifulsoup4` docs — topic: `"decompose get_text tag removal html.parser"`

---

## Step 1 — Dependencies

Add two new runtime dependencies and lock them.

**What changes in `pyproject.toml`:**
```toml
[project.dependencies]
# existing entries ...
"python-docx>=1.1,<1.2",
"beautifulsoup4>=4.12,<4.13",
```

**Steps:**
- [ ] Obtain user approval for both additions (one AskUserQuestion call)
- [ ] Add `python-docx>=1.1,<1.2` to `[project.dependencies]` in `pyproject.toml`
- [ ] Add `beautifulsoup4>=4.12,<4.13` to `[project.dependencies]` in `pyproject.toml`
- [ ] Run `uv lock` — verify `uv.lock` updates cleanly
- [ ] Update `specs/tech-stack.md` runtime table: promote both from "Phase 3 planned" to active rows
- [ ] Commit: `chore: add python-docx and beautifulsoup4 runtime dependencies`

---

## Step 2 — New Reader Helpers in `reader.py`

### What we're building

`src/agentrag/ingestion/reader.py` gets three new private helper functions and
an extended dispatch block. The public function `read_file(path: Path) -> RawDocument`
signature is **unchanged** — callers see no difference.

**New imports added at top of `reader.py`:**
```python
import json
from bs4 import BeautifulSoup
from docx import Document
```

**Three new private helpers:**

```python
def _read_docx(path: Path) -> str:
    """Extract paragraph text from a .docx file."""
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def _read_html(path: Path) -> str:
    """Extract body text from HTML, stripping nav/header/footer/script/style."""
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)

def _read_ipynb(path: Path) -> str:
    """Extract source text from code and markdown cells in a Jupyter notebook."""
    nb = json.loads(path.read_text(encoding="utf-8"))
    parts = [
        "".join(cell["source"])
        for cell in nb.get("cells", [])
        if cell.get("cell_type") in {"code", "markdown"}
    ]
    return "\n\n".join(parts)
```

**Extended dispatch in `read_file()`:**

The existing suffix check expands from `{".pdf", ".txt", ".md"}` to include
the four new types. `.py` needs no new helper — it reuses the existing
`path.read_text(encoding="utf-8")` branch:

```python
# Before (Phase 2):
if suffix not in {".pdf", ".txt", ".md"}:
    raise ValueError(...)
if suffix == ".pdf":
    text = _read_pdf(path)
else:
    text = path.read_text(encoding="utf-8")

# After (Phase 3):
if suffix not in {".pdf", ".txt", ".md", ".docx", ".html", ".py", ".ipynb"}:
    raise ValueError(...)
if suffix == ".pdf":
    text = _read_pdf(path)
elif suffix == ".docx":
    text = _read_docx(path)
elif suffix == ".html":
    text = _read_html(path)
elif suffix == ".ipynb":
    text = _read_ipynb(path)
else:  # .txt, .md, .py — raw text
    text = path.read_text(encoding="utf-8")
```

### 2a — `.docx` (TDD sequence)

- [ ] Write `test_read_docx` in `tests/unit/test_reader.py` — assert `RawDocument.text`
      is non-empty, `filename` matches, `source_id` is 16-char hex
- [ ] Run → confirm **red** (`.docx` branch doesn't exist yet)
- [ ] Create `tests/fixtures/sample.docx` programmatically using `python-docx`:
      3 paragraphs of real prose, one empty paragraph to verify filtering
- [ ] Implement `_read_docx()` and add `.docx` branch to `read_file()`
- [ ] Run → confirm **green**

### 2b — `.html` (TDD sequence)

- [ ] Write `test_read_html` in `tests/unit/test_reader.py` — assert no `<`/`>` chars,
      nav/script/style sentinel strings absent, body content present
- [ ] Run → confirm **red**
- [ ] Create `tests/fixtures/sample.html`: contains `<nav>NAVTEXT</nav>`,
      `<script>SCRIPTTEXT</script>`, `<style>STYLETEXT</style>`, `<header>HEADERTEXT</header>`,
      `<footer>FOOTERTEXT</footer>`, and `<main><p>BODYTEXT paragraph one.</p></main>`
      (sentinel strings make assertions unambiguous)
- [ ] Implement `_read_html()` and add `.html` branch
- [ ] Run → confirm **green**

### 2c — `.py` (TDD sequence)

- [ ] Write `test_read_py` in `tests/unit/test_reader.py` — assert `text` equals
      exact raw source of fixture (no transformation whatsoever)
- [ ] Run → confirm **red** (`.py` not in supported set yet)
- [ ] Create `tests/fixtures/sample.py`: 3 functions with docstrings, ≥30 lines
- [ ] Add `.py` to the supported suffix set in `read_file()` — no new helper needed,
      falls through to the existing `path.read_text(encoding="utf-8")` branch
- [ ] Run → confirm **green**

### 2d — `.ipynb` (TDD sequence)

- [ ] Write `test_read_ipynb` in `tests/unit/test_reader.py` — assert known code cell
      string present in output, known markdown cell string present in output,
      `cell_type=="raw"` content absent
- [ ] Run → confirm **red**
- [ ] Create `tests/fixtures/sample.ipynb`: valid JSON, 2 code cells + 2 markdown cells
      + 1 raw cell with a unique sentinel string (to assert exclusion)
- [ ] Implement `_read_ipynb()` and add `.ipynb` branch
- [ ] Run → confirm **green**

### 2e — Full reader suite

- [ ] `uv run pytest tests/unit/test_reader.py` → all tests green (old + 4 new)
- [ ] `uv run black . && uv run ruff check . && uv run mypy --strict src/` → zero errors
- [ ] Commit: `feat: extend reader with docx, html, py, ipynb support`

---

## Step 3 — Extend `ingest_directory` in `tools.py`

### What we're building

One line changes in `src/agentrag/server/tools.py`. The `ingest_directory` handler's
glob list expands from 3 to 7 extensions. No new logic, no new functions.

```python
# Before (Phase 2):
for ext in ["*.txt", "*.md", "*.pdf"]:

# After (Phase 3):
for ext in ["*.txt", "*.md", "*.pdf", "*.docx", "*.html", "*.py", "*.ipynb"]:
```

The handler stays ≤15 lines (Article IV.1). The stale comment `# Phase 2: only ...`
is removed — no task-tracking comments in source (Article III.3).

### TDD sequence

- [ ] Write `test_ingest_directory_all_types` in `tests/unit/test_tools.py`:
      mock pipeline + a temp directory containing one file of each of 7 extensions,
      assert `ingest()` called exactly 7 times (once per file, none skipped)
- [ ] Run → confirm **red** (only 3 types currently globbed)
- [ ] Update the glob list in `ingest_directory`; remove stale Phase 2 comment
- [ ] Run → confirm **green**
- [ ] `uv run black . && uv run ruff check . && uv run mypy --strict src/` → zero errors
- [ ] Commit: `feat: extend ingest_directory to support all 7 file types`

---

## Step 4 — Integration Tests

### What we're building

`tests/integration/test_extended_ingestion.py` — 5 tests against a real embedded
Qdrant instance. These tests verify the full pipeline (reader → chunker → embedder →
store) for each new type, not just the reader in isolation.

**Test: `test_ingest_docx`**
- Ingest `tests/fixtures/sample.docx` via `ingest(path, settings)`
- Assert `IngestResult.status == "ok"`, `chunk_count > 0`

**Test: `test_ingest_html`**
- Ingest `tests/fixtures/sample.html`
- Assert `chunk_count > 0`
- Call `search_documents("BODYTEXT")` → ≥1 result
- Assert no `SearchResult.text` contains "NAVTEXT", "SCRIPTTEXT", or "STYLETEXT"
  (proves boilerplate was stripped before chunking, not just in unit test)

**Test: `test_ingest_py`**
- Ingest `tests/fixtures/sample.py`
- Assert `chunk_count > 0`
- Assert at least one chunk contains a known function name from the fixture

**Test: `test_ingest_ipynb`**
- Ingest `tests/fixtures/sample.ipynb`
- Assert `chunk_count > 0`
- Assert at least one chunk contains the known markdown cell sentinel string

**Test: `test_ingest_directory_mixed`**
- Call `ingest_directory` on `tests/fixtures/` (contains all 7 types)
- Assert 7 `IngestResult` entries returned, all `status == "ok"`, all `chunk_count > 0`

### Steps

- [ ] Create `tests/integration/test_extended_ingestion.py` with the 5 tests above
- [ ] `uv run pytest tests/integration/test_extended_ingestion.py` → all green
- [ ] `uv run pytest --tb=short` (full suite) → zero failures
- [ ] `uv run mypy --strict src/` → zero errors
- [ ] Invoke `coderabbit:code-review` on all changed files; resolve blocking issues
- [ ] Commit: `test: integration tests for extended file ingestion`

---

## Step 5 — Exit Gate Script

### What we're building

`scripts/verify_phase3.sh` — a runnable, deterministic exit gate. Same pattern
as `scripts/verify_phase1.sh`. Exits 0 only when all checks pass.

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Phase 3 exit gate ==="

echo "--- pytest ---"
uv run pytest --tb=short

echo "--- mypy ---"
uv run mypy --strict src/

echo "--- CLI smoke: all 7 file types ---"
for f in tests/fixtures/sample.txt \
          tests/fixtures/sample.md  \
          tests/fixtures/sample.pdf \
          tests/fixtures/sample.docx \
          tests/fixtures/sample.html \
          tests/fixtures/sample.py   \
          tests/fixtures/sample.ipynb; do
    agentrag ingest "$f"
    echo "  ingested: $f"
done

echo "=== Phase 3 exit gate PASSED ==="
```

### Steps

- [ ] Create `scripts/verify_phase3.sh` with the above content
- [ ] `bash scripts/verify_phase3.sh` → exits 0
- [ ] Commit: `chore: add verify_phase3.sh exit gate script`

---

## Step 6 — PR

- [ ] `git push origin phase/3-extended-file-support`
- [ ] Open PR: `phase/3-extended-file-support` → `main`
- [ ] PR title: `Phase 3: Extended File Support (.docx, .html, .py, .ipynb)`
- [ ] CI green on branch before merge
- [ ] After merge: update `specs/roadmap.md` Phase 3 entry to `COMPLETE`
