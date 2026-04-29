# Phase 1 — Core Ingestion Pipeline: Execution Plan

Task groups mirror the roadmap step numbering. Each group breaks the step into
the minimum executable sub-steps following strict TDD order: test file written
and confirmed **failing** before any implementation file is created.

---

## Group 1 — Skeleton and Fixtures

_No tests required. No logic exists yet to test._

1. Create full directory skeleton — all packages first so imports resolve:
   - `src/agentrag/__init__.py`
   - `src/agentrag/ingestion/__init__.py`
   - `src/agentrag/retrieval/__init__.py`
   - `src/agentrag/store/__init__.py`
   - `src/agentrag/server/__init__.py`
   - `tests/__init__.py`
   - `tests/unit/__init__.py`
   - `tests/integration/__init__.py`
   - `tests/fixtures/` (empty directory placeholder)
2. Write `tests/conftest.py` — shared fixtures used by every unit test:
   - `tmp_path`-based `Settings` with isolated `data_dir` (no collision across tests)
   - mock `SentenceTransformer` returning deterministic 384-dim zero vectors
   - mock `QdrantClient`
   - `sample_chunks` list of three `EmbeddedChunk` instances
3. Write `.git/hooks/pre-commit`:
   - Runs `black --check . && ruff check . && mypy --strict src/`
   - Exits non-zero on any failure, blocking the commit
   - Mark executable (`chmod +x`)
4. Write `tests/fixtures/sample.txt` — plain text, ≥ 600 words
5. Write `tests/fixtures/sample.pdf` — single-page PDF fixture (binary, committed once, never regenerated automatically)
6. Write `pyproject.toml`:
   - All Phase 1 runtime and dev dependencies (see requirements.md)
   - Entry point: `agentrag = agentrag.cli:app`
   - `[tool.black]` line-length = 88
   - `[tool.ruff]` extends black, standard rule categories
   - `[tool.mypy]` strict = true
   - `[tool.pytest.ini_options]` asyncio_mode = "auto", testpaths = ["tests"]
   - `[tool.coverage.run]` source = ["src"]

**Acceptance:** `pip install -e ".[dev]"` exits 0. `pytest --collect-only` collects zero tests without import errors.

---

## Group 2 — Domain Types

_No tests — pure dataclasses, zero business logic._

1. Write `src/agentrag/types.py` — all 8 cross-module dataclasses:
   `RawDocument`, `Chunk`, `EmbeddedChunk`, `SearchResult`, `SourceInfo`,
   `IngestResult`, `DeleteResult`, `DocumentContent`
2. Run `mypy --strict src/` — confirm clean
3. Run `black . && ruff check .` — confirm clean

**Acceptance:** `mypy --strict src/` exits 0. `from agentrag.types import RawDocument` in a Python shell imports without error.

---

## Group 2.5 — Context7 Batch Lookup

_Run once, before any implementation code in Groups 3–11._

Query Context7 for all 6 Phase 1 libraries in a single batch session. Do not
query mid-implementation. Cache all results in context before Group 3 begins.

| Library | Topic |
|---------|-------|
| `qdrant-client` | embedded client init, upsert, query, delete, filters |
| `sentence-transformers` | SentenceTransformer, batch encode, model loading |
| `pydantic-settings` | Settings, env var binding, field defaults |
| `pymupdf` | fitz.open, page.get_text, document iteration |
| `typer` | app, command, argument, option |
| `transformers` | AutoTokenizer, from_pretrained, encode, token counting |

---

## Group 3 — Config

1. Write `tests/unit/test_config.py` with 4 test cases:
   - Default values load without env vars set
   - Env var `AGENTRAG_DATA_DIR` overrides `data_dir`
   - `data_dir` is created on disk when it does not exist
   - `vector_dim` defaults to `384`
2. Run `pytest tests/unit/test_config.py` → **confirm red** (ImportError or AttributeError expected)
3. Write `src/agentrag/config.py` — `Settings` via `pydantic-settings`, auto-creates `data_dir` on instantiation
4. Run `pytest tests/unit/test_config.py` → **confirm green**
5. Run `black . && ruff check . && mypy --strict src/` → fix all issues until clean

