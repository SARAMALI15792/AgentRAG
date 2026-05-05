#!/usr/bin/env bash
set -euo pipefail

echo "=== Phase 6 Exit Gate ==="

echo "[1/5] Black..."
uv run black --check .

echo "[2/5] Ruff..."
uv run ruff check .

echo "[3/5] Mypy..."
uv run mypy --strict src/

echo "[4/5] Pytest..."
uv run pytest --tb=short -q

echo "[5/5] Phase-specific smoke tests..."
uv run python scripts/smoke_phase6.py

echo "=== Phase 6 Exit Gate: PASSED ==="
