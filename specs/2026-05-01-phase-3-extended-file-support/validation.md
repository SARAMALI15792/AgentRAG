# Phase 3 — Extended File Support — Validation Checklist

Phase 3 is **not complete** until every gate below is checked. Partial completion
does not constitute a done phase. These criteria are immutable — changes require
user approval (Article V.5).

---

## Gate 1 — Implementation Shape

Verify the code was written correctly before running anything.

- [ ] `reader.py` has exactly 3 new private helpers: `_read_docx`, `_read_html`, `_read_ipynb`
- [ ] `_read_docx` uses `Document(path)` from `python-docx`; skips empty paragraphs
- [ ] `_read_html` calls `.decompose()` on `nav/header/footer/script/style` before `get_text()`
- [ ] `_read_ipynb` includes `"code"` and `"markdown"` cells; excludes `"raw"` and outputs
- [ ] `.py` has **no new helper** — it falls through to the existing `path.read_text()` branch
- [ ] Supported suffix set in `read_file()` expanded to all 7 types
- [ ] `read_file()` public signature unchanged: `(path: Path) -> RawDocument`
- [ ] `ingest_directory` glob list extended to 7 extensions, stale comment removed
- [ ] `ingest_directory` is still ≤15 lines of meaningful code (Article IV.1)
- [ ] New imports added to `reader.py`: `json`, `BeautifulSoup`, `Document`
- [ ] No new imports added to `tools.py` (glob change requires none)
- [ ] `types.py` unchanged — no new dataclasses

---

## Gate 2 — Static Analysis

- [ ] `uv run black . --check` exits 0
- [ ] `uv run ruff check .` exits 0
- [ ] `uv run mypy --strict src/` exits 0
- [ ] No `# type: ignore` without inline justification
- [ ] No `Any` without inline comment explaining why it cannot be narrowed

---

## Gate 3 — Unit Tests Pass

- [ ] `test_read_docx`: `RawDocument.text` non-empty; empty paragraph from fixture absent
- [ ] `test_read_html`: "NAVTEXT", "SCRIPTTEXT", "STYLETEXT", "HEADERTEXT", "FOOTERTEXT"
      all absent from `RawDocument.text`; "BODYTEXT" present
- [ ] `test_read_py`: `RawDocument.text` equals the fixture file's raw source verbatim
- [ ] `test_read_ipynb`: code cell sentinel string present; markdown cell sentinel present;
      raw cell sentinel absent
- [ ] `test_ingest_directory_all_types`: `ingest()` called exactly 7 times for a
      directory containing one file of each type
- [ ] All pre-existing reader and tools unit tests still pass (no regressions)

---

## Gate 4 — Integration Tests Pass

End-to-end pipeline verification with real embedded Qdrant:

- [ ] `test_ingest_docx`: `status == "ok"`, `chunk_count > 0`
- [ ] `test_ingest_html`: `chunk_count > 0`; boilerplate sentinel strings absent from
      all `SearchResult.text` values (proves stripping survives chunker + store round-trip)
- [ ] `test_ingest_py`: `chunk_count > 0`; a known function name from the fixture
      is retrievable via `search_documents`
- [ ] `test_ingest_ipynb`: `chunk_count > 0`; markdown cell sentinel present in
      at least one `SearchResult.text`
- [ ] `test_ingest_directory_mixed`: 7 results, all `status == "ok"`, all `chunk_count > 0`
- [ ] `uv run pytest --tb=short` (full suite) exits 0 — zero failures, zero errors

---

## Gate 5 — Exit Gate Script

- [ ] `scripts/verify_phase3.sh` exists, is executable (`chmod +x`)
- [ ] `bash scripts/verify_phase3.sh` exits 0
- [ ] Script runs pytest, mypy, and CLI smoke ingest of all 7 fixture files

---

## Gate 6 — CodeRabbit Review

- [ ] `coderabbit:code-review` run on every new/changed file:
      `reader.py`, `tools.py`, `test_reader.py`, `test_tools.py`,
      `test_extended_ingestion.py`, `verify_phase3.sh`
- [ ] Zero blocking issues (bugs, logic errors, security, broken contracts)
- [ ] All non-blocking issues either fixed or explained in commit body

---

## Gate 7 — CI Green

- [ ] GitHub Actions passes on `phase/3-extended-file-support`
- [ ] PR opened: `phase/3-extended-file-support` → `main`
- [ ] PR merged to `main` with CI green

---

## Exit Statement

Phase 3 closes when all 7 gates are checked and the PR is merged to `main`.
After merge, update `specs/roadmap.md` Phase 3 entry to `COMPLETE` using the
same format as Phase 1 and Phase 2 (date, PR number, summary of what shipped).
