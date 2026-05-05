# Phase 7 — Validation Criteria

Phase 7 is complete when `scripts/verify_phase7.sh` exits 0 AND the manual
cloud roundtrip check below is confirmed before PR merge.

---

## Primary Gate: `scripts/verify_phase7.sh`

```bash
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

echo "[5/6] Phase 7 smoke tests..."
# Local backend roundtrip via CLI
uv run agentrag sync push
uv run agentrag sync status
uv run agentrag sync pull

echo "[6/6] uvx zero-install re-validation..."
uv run python -m build --quiet
uvx --from ./dist/agentrag-0.1.0-*.whl agentrag serve --help
uvx --from ./dist/agentrag-0.1.0-*.whl agentrag sync push --help
uvx --from ./dist/agentrag-0.1.0-*.whl agentrag sync pull --help

echo "=== Phase 7 Exit Gate: PASSED ==="
```

The smoke tests in step 5 run against the local backend (`AGENTRAG_SYNC_BACKEND=local`).
Cloud backend is verified manually (see below) — not in CI.

---

## Functional Criteria

### SyncBackend Protocol

- [ ] A class implementing `push`, `pull`, `status` with correct signatures
      satisfies `SyncBackend` without inheriting from it (structural typing)
- [ ] `SyncResult` and `SyncStatus` types are fully annotated in `types.py`

### LocalSyncBackend

- [ ] `push()` creates a snapshot file in `AGENTRAG_SYNC_LOCAL_DIR`
- [ ] `pull()` restores data — search returns results after pull on empty store
- [ ] `push()` + `pull()` is idempotent: two push/pull cycles produce the same
      search results
- [ ] `status()` returns correct last-push timestamp and snapshot count
- [ ] `AGENTRAG_SYNC_LOCAL_DIR` missing/unwritable → `SyncResult(error)` with
      path and fix hint, no raise

### S3SyncBackend

- [ ] `push()` uploads encrypted bytes to S3 (verified: downloaded bytes differ
      from plaintext snapshot)
- [ ] `pull()` downloads and decrypts correctly — data restored matches original
- [ ] Wrong `AGENTRAG_SYNC_KEY` on pull → `SyncResult(error)` with decryption
      message, no raise
- [ ] Invalid AWS credentials → `SyncResult(error)` with actionable message,
      no raise
- [ ] No snapshots in bucket → `SyncResult(error, "no snapshots found…")`,
      no raise
- [ ] `AGENTRAG_SYNC_KEY` missing → `ValueError` with `generate_key()` command

### Backend Factory

- [ ] `AGENTRAG_SYNC_BACKEND=local` → `LocalSyncBackend`
- [ ] `AGENTRAG_SYNC_BACKEND=s3` → `S3SyncBackend`
- [ ] Unknown value → `ValueError` with supported backends listed

### CLI Commands

- [ ] `agentrag sync push` prints one-line success or error message
- [ ] `agentrag sync pull` prints one-line success or error message
- [ ] `agentrag sync status` prints backend, last push/pull times, count
- [ ] All three commands exit 0 on success, non-zero on error

---

## Type Checking

- [ ] `uv run mypy --strict src/` exits 0 with zero errors
- [ ] `SyncBackend` protocol, `LocalSyncBackend`, `S3SyncBackend` fully annotated
- [ ] `SyncResult`, `SyncStatus` dataclasses fully annotated in `types.py`
- [ ] No bare `Any` without inline comment justification

---

## Error Quality (Article XIII)

- [ ] Missing `AGENTRAG_SYNC_KEY`: error includes exact `Fernet.generate_key()`
      command to generate one
- [ ] Wrong decryption key: error says "Verify AGENTRAG_SYNC_KEY matches the
      key used during push"
- [ ] No snapshots in bucket: error names the S3 path and says "Run
      agentrag sync push first"
- [ ] Invalid credentials: error names the env var to check
      (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`)

---

## Manual Cloud Roundtrip (Required Before PR Merge)

CI does not hold AWS credentials. This check is performed manually by the
developer before opening the PR:

```bash
export AGENTRAG_SYNC_BACKEND=s3
export AGENTRAG_SYNC_ENDPOINT=<your-s3-bucket>
export AGENTRAG_SYNC_KEY=<your-fernet-key>
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>

# 1. Ingest a document
uv run agentrag ingest tests/fixtures/sample.txt

# 2. Push to S3
uv run agentrag sync push
# Expected: "Snapshot uploaded: s3://<bucket>/agentrag/snapshot_<ts>.enc"

# 3. Wipe local Qdrant data
rm -rf ~/.agentrag/qdrant

# 4. Pull from S3
uv run agentrag sync pull
# Expected: "Snapshot restored from s3://<bucket>/agentrag/snapshot_<ts>.enc"

# 5. Verify data survived
uv run agentrag list
# Expected: sample.txt listed with chunk count > 0
```

All five steps must succeed before the PR is opened.

---

## Spec Updates Required Before PR Merge

- [ ] `specs/tech-stack.md` — add `boto3 1.x`, `cryptography 42.x` to runtime
      stack table; add all five `AGENTRAG_SYNC_*` env vars to env var table;
      add `sync` optional dep group to packaging table
- [ ] `specs/roadmap.md` — mark Phase 7 complete with PR number and date
- [ ] `CHANGELOG.md` — add Phase 7 entry under `v0.2.0`

---

## PyPI Publish — Formal Deliverable

Phase 7 exit triggers the `v0.1.0` PyPI release. This is not optional.

**Sequence (after PR merges to `main`):**

```bash
# 1. Tag the release
git tag v0.1.0
git push origin v0.1.0
# → triggers CI publish workflow: uv build → uv publish → PyPI

# 2. Confirm publish job green in GitHub Actions

# 3. Verify the npx-equivalent zero-install flow from PyPI
uvx agentrag serve --help
uvx agentrag sync push --help
uvx agentrag sync pull --help
uvx agentrag sync status --help
```

**Why `uvx` is the `npx` equivalent:**

| Node.js | Python (AgentRAG) |
|---|---|
| `npx some-tool` | `uvx agentrag serve` |
| No install needed | No install needed |
| Downloads + runs from registry | Downloads + runs from PyPI |
| `package.json` entry point | `pyproject.toml` entry point |

`uvx agentrag serve` is the user-facing zero-install command documented in
the README. A new user with only `uv` installed runs this one command and
has a running MCP server — no `pip install`, no `python -m`, no venv.

**Validation:**
- [ ] `git tag v0.1.0 && git push origin v0.1.0` triggers CI publish job
- [ ] CI publish job exits 0 (package on PyPI)
- [ ] `uvx agentrag serve --help` works from PyPI (not local wheel)
- [ ] `uvx agentrag sync push --help` works from PyPI
- [ ] `uvx agentrag ingest --help` works from PyPI

---

## Definition of Done

Phase 7 is done when:

1. `scripts/verify_phase7.sh` exits 0 in CI (including uvx re-validation)
2. All functional criteria above are checked off
3. Manual S3 roundtrip completed and confirmed
4. `specs/tech-stack.md` updated with new deps and env vars
5. PR merged to `main` with CI green
6. `git tag v0.1.0` pushed — PyPI CI job green — `uvx agentrag` works from PyPI
