# Phase 3 — Extended File Support — Validation Checklist

Phase 3 is **not complete** until every item below is checked. Partial completion
does not constitute a done phase. These criteria are immutable — changes require
user approval (Article V.5).

---

## Gate 1 — All Tests Pass

- [ ] `uv run pytest --tb=short` exits 0 with zero failures and zero errors
- [ ] The following test files are green:
  - `tests/unit/test_reader.py` — all 4 new test cases pass
  - `tests/unit/test_tools.py` — `test_ingest_directory_all_types` passes
  - `tests/integration/test_extended_ingestion.py` — all 5 integration tests pass
- [ ] No existing tests were broken by Phase 3 changes

---

## Gate 2 — Static Analysis Clean

- [ ] `uv run black . --check` exits 0 (no formatting violations)
- [ ] `uv run ruff check .` exits 0 (no lint violations)
- [ ] `uv run mypy --strict src/` exits 0 (zero type errors)
- [ ] No `# type: ignore` added without inline justification comment
- [ ] No `Any` added without inline comment explaining why it cannot be narrowed

---

## Gate 3 — Exit Gate Script

- [ ] `scripts/verify_phase3.sh` exists and is executable
- [ ] `bash scripts/verify_phase3.sh` exits 0 on a clean run
- [ ] Script exercises all 7 file types via the `agentrag ingest` CLI
- [ ] Script re-runs from a clean Qdrant state (no leftover data from previous runs)

---

## Gate 4 — CodeRabbit Review Clean

- [ ] `coderabbit:code-review` invoked on all new and modified source files:
  - `src/agentrag/ingestion/reader.py`
  - `src/agentrag/server/tools.py`
  - `tests/unit/test_reader.py`
  - `tests/unit/test_tools.py`
  - `tests/integration/test_extended_ingestion.py`
  - `scripts/verify_phase3.sh`
- [ ] Zero **blocking** issues (bugs, logic errors, security, broken contracts)
- [ ] All non-blocking issues either fixed or documented in commit body

---

## Gate 5 — Architecture Compliance

- [ ] Only `reader.py` and `tools.py` contain new logic (no boundary violations)
- [ ] `reader.py` does not import `qdrant_client`, `retrieval/`, or `server/`
- [ ] No new domain types added to `types.py` (unchanged by Phase 3)
- [ ] `ingest_directory` handler still ≤15 lines of meaningful code (Article IV.1)
- [ ] Dependency direction unchanged — verified by `mypy --strict` import analysis

---

## Gate 6 — Functional Correctness

Each of the following must be demonstrated by a passing test (not manual inspection):

- [ ] `.docx` → `RawDocument.text` is non-empty; empty paragraphs not in output
- [ ] `.html` → nav/header/footer/script/style contents absent from `RawDocument.text`
- [ ] `.html` → body `<p>` content present in `RawDocument.text`
- [ ] `.py` → `RawDocument.text` equals raw file source verbatim
- [ ] `.ipynb` → both code and markdown cell source present in `RawDocument.text`
- [ ] `.ipynb` → raw cell content absent from output
- [ ] `ingest_directory` processes all 7 types in a mixed directory

---

## Gate 7 — CI Green

- [ ] GitHub Actions CI passes on `phase/3-extended-file-support` branch
- [ ] No new CI warnings introduced
- [ ] PR opened: `phase/3-extended-file-support` → `main`

---

## Exit Statement

Phase 3 is closed when all 7 gates above are fully checked and the PR is merged
to `main`. The closing commit on `main` must reference the PR number.

Update `specs/roadmap.md` Phase 3 entry to `COMPLETE` after merge, following
the same format used for Phase 1 and Phase 2.
