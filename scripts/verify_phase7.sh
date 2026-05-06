#!/usr/bin/env bash
set -euo pipefail

echo "=== Phase 7 Exit Gate ==="

echo "[1/5] Black..."
uv run black --check .

echo "[2/5] Ruff..."
uv run ruff check .

echo "[3/5] Mypy..."
uv run mypy --strict src/

echo "[4/5] Pytest..."
uv run pytest --tb=short -q

echo "[5/5] Phase 7 smoke tests (local backend)..."
export AGENTRAG_SYNC_BACKEND=local
uv run agentrag sync status
uv run agentrag sync push
uv run agentrag sync status
uv run agentrag sync pull

echo "=== Phase 7 Exit Gate: PASSED ==="
