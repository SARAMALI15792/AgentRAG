# Phase 3 — Extended File Support — Requirements

## What Phase 3 Is

Add support for four new file types — `.docx`, `.html`, `.py`, `.ipynb` — to the
ingestion pipeline. Extend `ingest_directory` to recursively pick up all seven
supported types. No new retrieval logic, no new MCP tools, no new external services.

This phase touches **exactly two source files**:

| File | What changes |
|------|-------------|
| `src/agentrag/ingestion/reader.py` | 3 new private helpers + extended dispatch block |
| `src/agentrag/server/tools.py` | Glob list in `ingest_directory` extended from 3 to 7 |

Everything else — `chunker.py`, `embedder.py`, `pipeline.py`, `store/qdrant.py`,
`retrieval/`, `config.py`, `types.py` — is **untouched**.

---

## New Dependencies

| Library | Version pinned | Why runtime, not dev-only |
|---------|---------------|--------------------------|
| `python-docx` | `>=1.1,<1.2` | End users ingesting `.docx` files need it installed |
| `beautifulsoup4` | `>=4.12,<4.13` | End users ingesting `.html` files need it installed |

`.ipynb` parsing uses `json` (stdlib). `.py` reading uses `pathlib.Path.read_text`
(stdlib). Neither requires a new dependency.

`lxml` is **not** added. `html.parser` (stdlib) is the BeautifulSoup backend —
sufficient for clean HTML and avoids a C-extension dependency.

---

## What the Code Looks Like After Phase 3

### `reader.py` — new import block

```python
import json                          # new — ipynb parsing
from bs4 import BeautifulSoup        # new — html parsing
from docx import Document            # new — docx parsing
```

Existing imports (`hashlib`, `logging`, `pathlib.Path`, `pymupdf`, `agentrag.types`)
are unchanged.

### `reader.py` — three new private helpers

```python
def _read_docx(path: Path) -> str:
    """Extract paragraph text from a .docx file, skipping empty paragraphs."""
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _read_html(path: Path) -> str:
    """Extract body text from HTML after removing nav/header/footer/script/style."""
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def _read_ipynb(path: Path) -> str:
    """Concatenate source from code and markdown cells in a Jupyter notebook."""
    nb = json.loads(path.read_text(encoding="utf-8"))
    parts = [
        "".join(cell["source"])
        for cell in nb.get("cells", [])
        if cell.get("cell_type") in {"code", "markdown"}
    ]
    return "\n\n".join(parts)
```

### `reader.py` — updated dispatch in `read_file()`

The public function signature is **unchanged**: `read_file(path: Path) -> RawDocument`.
Only the internal suffix check and dispatch expand:

```python
# supported set grows from 3 to 7:
if suffix not in {".pdf", ".txt", ".md", ".docx", ".html", ".py", ".ipynb"}:
    raise ValueError(f"Unsupported file type: {suffix}")

# dispatch adds 3 new branches; .py reuses existing read_text path:
if suffix == ".pdf":
    text = _read_pdf(path)
elif suffix == ".docx":
    text = _read_docx(path)
elif suffix == ".html":
    text = _read_html(path)
elif suffix == ".ipynb":
    text = _read_ipynb(path)
else:                           # .txt, .md, .py
    text = path.read_text(encoding="utf-8")
```

### `tools.py` — updated glob list in `ingest_directory`

```python
# Before (Phase 2):
for ext in ["*.txt", "*.md", "*.pdf"]:

# After (Phase 3):
for ext in ["*.txt", "*.md", "*.pdf", "*.docx", "*.html", "*.py", "*.ipynb"]:
```

The stale inline comment `# Phase 2: only .txt, .md, .pdf` is removed (Article III.3).
No other change to `ingest_directory`. Handler stays ≤15 lines (Article IV.1).

---

## Per-Type Parsing Decisions

### `.docx`

