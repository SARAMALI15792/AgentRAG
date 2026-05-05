#!/usr/bin/env bash
set -euo pipefail

echo "=== Phase 5 Exit Gate ==="

echo "[1/5] Black..."
uv run black --check .

echo "[2/5] Ruff..."
uv run ruff check .

echo "[3/5] Mypy..."
uv run mypy --strict src/

echo "[4/5] Pytest..."
uv run pytest --tb=short -q

echo "[5/5] Build wheel..."
rm -rf dist/
uv run python -m build
ls dist/agentrag-0.1.0-*.whl

echo "=== Phase 5 Exit Gate: PASSED ==="
