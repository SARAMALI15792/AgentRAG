#!/usr/bin/env bash
# Phase 1 exit gate — deterministic verification script
# Exit code 0 = phase complete, ready for Phase 2

set -e  # Exit on any error

echo "=== Phase 1 Exit Gate ==="
echo ""

echo "Step 1: Running pytest..."
uv run pytest
echo "✓ All tests pass"
echo ""

echo "Step 2: Running mypy --strict..."
uv run mypy --strict src/
echo "✓ Type checking passes"
echo ""

echo "Step 3: Smoke test — ingest sample.txt..."
uv run agentrag ingest tests/fixtures/sample.txt
echo "✓ Ingestion succeeds"
echo ""

echo "Step 4: Smoke test — list sources..."
uv run agentrag list
echo "✓ List command succeeds"
echo ""

echo "=== Phase 1 Exit Gate: PASSED ==="
echo "Phase 1 complete. Ready for Phase 2."
