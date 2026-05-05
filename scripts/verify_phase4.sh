#!/usr/bin/env bash
set -euo pipefail

echo "=== Phase 4 Exit Gate ==="

echo "[1/5] Black..."
uv run black --check .

echo "[2/5] Ruff..."
uv run ruff check .

echo "[3/5] Mypy..."
uv run mypy --strict src/

echo "[4/5] Pytest..."
uv run pytest --tb=short -q

echo "[5/5] Reranker smoke (AGENTRAG_RERANK=true)..."
AGENTRAG_RERANK=true uv run pytest tests/unit/test_reranker.py -q

echo "=== Phase 4 Exit Gate: PASSED ==="
