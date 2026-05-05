# Phase 7 — Implementation Plan

Execution order is strict. TDD is mandatory — failing test before every
implementation file. Cloud backend (Step 2) is gated behind the local
backend (Step 1) — the abstraction must be proven locally first.

---

## Step 0 — Context7 Lookups _(before any code)_

- [ ] `boto3` — `S3Client`, `upload_file`, `download_file`, `list_objects_v2`,
      presigned URLs, error handling (`ClientError`)
- [ ] `cryptography` — `Fernet`, key generation, `encrypt`, `decrypt`,
      `InvalidToken` error
- [ ] `qdrant-client` — snapshot API: `create_full_snapshot`, `recover_snapshot`,
      snapshot listing and deletion

---

## Step 1 — Sync Abstraction Layer

- [ ] `tests/unit/test_sync_base.py` — confirm `SyncBackend` protocol is
      structurally correct: class implementing `push`, `pull`, `status` satisfies it
      without inheriting — confirm red, then green
- [ ] `src/agentrag/sync/__init__.py` — empty module init
- [ ] `src/agentrag/sync/base.py` — `SyncBackend` protocol:
      ```
      class SyncBackend(Protocol):
          def push(self) -> SyncResult: ...
          def pull(self) -> SyncResult: ...
          def status(self) -> SyncStatus: ...
      ```
- [ ] Add `SyncResult` and `SyncStatus` dataclasses to `src/agentrag/types.py`
- [ ] `tests/unit/test_sync_local.py` — local backup roundtrip: push creates
      snapshot file, pull restores it, status reports last sync time — confirm red
- [ ] `src/agentrag/sync/local.py` — `LocalSyncBackend`:
      - `push()`: call Qdrant snapshot API → copy snapshot to
        `AGENTRAG_SYNC_LOCAL_DIR` with timestamp filename
      - `pull()`: find latest snapshot in dir → call Qdrant recover API
      - `status()`: return last push/pull timestamps and snapshot count
- [ ] Run `uv run pytest tests/unit/test_sync_local.py` — green

---

## Step 2 — Cloud Backend (S3)

- [ ] `tests/unit/test_sync_cloud.py` — S3 client mocked:
      - `push()` uploads encrypted snapshot to S3, returns `SyncResult(ok)`
      - `pull()` downloads latest snapshot, decrypts, restores — returns `SyncResult(ok)`
      - `push()` with invalid credentials → `SyncResult(error)` with message, no raise
      - `pull()` with no snapshots in bucket → `SyncResult(error, "no snapshots found")`
      - Encrypted bytes differ from plaintext (encryption is applied)
      Confirm red
- [ ] `src/agentrag/sync/cloud.py` — `S3SyncBackend`:
      - Encrypt snapshot with `Fernet(key)` before upload
      - Decrypt after download before passing to Qdrant recover
      - Key sourced from `AGENTRAG_SYNC_KEY` env var
      - Bucket from `AGENTRAG_SYNC_ENDPOINT`
      - Catch `ClientError`, return `SyncResult(error=...)` — never raise
- [ ] Add `boto3 1.x` to runtime deps in `pyproject.toml`
- [ ] Add `cryptography 42.x` to runtime deps in `pyproject.toml`
- [ ] Run `uv lock`
- [ ] Run `uv run pytest tests/unit/test_sync_cloud.py` — green

---

## Step 3 — Backend Factory

- [ ] `tests/unit/test_sync_factory.py` — `AGENTRAG_SYNC_BACKEND=local` →
      returns `LocalSyncBackend`; `=s3` → returns `S3SyncBackend`;
      unknown value → `ValueError` with actionable message — confirm red
- [ ] `src/agentrag/sync/factory.py` — `get_sync_backend(settings) -> SyncBackend`
- [ ] Add `AGENTRAG_SYNC_BACKEND`, `AGENTRAG_SYNC_ENDPOINT`, `AGENTRAG_SYNC_KEY`,
      `AGENTRAG_SYNC_LOCAL_DIR` to `src/agentrag/config.py`
- [ ] Run pytest — green

---

## Step 4 — CLI Commands

- [ ] `tests/unit/test_cli_sync.py` — mock sync backend:
      - `agentrag sync push` → calls `backend.push()`, prints result
      - `agentrag sync pull` → calls `backend.pull()`, prints result
      - `agentrag sync status` → calls `backend.status()`, prints summary
      Confirm red
- [ ] `src/agentrag/cli.py` — add `sync` command group with `push`, `pull`,
      `status` subcommands via typer
- [ ] Run pytest — green

---

## Step 5 — Integration Test (Local Backend)

- [ ] `tests/integration/test_sync_local.py` — real Qdrant embedded:
      - Ingest `sample.txt` → `push()` creates snapshot file on disk
      - Delete collection → `pull()` restores data → search returns results
      - `status()` returns non-empty last-sync timestamp
      - Roundtrip is idempotent: push + pull + push produces same snapshot size
- [ ] Run integration tests — green

---

## Step 6 — Update `specs/tech-stack.md`

- [ ] Add `boto3 1.x` and `cryptography 42.x` to the tech-stack table
- [ ] Add new env vars (`AGENTRAG_SYNC_*`) to the environment variable table
- [ ] Update Packaging section: add `sync` optional dep group

---

## Step 7 — Exit Gate

- [ ] `scripts/verify_phase7.sh` — write and run
- [ ] All checks pass: black, ruff, mypy, pytest, phase-specific smoke tests
- [ ] Manual cloud roundtrip verified before PR merge
- [ ] Push branch, open PR against `main`

---

## Step 8 — PyPI Publish (Phase 7 Exit Triggers v0.1.0)

This step runs after the PR is merged to `main` and CI is green.

- [ ] Confirm `uv run python -m build` produces clean wheel with zero warnings
- [ ] Confirm `uvx --from ./dist/agentrag-0.1.0-*.whl agentrag serve --help`
      exits 0 (zero-install entry point works)
- [ ] Confirm `uvx --from ./dist/agentrag-0.1.0-*.whl agentrag sync --help`
      exits 0 (sync commands present in published wheel)
- [ ] Run `git tag v0.1.0 && git push origin v0.1.0`
      — triggers CI publish workflow (`uv build` → `uv publish` → PyPI)
- [ ] Confirm PyPI publish job green in GitHub Actions
- [ ] Confirm `uvx agentrag serve --help` works from PyPI (zero-install,
      no local wheel — this is the user-facing `npx`-equivalent flow):
      ```bash
      uvx agentrag serve --help
      uvx agentrag sync push --help
      ```
- [ ] Update `specs/roadmap.md` — mark Phase 7 complete, record PyPI publish date