**Acceptance:** `pytest tests/unit/test_config.py` exits 0. `mypy --strict src/` exits 0.

---

## Group 4 — Vector Store

_Parallel-eligible: can run concurrently with Groups 5, 6, 7 once Group 2 is done._

1. Write `tests/unit/test_store.py` with 6 test cases:
   - `upsert` then `query` returns the inserted chunks
   - `upsert` same `source_id` twice → chunk count unchanged (dedup)
   - `delete(source_id)` removes all points for that source
   - `list_sources()` returns correct `SourceInfo` after upsert
   - `query` on empty collection returns `[]`, does not raise
   - `list_sources()` on empty store returns `[]`
2. Run `pytest tests/unit/test_store.py` → **confirm red**
3. Write `src/agentrag/store/qdrant.py`:
   - Qdrant embedded client; collection created on init
   - `vector_size = settings.vector_dim`, distance = Cosine
   - `upsert`: deletes all existing points for `source_id` before inserting
   - Only file in the codebase permitted to import `qdrant_client`
4. Run `pytest tests/unit/test_store.py` → **confirm green**
5. Run lint gate → fix all issues

**Acceptance:** `pytest tests/unit/test_store.py` exits 0. Grep confirms `qdrant_client` imported only in `store/qdrant.py`.

---

## Group 5 — Reader

_Parallel-eligible: can run concurrently with Groups 4, 6, 7 once Group 2 is done._

1. Write `tests/unit/test_reader.py` with 7 test cases:
   - `.txt` path → `RawDocument` with correct `text` and `filename`
   - `.md` path → `RawDocument`
   - `.pdf` path → `RawDocument` with non-empty `text`
   - `source_id` is a 16-char hex string (SHA-256 of resolved path, truncated)
   - Non-existent path raises `FileNotFoundError`
   - Unsupported extension raises `ValueError`
   - Empty file raises `ValueError`
2. Run `pytest tests/unit/test_reader.py` → **confirm red**
3. Write `src/agentrag/ingestion/reader.py`:
   - `source_id = hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]`
   - `.pdf` via pymupdf/fitz; `.md` and `.txt` via plain `read_text()`
4. Run `pytest tests/unit/test_reader.py` → **confirm green**
5. Run lint gate → fix all issues

**Acceptance:** `pytest tests/unit/test_reader.py` exits 0. `mypy --strict src/` clean.

---

## Group 6 — Chunker

_Parallel-eligible: can run concurrently with Groups 4, 5, 7 once Group 2 is done._

1. Write `tests/unit/test_chunker.py` with 5 test cases:
   - Long text → multiple chunks, each ≤ `chunk_size` tokens
   - Consecutive chunks overlap by `overlap` tokens
   - Text shorter than `chunk_size` → exactly one chunk
   - `chunk_id` format is `"{source_id}_{index}"`
   - `index` is zero-based and contiguous
2. Run `pytest tests/unit/test_chunker.py` → **confirm red**
3. Write `src/agentrag/ingestion/chunker.py`:
   - `AutoTokenizer.from_pretrained(settings.embed_model)` for all token counting
   - Sliding window: `chunk_size = 512` tokens, `overlap = 64` tokens
4. Run `pytest tests/unit/test_chunker.py` → **confirm green**
5. Run lint gate → fix all issues

**Acceptance:** `pytest tests/unit/test_chunker.py` exits 0. No character-count or tiktoken usage anywhere in `chunker.py`.

---

## Group 7 — Embedder

_Parallel-eligible: can run concurrently with Groups 4, 5, 6 once Group 2 is done._

1. Write `tests/unit/test_embedder.py` with 4 test cases (SentenceTransformer mocked):
   - Output list length equals input chunk list length
   - Each vector has length `settings.vector_dim`
   - `chunk_id`, `source_id`, and `text` are preserved in output
   - `metadata` dict is passed through unchanged