- **Library:** `python-docx` — `Document(path)` opens the file.
- **What we extract:** `paragraph.text` for every paragraph where `text.strip() != ""`.
- **What we skip:** empty paragraphs (whitespace only), tables, images, embedded objects.
  Tables are structurally complex and out of scope for Phase 3.
- **Join:** paragraphs joined with `"\n"`.
- **Encoding:** handled internally by `python-docx` — no explicit encoding parameter needed.

### `.html`

- **Library:** `beautifulsoup4` with `html.parser` backend.
- **Boilerplate removal:** `.decompose()` called on every `nav`, `header`, `footer`,
  `script`, `style` tag. `decompose()` removes both the tag and its subtree from the
  parse tree — not just the tag wrapper. This happens before `get_text()`.
- **What we keep:** `<title>` stays (useful retrieval context). `<meta>` and `<link>`
  stay (they contribute no text to `get_text()` output anyway).
- **Text extraction:** `soup.get_text(separator="\n", strip=True)`.
- **Malformed HTML:** `html.parser` is lenient and will not raise on broken markup.

### `.py`

- **No new helper.** `.py` falls through to the existing `path.read_text(encoding="utf-8")`
  branch — the same path used for `.txt` and `.md`.
- **What we extract:** the raw source file verbatim. No AST parsing, no stripping.
- **Why raw source:** the chunker splits on token boundaries; function names, docstrings,
  and comments are all semantically valuable for retrieval without transformation.
- **Encoding:** UTF-8 enforced. Non-UTF-8 `.py` files raise `UnicodeDecodeError`,
  which `pipeline.py` catches and returns as `IngestResult(status="error")`.

### `.ipynb`

- **No library:** `json.loads(path.read_text(encoding="utf-8"))` — stdlib only.
- **Cell types included:** `"code"` and `"markdown"`. `"raw"` cells are skipped.
- **Source field:** each cell's `"source"` is a list of strings (notebook format v4).
  `"".join(cell["source"])` reconstructs the cell text with no extra separators.
- **Cell separator:** cells are joined with `"\n\n"` (double newline) so the chunker
  sees clean block boundaries between cells.
- **What we skip:** `cell["outputs"]` (stdout, stderr, display_data, execute_result).
  Outputs are runtime noise — they embed timestamps, tracebacks, and large data blobs
  that hurt retrieval signal.
- **Malformed notebook:** `json.JSONDecodeError` propagates to `pipeline.py` as
  `IngestResult(status="error")`.

---

## Data Flow After Phase 3

```
User file (.docx / .html / .py / .ipynb)
  │
  ▼
read_file(path)                        ← reader.py (extended)
  dispatches to _read_docx / _read_html / _read_ipynb / read_text
  returns RawDocument(source_id, filename, text, metadata={})
  │
  ▼                                    ← unchanged below this line
chunker.py  →  embedder.py  →  store/qdrant.py
```

The chunker, embedder, and store see `RawDocument` — they are completely unaware of
the file type. Phase 3's entire job is to normalise new file types into that one type.

---

## What Phase 3 Does NOT Change

- `RawDocument` dataclass — no new fields
- `Chunk`, `EmbeddedChunk`, `SearchResult` — untouched
- `pipeline.py` — untouched; already handles any `RawDocument`
- Chunking parameters (512 tokens / 64 overlap) — unchanged
- Embedding model — unchanged
- Qdrant collection schema — unchanged
- All 7 existing MCP tools — unchanged
- `config.py` — no new env vars

---

## Out of Scope

- `.epub`, `.odt`, `.csv`, `.xlsx` — not in roadmap; do not add
- URL/web ingestion — explicitly a non-goal in `specs/mission.md`
- Table extraction from `.docx` — deferred; adds complexity for limited gain
- Cell outputs in `.ipynb` — runtime noise that degrades retrieval quality
- Cross-encoder re-ranking — Phase 5
- Query decomposition / Gemini integration — Phase 4
