# Phase 5 — Distribution: Validation Criteria

Phase 5 is complete when **all** criteria below are satisfied.
The authoritative check is `scripts/verify_phase5.sh` exiting 0.

---

## Automated Gate — verify_phase5.sh

```
scripts/verify_phase5.sh exits 0
```

The script runs in order and fails fast on the first failing check:

| Step | Check |
|------|-------|
| 1 | `uv run black --check .` — zero formatting issues |
| 2 | `uv run ruff check .` — zero lint errors |
| 3 | `uv run mypy --strict src/` — zero type errors |
| 4 | `uv run pytest --tb=short -q` — zero failures, zero errors |
| 5 | `uv run python -m build` — produces wheel and sdist with zero warnings |

---

## Functional Checks

These must pass before the PR is opened. They are not run in CI but must be
confirmed locally and documented in the PR description.

### F1 — Wheel contents are clean

```
unzip -l dist/agentrag-0.1.0-*.whl
```

- All `src/agentrag/**` modules present.
- No `.env`, `__pycache__/`, `tests/`, or `specs/` directories bundled.
- `agentrag-0.1.0.dist-info/METADATA` contains correct homepage URL and license.

### F2 — uvx entry point works from local wheel

```
uvx --from ./dist/agentrag-0.1.0-*.whl agentrag serve --help
```

- Exits 0.
- Help output lists `serve`, `ingest`, and `list` commands.
- No import errors or missing dependency errors.

### F3 — README renders correctly

- Open the README on GitHub after pushing the branch.
- All tables render without broken columns.
- No broken internal links.
- The 60-second quickstart command block is copy-paste correct.

### F4 — CI matrix is green

- Both `python-version: 3.12` and `python-version: 3.13` jobs pass on the
  `phase/5-distribution` branch in GitHub Actions.

---

## Documentation Completeness Checklist

Before merge, verify README contains all of the following:

- [ ] 60-second quickstart (install → API key → `agentrag serve`)
- [ ] Claude Desktop config snippet (pip form + uvx form)
- [ ] Full env vars table (all 14 variables from `specs/tech-stack.md`)
- [ ] All 10 MCP tools listed with one-line descriptions
- [ ] Supported file types table with optional dependency groups
- [ ] CLI flags table (`--data-dir`, `--transport`, `--port`, `--embed-model`, `--collection`)

---

## Out-of-Scope for This Phase

- Live `pip install agentrag` from PyPI (deferred to post-Phase 7).
- `uvx agentrag serve` on a clean machine without a local wheel.
  (Deferred — requires PyPI publication.)
- Any new feature functionality.

---

## Merge Condition

PR to `main` may be merged when:

1. `scripts/verify_phase5.sh` exits 0 locally.
2. CI is green on both Python 3.12 and 3.13.
3. F1–F4 functional checks confirmed and noted in PR description.
4. Documentation completeness checklist fully checked.
