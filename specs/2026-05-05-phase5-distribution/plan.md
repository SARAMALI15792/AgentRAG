# Phase 5 — Distribution: Implementation Plan

Execution order is strict. Each task group must be fully green before the next begins.
TDD applies to all testable deliverables. Verify script is written first (Task Group 1).

---

## Task Group 1 — Exit Gate Script (write first)

1.1. Create `scripts/verify_phase5.sh` with the standard 5-step structure (Article XI.2).
     Phase-specific check: `uv run python -m build` produces a wheel with no warnings.
1.2. Confirm the script fails on the current state (no wheel yet — expected).

---

## Task Group 2 — Package Metadata

2.1. Open `pyproject.toml` and finalize all required fields:
     - `name = "agentrag"`
     - `version = "0.1.0"`
     - `description` — one-line plain-language summary
     - `license = { text = "MIT" }`
     - `[project.urls]` with `Homepage`, `Repository`, `Issues` pointing to
       `https://github.com/SARAMALI15792/AgentRAG`
     - `classifiers` — standard PyPI classifiers (Python versions, license, OS)
     - `requires-python = ">=3.12"` (already set — verify)
2.2. Run `uv run python -m build` — confirm wheel and sdist build with zero warnings.
2.3. Inspect wheel contents with `unzip -l dist/*.whl | head -40` — verify all source files
     are included and no unintended files (`.env`, `__pycache__`, test fixtures) are bundled.

---

## Task Group 3 — Zero-Install Entry Point

3.1. Verify `[project.scripts] agentrag = "agentrag.cli:app"` is present and correct.
3.2. Run `uvx --from ./dist/agentrag-0.1.0-*.whl agentrag serve --help` locally — confirm
     the CLI starts and prints help without error.
3.3. Verify Claude Desktop JSON config snippet works (stdio transport, `uvx` form).
     Document confirmed snippet in requirements.md.

---

## Task Group 4 — Documentation

4.1. Create `README.md` at project root with:
     - 60-second quickstart: install → set `AGENTRAG_GOOGLE_API_KEY` → `agentrag serve`
     - Claude Desktop config block (both `pip install` and `uvx` forms, copy-paste ready)
     - Full table of CLI flags and env vars (sourced from `config.py` and `specs/tech-stack.md`)
     - All 10 MCP tools listed with one-line descriptions
     - Supported file types table with optional dependency groups
     - Optional: badge row (CI, PyPI, Python version)
4.2. Create `CHANGELOG.md` at project root with a single `v0.1.0` entry summarising
     all five completed phases. Use Keep a Changelog format.
4.3. Verify both files render correctly in GitHub markdown preview (no broken links or
     malformed tables).

---

## Task Group 5 — CI Hardening

5.1. Edit `.github/workflows/ci.yml` — extend the test job with a Python version matrix:
     `python-version: ["3.12", "3.13"]`.
5.2. Add a `publish` job to `.github/workflows/ci.yml` (or a separate `release.yml`):
     - Triggered on `v*` tag push only.
     - Steps: checkout → `uv build` → `uv publish` (uses `PYPI_TOKEN` secret).
     - Job is defined and syntactically valid; actual publication deferred to after Phase 7.
     - Add a comment in the workflow making the deferral explicit.
5.3. Push the branch and verify CI turns green across both Python versions.

---

## Task Group 6 — Exit Gate

6.1. Run `scripts/verify_phase5.sh` locally — confirm exit 0.
6.2. Verify CI is green on `phase/5-distribution` (all matrix versions).
6.3. Open PR → `main`.
