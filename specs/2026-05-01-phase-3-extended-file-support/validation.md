# Phase 3 — Extended File Support — Validation Checklist

Phase 3 is not complete until every gate below is checked. These criteria are
immutable — changes require user approval (Article V.5).

---

## Gate 1 — Implementation Files Correct

Verify `reader.py` and `tools.py` were written as specified before running
any tests.

- [ ] `reader.py` has one new private helper for `.docx`, one for `.html`,
      one for `.ipynb` — exactly three new helpers, no more
- [ ] `.py` files use the existing read-text path with no new helper added
- [ ] The supported suffix set in `read_file` includes all seven types
- [ ] The dispatch block routes each suffix to the correct helper
- [ ] Empty paragraphs are filtered in the `.docx` helper
- [ ] Boilerplate tags (`nav`, `header`, `footer`, `script`, `style`) are
      removed before text extraction in the `.html` helper
- [ ] Only `code` and `markdown` cell types are collected in the `.ipynb`
      helper; `raw` cells and cell outputs are excluded
- [ ] The public `read_file` signature is unchanged
- [ ] `reader.py` imports only `json`, `BeautifulSoup`, and `Document` as
      new additions — no imports from `retrieval/`, `server/`, or `qdrant_client`
- [ ] `ingest_directory` in `tools.py` lists all seven extensions in its glob loop
- [ ] `ingest_directory` is still within 15 lines of meaningful code
- [ ] `types.py` is unchanged — no new dataclasses added

---

## Gate 2 — Test Files Correct

Verify the test files are complete and cover what was specified.

- [ ] `test_reader.py` has four new test cases: one each for `.docx`, `.html`,
      `.py`, `.ipynb`
- [ ] The `.docx` test asserts non-empty text, correct filename, 16-char hex
      source_id, and that the blank paragraph from the fixture is absent
- [ ] The `.html` test asserts that all five boilerplate sentinel strings are
      absent from the output and that body content is present
- [ ] The `.py` test asserts that output text is identical to the raw file source
- [ ] The `.ipynb` test asserts code and markdown cell sentinels are present
      and the raw cell sentinel is absent
- [ ] `test_tools.py` has one new test that covers all seven file types in a
      single `ingest_directory` call with the pipeline mocked
- [ ] `test_extended_ingestion.py` exists with five tests covering `.docx`,
      `.html`, `.py`, `.ipynb` individually and `ingest_directory` mixed
- [ ] Integration tests for `.html` assert that boilerplate content is not
      retrievable via `search_documents` — not just absent from `RawDocument`
- [ ] All four fixture files exist in `tests/fixtures/` and match their specs

---

## Gate 3 — All Tests Pass

- [ ] `uv run pytest tests/unit/test_reader.py` — all tests green, no regressions
- [ ] `uv run pytest tests/unit/test_tools.py` — all tests green, no regressions
- [ ] `uv run pytest tests/integration/test_extended_ingestion.py` — all five
      tests green
- [ ] `uv run pytest --tb=short` (full suite) exits 0 — zero failures, zero errors

---

## Gate 4 — Static Analysis

- [ ] `uv run black . --check` exits 0
- [ ] `uv run ruff check .` exits 0
- [ ] `uv run mypy --strict src/` exits 0
- [ ] No `# type: ignore` without an inline comment identifying the suppressed
      error and explaining why suppression is the only option
- [ ] No `Any` without an inline comment explaining why it cannot be narrowed

---

## Gate 5 — Exit Gate Script

- [ ] `scripts/verify_phase3.sh` exists and is executable
- [ ] The script runs the full test suite, the type-checker, and CLI smoke
      ingests of all seven fixture files
- [ ] `bash scripts/verify_phase3.sh` exits 0

---

## Gate 6 — CodeRabbit Review

- [ ] `coderabbit:code-review` run on `reader.py`, `tools.py`,
      `test_reader.py`, `test_tools.py`, `test_extended_ingestion.py`,
      and `verify_phase3.sh`
- [ ] Zero blocking issues
- [ ] All non-blocking issues either fixed or explained in the commit body

---

## Gate 7 — CI and Merge

- [ ] GitHub Actions passes on `phase/3-extended-file-support`
- [ ] PR open from `phase/3-extended-file-support` to `main`
- [ ] PR merged to `main` with CI green
- [ ] `specs/roadmap.md` Phase 3 entry updated to `COMPLETE` with merge date
      and PR number