2. Run `pytest tests/unit/test_embedder.py` → **confirm red**
3. Write `src/agentrag/ingestion/embedder.py`:
   - Loads `SentenceTransformer(settings.embed_model)`
   - Batch-encodes all chunk texts in one call
   - Returns `list[EmbeddedChunk]`
4. Run `pytest tests/unit/test_embedder.py` → **confirm green**
5. Run lint gate → fix all issues

**Acceptance:** `pytest tests/unit/test_embedder.py` exits 0. No model download occurs in unit tests (mock is used).

---

## Group 8 — Pipeline

_Sequential: must wait for all of Groups 4, 5, 6, 7 to complete._

1. Write `tests/unit/test_pipeline.py` with 4 test cases (store + embedder mocked):
   - Success: returns `IngestResult(status="ok", chunk_count > 0)`
   - Non-existent file: returns `IngestResult(status="error")`, does not raise
   - Unsupported extension: returns `IngestResult(status="error")`
   - Embedder failure: returns `IngestResult(status="error")`
2. Run `pytest tests/unit/test_pipeline.py` → **confirm red**
3. Write `src/agentrag/ingestion/pipeline.py`:
   - `ingest(path: Path, metadata: dict[str, Any]) -> IngestResult`
   - Orchestrates reader → chunker → embedder → store
   - All exceptions caught; surfaced as `IngestResult(status="error", error=str(e))`
   - Never raises
4. Run `pytest tests/unit/test_pipeline.py` → **confirm green**
5. Run lint gate → fix all issues

**Acceptance:** `pytest tests/unit/test_pipeline.py` exits 0. `pipeline.py` contains no bare `raise` statements.

---

## Group 9 — CLI and Exit Gate Script

1. Write `src/agentrag/cli.py`:
   - `agentrag ingest <file>` — calls `pipeline.ingest`, prints `IngestResult`
   - `agentrag list` — calls `store.list_sources()`, prints source table
   - Only file that calls `logging.basicConfig()`
2. Write `scripts/verify_phase1.sh`:
   ```bash
   pytest && \
   mypy --strict src/ && \
   agentrag ingest tests/fixtures/sample.txt && \
   agentrag list
   ```
   Mark executable. Exit code 0 = phase exit condition met.
3. Run `mypy --strict src/` → confirm clean across all modules
4. Run `agentrag ingest tests/fixtures/sample.txt` → smoke test
5. Run `agentrag list` → verify ingested source appears

**Acceptance:** Both CLI commands execute without error. `verify_phase1.sh` exits 0.

---

## Group 10 — CI

1. Write `.github/workflows/ci.yml`:
   - Triggered on every push to `main`
   - Steps: checkout → set up Python 3.12 → `pip install -e ".[dev]"` → `black --check .` → `ruff check .` → `mypy --strict src/` → `pytest --tb=short`
   - Fails fast on first error
2. Push branch to `main` (or open PR) → verify GitHub Actions run turns green

**Acceptance:** CI pipeline runs all 6 steps with zero failures. No skipped steps.

---

## Group 11 — Integration Tests

1. Write `tests/integration/test_pipeline.py` with 4 test cases (real Qdrant embedded, real files):
   - Ingest `tests/fixtures/sample.txt` → `chunk_count > 0`
   - Ingest `tests/fixtures/sample.pdf` → `chunk_count > 0`
   - Re-ingest `sample.txt` → `chunk_count` identical to first ingest (dedup)
   - `list_sources()` returns the ingested source after ingest
2. Run `pytest tests/integration/` → **confirm green**

**Acceptance:** `pytest tests/integration/test_pipeline.py` exits 0. No mocks used — real Qdrant embedded instance, real fixture files.

---

## Phase Exit Gate

```bash
scripts/verify_phase1.sh
```

Exit code 0 = Phase 1 complete. CI is green on `main`. `mypy --strict` passes.
No manual verification steps remain. Phase 2 may begin.
