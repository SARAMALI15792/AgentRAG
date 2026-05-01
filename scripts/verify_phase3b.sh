#!/usr/bin/env bash
set -euo pipefail

echo "=== Phase 3B Exit Gate ==="

echo "[1/5] Black..."
uv run black --check .

echo "[2/5] Ruff..."
uv run ruff check .

echo "[3/5] Mypy..."
uv run mypy --strict src/

echo "[4/5] Pytest..."
uv run pytest --tb=short -q

echo "[5/5] Phase-specific smoke tests..."
uv run agentrag ingest tests/fixtures/sample.xlsx
uv run agentrag ingest tests/fixtures/sample.pptx
uv run agentrag ingest tests/fixtures/sample.csv
uv run agentrag ingest tests/fixtures/sample.epub
uv run agentrag ingest tests/fixtures/sample.json
uv run agentrag ingest tests/fixtures/sample.yaml
uv run agentrag ingest tests/fixtures/sample.xml
uv run agentrag ingest tests/fixtures/sample.toml
uv run agentrag ingest tests/fixtures/sample.srt
uv run agentrag ingest tests/fixtures/sample.eml

echo "=== Phase 3B Exit Gate: PASSED ==="
