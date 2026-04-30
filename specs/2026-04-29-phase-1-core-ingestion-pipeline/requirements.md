# Phase 1 — Core Ingestion Pipeline: Requirements

Full scope, all decisions (made and open), and context for a cold session.
A future Claude with no memory of this project can read this file and know
exactly what Phase 1 is, what has already been decided, and what is still open.

---

## Scope

**In scope:**

- Read local files (`.txt`, `.md`, `.pdf`)
- Chunk text using a sliding token window
- Embed chunks locally using `sentence-transformers`
- Persist embedded chunks to Qdrant (in-process embedded mode)
- Delete all chunks for a given source from the store
- List all ingested sources
- CLI commands: `agentrag ingest <file>` and `agentrag list`
- Full unit and integration test suite
- CI pipeline (GitHub Actions) on `main`
- Pre-commit hook enforcing lint + type checks

**Out of scope (not until Phase 2 or later):**

- MCP server and all 7 MCP tools — Phase 2
- Retrieval / semantic search — Phase 2
- Agentic query decomposition or evaluation — Phase 3
- `.docx`, `.html`, `.py`, `.ipynb` support — Phase 4
- Re-ranking — Phase 5
- PyPI distribution — Phase 6
- URL ingestion, multi-user support, cloud backend — non-goals, not in any phase
- Any Gemini/google-genai calls — not until Phase 4

---

## Already-Made Decisions

These are locked. Changing any requires amending `specs/tech-stack.md` with
user approval before touching code.

### Embedding model

`all-MiniLM-L6-v2` via `sentence-transformers 3.x`. Output dimension: 384.
Fast, small (22M parameters), runs on CPU without GPU. No API key required.
Model is downloaded on first run to the `sentence-transformers` cache
(`~/.cache/huggingface/`). Unit tests mock the model — no download in CI.

### Chunk size and overlap

- `chunk_size = 512` tokens
- `overlap = 64` tokens (sliding window)
- Token counting uses `AutoTokenizer.from_pretrained(settings.embed_model)`
  from the `transformers` library (transitive dependency of `sentence-transformers`).
  Character counts and `tiktoken` are **prohibited** — chunk boundaries must
  align exactly with the embedding model's vocabulary.

### Vector dimension

`384`. Must match `all-MiniLM-L6-v2` output and the Qdrant collection
`vector_size`. If the model is ever changed, both `AGENTRAG_VECTOR_DIM` and
the Qdrant collection must be updated together (the collection must be
recreated from scratch — Qdrant does not support in-place dimension changes).

### Vector store

Qdrant embedded client (`qdrant-client 1.17.x`). Runs in-process — no Docker,
no network, no server process. Data persists to `~/.agentrag/qdrant/` (or
the configured `data_dir`). The embedded client is imported **only** in
`src/agentrag/store/qdrant.py`. No other module may import `qdrant_client`.

### Distance metric

Cosine similarity. This is the appropriate metric for normalized
sentence-transformers embeddings and is set at collection creation time.

### Deduplication strategy

`upsert` in `store/qdrant.py` deletes all existing points for a `source_id`
before inserting new ones. This guarantees idempotent re-ingestion: calling
`ingest` on the same file twice produces the same `chunk_count` and does not
accumulate duplicate points.

### Source ID computation

```python
import hashlib
from pathlib import Path

def make_source_id(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]
```

- Always uses the **resolved absolute path** (symlinks expanded, `..` collapsed)
- Truncated to 16 hex characters (64-bit collision resistance — sufficient for
  a single-user local store)
- Computed once in `reader.py`; used as the partition key throughout the system
- Changing this function invalidates all stored data

### PDF parsing

`pymupdf` (import name: `fitz`) version `1.24.x`. Fastest Python PDF parser,
handles complex layouts. Page text extracted via `page.get_text()` for each
page, joined with newlines.

### Settings

`pydantic-settings 2.x`. All runtime parameters live in `src/agentrag/config.py`
as a `Settings` class. No magic strings, no hardcoded paths, no `os.environ`
reads outside this file.

### Logging

Standard Python `logging` module only. `logging.basicConfig()` called only in
`cli.py`. All other modules use `logging.getLogger(__name__)`. `print()` is
forbidden in production code paths.

### CLI framework

`typer 0.12.x`. Two commands in Phase 1: `ingest` and `list`. A third command
(`serve`) is added in Phase 2 — do not scaffold it in Phase 1.

### Test runner

`pytest 8.x` only. The `unittest` module is not permitted anywhere in the
test suite. Async tests use `pytest-asyncio 1.3.x` with `asyncio_mode = "auto"`.

### Type checking

`mypy 1.10.x` with `--strict`. Every public function and method must be fully
annotated. `Any` is permitted only when unavoidable; every use must have an
inline comment explaining why. `# type: ignore` is forbidden without an inline
comment naming the exact mypy error and why suppression is the only option.

