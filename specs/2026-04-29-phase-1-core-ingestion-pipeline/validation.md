# Phase 1 — Core Ingestion Pipeline: Validation Criteria

One acceptance condition per plan group, plus the binding phase exit gate.
A group is not complete until its acceptance condition is met — not before.
The phase is not complete until the Phase Exit Gate section passes in full.

---

## Group 1 — Skeleton and Fixtures

**Condition:** `pip install -e ".[dev]"` exits 0 with no dependency errors.
`pytest --collect-only` runs without import errors and collects zero tests
(no tests exist yet — zero is correct at this stage).

---

## Group 2 — Domain Types

**Condition:** `mypy --strict src/` exits 0 with zero errors or warnings.
Running `python -c "from agentrag.types import RawDocument, Chunk, EmbeddedChunk, SearchResult, SourceInfo, IngestResult, DeleteResult, DocumentContent"` produces no output and exits 0.

---

## Group 2.5 — Context7 Batch Lookup

**Condition:** Documentation retrieved for all 6 libraries listed in plan.md.
No implementation code written before this group completes.

---

## Group 3 — Config

**Condition:** `pytest tests/unit/test_config.py -v` exits 0 with all 4 tests
marked `PASSED`. `mypy --strict src/` exits 0. Running the following in a
clean shell with no env vars set produces a `Settings` object with
`data_dir = Path.home() / ".agentrag"` and `vector_dim = 384`:

```python
from agentrag.config import Settings
s = Settings()
assert s.vector_dim == 384
```

---

## Group 4 — Vector Store

**Condition:** `pytest tests/unit/test_store.py -v` exits 0 with all 6 tests
marked `PASSED`. Running `grep -r "qdrant_client" src/` returns only
`src/agentrag/store/qdrant.py` — no other file imports `qdrant_client`.
`mypy --strict src/` exits 0.

---

## Group 5 — Reader

**Condition:** `pytest tests/unit/test_reader.py -v` exits 0 with all 7 tests
marked `PASSED`. The `source_id` produced by ingesting two different files
with the same filename in different directories is **not** the same value.
`mypy --strict src/` exits 0.

---

## Group 6 — Chunker

**Condition:** `pytest tests/unit/test_chunker.py -v` exits 0 with all 5 tests
marked `PASSED`. Running `grep -n "len(" src/agentrag/ingestion/chunker.py`
and `grep -n "tiktoken" src/agentrag/ingestion/chunker.py` both return empty
— no character-count or tiktoken usage. `mypy --strict src/` exits 0.

---

## Group 7 — Embedder

**Condition:** `pytest tests/unit/test_embedder.py -v` exits 0 with all 4 tests
marked `PASSED`. No actual model is downloaded during the test run — the mock
`SentenceTransformer` is used throughout. `mypy --strict src/` exits 0.

---

## Group 8 — Pipeline

**Condition:** `pytest tests/unit/test_pipeline.py -v` exits 0 with all 4 tests
marked `PASSED`. Running `grep -n "raise" src/agentrag/ingestion/pipeline.py`
returns empty — the pipeline never raises; all errors are surfaced as
`IngestResult(status="error")`. `mypy --strict src/` exits 0.

---

## Group 9 — CLI and Exit Gate Script

**Condition:** Both CLI commands execute without error:

```bash
agentrag ingest tests/fixtures/sample.txt
agentrag list
```

`agentrag ingest` prints an `IngestResult` with `status="ok"` and
`chunk_count > 0`. `agentrag list` prints at least one source row containing
the filename `sample.txt`. `scripts/verify_phase1.sh` exits 0.

---

## Group 10 — CI

**Condition:** A push to `main` triggers the GitHub Actions workflow. All 6
steps complete with green checkmarks. No steps are skipped. The workflow URL
is available in the GitHub Actions tab at
`https://github.com/SARAMALI15792/AgentRAG/actions`.

---

## Group 11 — Integration Tests

**Condition:** `pytest tests/integration/test_pipeline.py -v` exits 0 with all
4 tests marked `PASSED`. No mocks are used — the real Qdrant embedded client
and real fixture files are used. Re-ingesting `sample.txt` produces the same
`chunk_count` as the first ingest (dedup verified).

---

## Phase Exit Gate (Binding)

The phase is complete when **all** of the following are true simultaneously:

```bash
scripts/verify_phase1.sh
```

This script exits 0 if and only if:

1. `pytest` — all unit and integration tests pass, zero failures, zero errors
2. `mypy --strict src/` — zero type errors across all source files
3. `agentrag ingest tests/fixtures/sample.txt` — exits 0, prints `status="ok"`
4. `agentrag list` — exits 0, shows the ingested source

**Additionally:**

5. CI is green on `main` — GitHub Actions workflow has a green run on the
   latest commit pushed to `main`
6. Pre-commit hook is active — committing a file with a Black formatting
   violation is blocked by the hook (verified manually once)

Phase 2 may not begin until all 6 conditions above are true.

---

## What Does Not Count as Passing

These conditions are insufficient on their own:

- Tests pass locally but CI is red — **not passing**
- `mypy` has errors suppressed with `# type: ignore` without inline justification — **not passing**
- `verify_phase1.sh` exits 0 but the pre-commit hook is not installed — **not passing**
- Integration tests pass with mocks — **not passing** (integration tests must use real Qdrant)
- A subset of the 4 `verify_phase1.sh` commands pass — **not passing**
