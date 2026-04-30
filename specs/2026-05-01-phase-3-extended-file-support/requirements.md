# Phase 3 — Extended File Support — Requirements

---

## What This Phase Delivers

Four new file types become ingestible: `.docx`, `.html`, `.py`, `.ipynb`.
The `ingest_directory` tool picks up all seven supported types recursively.
No new MCP tools. No new retrieval logic. No new external services.

---

## Files Changed

### `src/agentrag/ingestion/reader.py`

This is the only production file with new logic. It gains three private helper
functions — one for `.docx`, one for `.html`, one for `.ipynb` — and an extended
dispatch block that routes each new suffix to the right helper. The public function
`read_file` has an unchanged signature; callers see no difference.

`.py` files require no new helper. They are plain UTF-8 text and use the same
read path already in place for `.txt` and `.md` files. Only the supported suffix
set needs to include `.py`.

The module gains three new imports matching the three new helpers: the `json`
standard library module for notebook parsing, the `BeautifulSoup` class from
`beautifulsoup4` for HTML parsing, and the `Document` class from `python-docx`
for Word document parsing.

### `src/agentrag/server/tools.py`

The only change is the extension list inside `ingest_directory`. It grows from
three entries (`txt`, `md`, `pdf`) to seven by adding `docx`, `html`, `py`,
and `ipynb`. No new logic, no new imports, no change to the function signature.
The handler stays within the 15-line limit required by Article IV.1.

### Nothing else changes

`chunker.py`, `embedder.py`, `pipeline.py`, `store/qdrant.py`, `retrieval/`,
`config.py`, `types.py`, and all seven MCP tool handlers are untouched. The
pipeline already accepts any `RawDocument` — Phase 3's only job is to normalise
new file types into that one shape.

---

## New Dependencies

`python-docx 1.1.x` and `beautifulsoup4 4.12.x` are added as runtime dependencies
in `pyproject.toml`. They are runtime (not dev-only) because end users who ingest
`.docx` or `.html` files need them installed. `.ipynb` and `.py` parsing require
no new dependency.

`lxml` is not added. The `html.parser` backend bundled with Python's standard
library is used for BeautifulSoup — it handles clean HTML without a C-extension
dependency.

---

## Parsing Rules Per File Type

### `.docx`

The reader opens the file with `python-docx`, iterates over its paragraph
objects, and collects the text of each paragraph that is not blank. Paragraphs
consisting only of whitespace are skipped. Tables, images, and embedded objects
are not extracted in this phase. Paragraphs are joined with a single newline.

### `.html`

The reader parses the file with BeautifulSoup using the `html.parser` backend.
Before extracting any text, it removes the `nav`, `header`, `footer`, `script`,
and `style` elements and everything inside them. Only then is plain text
extracted, with a newline separator between elements. The `title` element is
left in because it provides useful retrieval context. Malformed HTML is tolerated
— `html.parser` does not raise on broken markup.

### `.py`

Raw UTF-8 source, read verbatim. No AST parsing, no comment stripping, no
docstring isolation. The chunker already handles token-level splitting, so
function names, docstrings, and comments all survive into the vector store as
searchable content.

### `.ipynb`

The reader parses the file as JSON. It iterates the notebook's cell list and
collects the source text from cells with type `code` or `markdown`. Cells with
type `raw` are skipped. Each cell's source is a list of strings in the notebook
format — these are concatenated directly to form the cell text. Cells are then
joined with a double newline to preserve block-level separation. Cell outputs
(stdout, stderr, display data, execution results) are not extracted; they are
runtime noise that degrades retrieval signal.

---

## Test Files

### `tests/unit/test_reader.py`

Four new test cases are added to the existing file, one per new type.

Each test uses a dedicated fixture file from `tests/fixtures/` and asserts the
shape and content of the returned `RawDocument`. The `.docx` test confirms that
empty paragraphs are filtered. The `.html` test uses sentinel strings to confirm
that boilerplate content is absent and body content is present. The `.py` test
confirms that the output is byte-identical to the input file. The `.ipynb` test
confirms that code and markdown cell text is present and raw cell text is absent.

### `tests/unit/test_tools.py`

One new test case is added. It creates a temporary directory with one file of
each of the seven supported extensions, mocks the ingest pipeline, and asserts
that `ingest_directory` processes all seven files with no type silently skipped.

### `tests/integration/test_extended_ingestion.py`

A new integration test file with five tests, each running the full pipeline
against a real embedded Qdrant instance. One test per new file type confirms
that chunks are stored and that the content is retrievable via `search_documents`.
The fifth test runs `ingest_directory` on the fixtures folder and confirms all
seven types are processed successfully in a single call.

---

## Test Fixtures

| File | Content | Purpose |
|------|---------|---------|
| `tests/fixtures/sample.docx` | Three paragraphs of prose, one blank paragraph | Verifies paragraph text extraction and empty-paragraph filtering |
| `tests/fixtures/sample.html` | Nav, header, footer, script, style with sentinel strings; main section with body content | Verifies boilerplate removal and body preservation |
| `tests/fixtures/sample.py` | At least three functions with docstrings, 30+ lines | Verifies raw-text pass-through; used in integration test for search |
| `tests/fixtures/sample.ipynb` | Two code cells, two markdown cells, one raw cell, each with unique sentinel strings | Verifies cell type filtering and source concatenation |

---

## Constraints

- `reader.py` must not import anything from `retrieval/`, `server/`, or `qdrant_client`
- `RawDocument` gains no new fields — the dataclass is unchanged
- The `make_source_id` function is unchanged; new file types use the same hash
- All code must pass `black`, `ruff`, and `mypy --strict` before committing

---

## Out of Scope

`.epub`, `.odt`, `.csv`, `.xlsx`, and URL ingestion are not in this phase.
Table extraction from `.docx`, cell output extraction from `.ipynb`, and
cross-encoder re-ranking are deferred to later phases.