### Formatter and linter

- Black `25.x`, `line-length = 88`
- Ruff `0.15.x`, extends Black, standard rule categories
- Both run in the pre-commit hook and in CI

### Architecture constraint: separation of ingestion and retrieval

Ingestion logic (read, chunk, embed) lives exclusively in `src/agentrag/ingestion/`.
Retrieval logic lives exclusively in `src/agentrag/retrieval/`. Phase 1 does not
implement any retrieval logic — `retrieval/` exists only as an empty package
skeleton. No ingestion logic may appear in `retrieval/`, and vice versa.

### Architecture constraint: store access

`src/agentrag/store/qdrant.py` is the only file permitted to import `qdrant_client`.
All other modules interact with the store through its public interface.

### Architecture constraint: no business logic in CLI

`cli.py` is a thin shell. It calls into `pipeline.ingest()` and `store.list_sources()`.
It contains no chunking, embedding, or retrieval logic.

### Python version

3.12+. Enforced in `pyproject.toml` via `requires-python = ">=3.12"`.

---

## Open Decisions

These are not yet resolved and will surface during implementation.

### ~~Windows path handling in tests~~ — RESOLVED 2026-04-29

`path.resolve()` on Windows (`tmp_path`-based paths) produces correct
`source_id` values. No special handling needed. Integration tests confirmed
no collisions or mismatches.

### ~~PDF fixture generation~~ — RESOLVED 2026-04-29

`scripts/create_sample_pdf.py` committed to `scripts/` and marked
`# not run in CI`. Binary fixture committed as `tests/fixtures/sample.pdf`.
Regeneration process: run the script locally, commit the binary.

### Qdrant embedded mode persistence path

The `data_dir` from `Settings` is used as the Qdrant storage root. In unit
tests, `tmp_path`-based `Settings` isolates each test's Qdrant storage.
In integration tests, the embedded client writes to a `tmp_path`-scoped
directory per test session. This has not been tested across multiple concurrent
pytest workers — if `pytest-xdist` is introduced later, storage path isolation
will need review.

### Model download in integration tests

Integration tests call `pipeline.ingest()` with a real `SentenceTransformer`.
The `all-MiniLM-L6-v2` model (~22MB) is downloaded on first use to
`~/.cache/huggingface/`. CI must have internet access for the first run, or
the model must be pre-cached in the CI runner. Flag if the GitHub Actions
runner has download restrictions.

---

## Environment Variables

All variables are loaded via `pydantic-settings` from environment or `.env`.
`config.py` is the only file that reads them.

| Variable | Default | Used by |
|---|---|---|
| `AGENTRAG_DATA_DIR` | `~/.agentrag` | `config.py` → Qdrant storage root |
| `AGENTRAG_EMBED_MODEL` | `all-MiniLM-L6-v2` | `embedder.py`, `chunker.py` |
| `AGENTRAG_VECTOR_DIM` | `384` | `store/qdrant.py` collection init |
| `AGENTRAG_CHUNK_SIZE` | `512` | `chunker.py` |
| `AGENTRAG_CHUNK_OVERLAP` | `64` | `chunker.py` |
| `AGENTRAG_PORT` | `8000` | `config.py` only (not used until Phase 2) |
| `AGENTRAG_TRANSPORT` | `stdio` | `config.py` only (not used until Phase 2) |

Variables prefixed with Phase 3+ (`AGENTRAG_OLLAMA_URL`, `AGENTRAG_OLLAMA_MODEL`,
`AGENTRAG_QUERY_EXPAND`, `AGENTRAG_RERANK`) must be defined in `config.py` with
their defaults so the settings model is complete — but the code paths that use
them are not implemented until the relevant phase.

---

## Phase 1 Dependencies

### Runtime

| Package | Version |
|---|---|
| `mcp` | ≥1.0, pin exact |
| `fastapi` | 0.136.x |
| `uvicorn` | 0.46.x |
| `qdrant-client` | 1.17.x |
| `sentence-transformers` | 3.x |
| `pymupdf` | 1.24.x |
| `pydantic-settings` | 2.x |
| `typer` | 0.12.x |
| `transformers` | (transitive via sentence-transformers — pin if needed) |

### Dev

| Package | Version |
|---|---|
| `black` | 25.x |
| `ruff` | 0.15.x |
| `mypy` | 1.10.x |
| `pytest` | 8.x |
| `pytest-asyncio` | 1.3.x |
| `pytest-cov` | 5.x |
| `httpx` | 0.27.x |
| `hatchling` | latest |

`mcp`, `fastapi`, and `uvicorn` are listed as runtime deps now so `pyproject.toml`
is complete for Phase 2 without requiring a dependency update mid-phase. They are
not called in Phase 1 implementation code.
