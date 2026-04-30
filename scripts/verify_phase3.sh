#!/usr/bin/env bash
# Exit gate for Phase 3 — Extended File Support.
# Runs full test suite, type checker, and CLI smoke ingests for all 7 file types.
# Must exit 0 before Phase 3 is considered complete.

set -euo pipefail

echo "=== Phase 3 Exit Gate ==="

echo "--- Formatting and linting ---"
uv run black . && uv run ruff check .

echo "--- Running full test suite ---"
uv run pytest --tb=short

echo "--- Running mypy strict type check ---"
uv run mypy --strict src/

echo "--- CLI smoke ingests for all 7 file types ---"
for fixture in \
    tests/fixtures/sample.txt \
    tests/fixtures/sample.md \
    tests/fixtures/sample.pdf \
    tests/fixtures/sample.docx \
    tests/fixtures/sample.html \
    tests/fixtures/sample.py \
    tests/fixtures/sample.ipynb; do
    echo "  Ingesting $fixture ..."
    uv run agentrag ingest "$fixture"
done

echo "=== Phase 3 exit gate PASSED ==="
