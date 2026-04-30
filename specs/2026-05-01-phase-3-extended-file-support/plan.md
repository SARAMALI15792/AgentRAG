# Phase 3 — Extended File Support — Execution Plan

Steps are strict-order. Each must be fully complete before the next begins.
For every implementation file written, a failing test is written first.

---

## Step 0 — Context7 Lookups

Before any code, look up current documentation for the two new libraries.

- [ ] Resolve and query `python-docx`: Document class, paragraph iteration, text extraction
- [ ] Resolve and query `beautifulsoup4`: tag decomposition, get_text, html.parser backend

---

## Step 1 — Dependencies

Add `python-docx 1.1.x` and `beautifulsoup4 4.12.x` to `pyproject.toml` runtime
dependencies. Run `uv lock`. Update `specs/tech-stack.md` to move both libraries
from "Phase 3 planned" notes into the active runtime table.

Commit: `chore: add python-docx and beautifulsoup4 runtime dependencies`

---

## Step 2 — New File Type Readers

The only implementation file that changes is `src/agentrag/ingestion/reader.py`.
The only test file that changes is `tests/unit/test_reader.py`.

For each file type below: write the test first, confirm it fails, create the
fixture, write the implementation, confirm the test passes.

---

### `.docx`

**Implementation — `reader.py`:**
Add a private helper that opens a `.docx` file, iterates its paragraphs, filters
out empty ones, and joins the remaining text. Add `.docx` to the supported suffix
set and route it to that helper in the dispatch block.

**Test — `test_reader.py`:**
Given a `.docx` fixture with known paragraphs and one intentionally empty paragraph,
assert the returned `RawDocument` has non-empty text, the correct filename, a
16-character hex source_id, and that the empty paragraph does not appear in the output.

**Fixture — `tests/fixtures/sample.docx`:**
Three paragraphs of real prose plus one blank paragraph. Created programmatically
using `python-docx` so it is a valid `.docx` binary.

---

### `.html`

**Implementation — `reader.py`:**
Add a private helper that parses the HTML, removes the `nav`, `header`, `footer`,
`script`, and `style` tags and all their contents, then extracts plain text.
Add `.html` to the supported suffix set and route it to that helper.

**Test — `test_reader.py`:**
Given an `.html` fixture containing known sentinel strings inside boilerplate tags
and separate known content in the body, assert the returned `RawDocument` text
contains the body content, does not contain any of the boilerplate sentinel strings,
and contains no raw angle-bracket characters.

**Fixture — `tests/fixtures/sample.html`:**
A complete HTML page with `<nav>`, `<header>`, `<footer>`, `<script>`, and `<style>`
elements each containing a unique sentinel string, and a `<main>` section with
at least three paragraphs of body content. Sentinel strings make the assertions
unambiguous and not dependent on counting characters.

---

### `.py`

**Implementation — `reader.py`:**
Add `.py` to the supported suffix set. No new helper is needed — `.py` files are
read as raw UTF-8 text, the same path already used for `.txt` and `.md`.

**Test — `test_reader.py`:**
Given a `.py` fixture, assert that `RawDocument.text` is byte-for-byte identical
to the raw file content — no transformation, stripping, or parsing applied.

**Fixture — `tests/fixtures/sample.py`:**
A plain Python source file with at least three functions, docstrings, and inline
comments totalling at least 30 lines. Serves as both the unit test fixture and
the integration test fixture.

---

### `.ipynb`

**Implementation — `reader.py`:**
Add a private helper that parses the notebook JSON, iterates its cells, collects
the source text from `code` and `markdown` cell types, skips `raw` cells entirely,
and joins the collected texts with a double newline separator. Add `.ipynb` to the
supported suffix set and route it to that helper.

**Test — `test_reader.py`:**
Given an `.ipynb` fixture with known text in code cells, markdown cells, and one
raw cell, assert that the code cell text is present in `RawDocument.text`, the
markdown cell text is present, and the raw cell text is absent.

**Fixture — `tests/fixtures/sample.ipynb`:**
A valid notebook JSON with two code cells, two markdown cells, and one raw cell.
Each cell contains a unique sentinel string to make assertions precise.

---

### Complete the reader step

After all four types pass individually, run the full `test_reader.py` suite to
confirm all old tests still pass alongside the four new ones. Run the full
formatter, linter, and type-checker. Commit: `feat: extend reader with docx, html, py, ipynb support`

---

## Step 3 — Extend `ingest_directory`

The only implementation change is in `src/agentrag/server/tools.py`: the glob
list inside `ingest_directory` grows from three extensions to seven. The handler
logic, line count, and public signature are unchanged.

**Test — `test_tools.py`:**
Add a test that creates a temporary directory with one file of each of the seven
supported extensions, calls `ingest_directory` with the pipeline mocked, and
asserts that `ingest` was called exactly once per file with no type silently skipped.
Confirm this test fails before the glob list is extended, then passes after.

Commit: `feat: extend ingest_directory to support all 7 file types`

---

## Step 4 — Integration Tests

Create `tests/integration/test_extended_ingestion.py`. These tests use a real
embedded Qdrant instance and exercise the full pipeline for each new type.

Five tests, one per concern:

- **`test_ingest_docx`** — ingest the `.docx` fixture end-to-end; assert the result
  status is `ok` and at least one chunk was stored.

- **`test_ingest_html`** — ingest the `.html` fixture end-to-end; assert chunks were
  stored; search for the body content and confirm it is retrievable; search for a
  boilerplate sentinel string and confirm no results are returned.

- **`test_ingest_py`** — ingest the `.py` fixture end-to-end; assert chunks were
  stored; confirm a known function name from the fixture is retrievable via search.

- **`test_ingest_ipynb`** — ingest the `.ipynb` fixture end-to-end; assert chunks
  were stored; confirm the markdown cell sentinel string is retrievable via search.

- **`test_ingest_directory_mixed`** — call `ingest_directory` on `tests/fixtures/`;
  assert seven results are returned, each with status `ok` and at least one chunk.

Run the full test suite after all five pass. Run the type-checker. Invoke
`coderabbit:code-review` on all changed files and resolve blocking issues.

Commit: `test: integration tests for extended file ingestion`

---

## Step 5 — Exit Gate Script

Create `scripts/verify_phase3.sh`. The script runs the full test suite, runs the
type-checker, and invokes `agentrag ingest` on each of the seven fixture files via
the CLI to confirm the end-to-end path works outside of pytest. Script exits 0
only if all steps pass. Run it and confirm exit 0.

Commit: `chore: add verify_phase3.sh exit gate script`

---

## Step 6 — PR

Push the branch, open a PR from `phase/3-extended-file-support` to `main`.
Wait for CI green. After merge, update `specs/roadmap.md` Phase 3 to `COMPLETE`.
