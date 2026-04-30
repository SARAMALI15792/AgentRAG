# Phase 3 — Extended File Support — Requirements

## Scope

Extend the ingestion pipeline to support four new file types: `.docx`, `.html`,
`.py`, and `.ipynb`. Extend `ingest_directory` to include all seven types in its
recursive glob. No new retrieval logic, no new MCP tools, no new external services.

This phase touches exactly two source files:
- `src/agentrag/ingestion/reader.py` — new type branches
- `src/agentrag/server/tools.py` — extended glob list in `ingest_directory`

All other modules (`chunker.py`, `embedder.py`, `pipeline.py`, `store/qdrant.py`,
`retrieval/`) are **unchanged** by this phase.

---

## New Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `python-docx` | `>=1.1,<1.2` | Parse `.docx` files; iterate paragraphs |
| `beautifulsoup4` | `>=4.12,<4.13` | Parse `.html` files; strip tags and boilerplate |

Both are runtime dependencies (not dev-only): users ingesting `.docx` or `.html`
files need them installed. Add to `[project.dependencies]` in `pyproject.toml`.

`lxml` is NOT added as a parser backend. `html.parser` (stdlib) is used for
`BeautifulSoup` to avoid an additional C-extension dependency.

`.ipynb` is parsed with `json` (stdlib) — no additional dependency required.
`.py` is read with `pathlib.Path.read_text` — no additional dependency required.

---

## Per-Type Parsing Decisions

### `.docx` — `python-docx`

- Entry point: `Document(path)` from `docx` package.
- Text extraction: iterate `doc.paragraphs`, take `paragraph.text`, join with `\n`.
- Empty paragraphs (where `paragraph.text.strip() == ""`) are skipped to avoid
  excessive whitespace in the resulting `RawDocument.text`.
- Tables are **not** extracted in Phase 3. Table text is out of scope.
- Images and embedded objects are **not** extracted. Plain text only.
- Encoding: `python-docx` handles encoding internally; no explicit encoding needed.

### `.html` — `beautifulsoup4`

- Parser: `html.parser` (stdlib, no additional dep, sufficient for clean HTML).
- Boilerplate removal: call `.decompose()` on every tag of type
  `nav`, `header`, `footer`, `script`, `style` before extracting text.
  This removes both the tag and its contents from the parse tree.
- Text extraction: `soup.get_text(separator="\n", strip=True)` after decompose.
- The resulting text must contain no raw `<` or `>` characters.
- Malformed HTML is tolerated — `html.parser` is lenient by default.
- No special handling for `<meta>`, `<link>`, `<title>` — these are left in.
  Title text is useful context for retrieval.

### `.py` — stdlib only

- Extraction: `path.read_text(encoding="utf-8")`.
- No AST parsing, no docstring extraction, no comment stripping. Raw source only.
- Rationale: the chunker already splits on token boundaries; semantic structure of
  Python source (indentation, function names) is preserved verbatim and aids retrieval.
- Encoding: UTF-8 enforced. Files with non-UTF-8 encoding will raise `UnicodeDecodeError`,
  which propagates to `pipeline.py`'s error handler as an ingest error (status "error").

### `.ipynb` — stdlib JSON

- Extraction: `json.loads(path.read_text(encoding="utf-8"))`.
- Cell types to include: `"code"` and `"markdown"`. `"raw"` cells are skipped.
- Source field: each cell has a `"source"` field that is either a string or a list
  of strings. Join with `""` (no separator) to reconstruct the cell source, then
  join cells with `"\n\n"` (double newline) to separate logical blocks.
- Output cells (`cell["outputs"]`) are **not** extracted. stdout/stderr/display_data
  output is out of scope for Phase 3.
- Kernel metadata and notebook metadata are ignored.
- Malformed notebook JSON raises `json.JSONDecodeError`, propagated as ingest error.

---

## `ingest_directory` Extension

Current glob list: `["*.txt", "*.md", "*.pdf"]`

Phase 3 glob list: `["*.txt", "*.md", "*.pdf", "*.docx", "*.html", "*.py", "*.ipynb"]`

The `ingest_directory` handler remains a thin delegate (≤15 lines, Article IV.1).
The glob extension is the only change. No new logic is introduced.

Files with unsupported extensions continue to be silently skipped (logged at DEBUG).

---

## Architecture Constraints (from Article IV)

- All new code lives in `src/agentrag/ingestion/reader.py`. No other source file
  gains new logic from this phase.
- `reader.py` must not import `qdrant_client`, `sentence_transformers`, or anything
  from `retrieval/` or `server/`.
- The `make_source_id` contract is unchanged. New file types use the same hash function.
- `RawDocument` is unchanged. No new fields are added to domain types in Phase 3.

---

## Test Fixture Specifications

| Fixture | Min content | Key assertions |
|---------|-------------|----------------|
| `tests/fixtures/sample.docx` | ≥3 paragraphs, ≥50 words | `text` non-empty, no raw tags |
| `tests/fixtures/sample.html` | `<nav>`, `<header>`, `<footer>`, `<script>`, `<style>`, `<main>` with ≥3 `<p>` | boilerplate absent, body present |
| `tests/fixtures/sample.py` | ≥3 functions with docstrings, ≥30 lines | `text` == raw source |
| `tests/fixtures/sample.ipynb` | 2 code cells + 2 markdown cells | both cell types present in `text` |

All fixture files are committed to the repository as binary/text artifacts.
`sample.docx` is a binary file; all others are text.

---

## Out of Scope for Phase 3

- `.epub`, `.odt`, `.csv`, `.xlsx` — not in roadmap; do not add.
- URL/web ingestion — explicitly excluded from mission non-goals.
- Table extraction from `.docx` — deferred; tables are structurally complex and
  low-priority for the target audience.
- Cell outputs in `.ipynb` — stdout/stderr/image outputs are noise for semantic search.
- Cross-encoder re-ranking — Phase 5 scope.
- Query decomposition / Gemini — Phase 4 scope.
