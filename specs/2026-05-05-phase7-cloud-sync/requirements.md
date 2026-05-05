# Phase 7 — Requirements

## Goal

Add optional, user-opt-in cloud sync for the AgentRAG vector store. Users
can back up their Qdrant data to cloud storage and restore it on any machine.
Privacy-first: data is encrypted before it leaves the machine. No sync
happens without an explicit user action.

This phase completes the mission's "workspace isolation + cloud sync" goal,
unblocking the PyPI publish that was deferred at the end of Phase 5.

---

## Scope

**In scope:**
- `SyncBackend` protocol and `LocalSyncBackend` (always available, no cloud)
- `S3SyncBackend` — Amazon S3 as the primary cloud backend
- Fernet encryption of snapshots before upload
- Three CLI commands: `agentrag sync push`, `pull`, `status`
- New env vars for sync configuration
- Integration test for local roundtrip

**Out of scope:**
- Google Drive and Azure Blob backends (future phases, user approval required)
- Automatic scheduled sync (no background process)
- Partial sync (incremental delta) — full snapshot only
- Sync of config files or `.env` — Qdrant data only
- Multi-backend simultaneous push

---

## Cloud Provider Decision: Amazon S3

S3 is chosen as the sole cloud backend for this phase.

**Why S3:**
- `boto3` is the most widely used Python cloud SDK — minimal friction
- Works with any S3-compatible store: AWS S3, Backblaze B2, Cloudflare R2,
  MinIO (self-hosted). Users who prefer not to use AWS can point
  `AGENTRAG_SYNC_ENDPOINT` at any S3-compatible endpoint
- GDrive requires an OAuth2 browser flow — incompatible with headless/CLI use
- Azure Blob is enterprise-focused; S3 has broader accessibility

**Dependency added:** `boto3 1.x` to runtime deps.

---

## Encryption: Fernet (cryptography library)

**Why Fernet:**
- AES-128-CBC + HMAC-SHA256. Well-audited, stdlib-adjacent, zero config
- Key is a URL-safe base64 string — user can store it in a password manager
- `cryptography` package is already a common transitive dep; explicit runtime
  dep keeps the version pinned

**Key lifecycle:**
- `AGENTRAG_SYNC_KEY` env var holds the Fernet key (base64 string)
- If absent: push/pull raises `ValueError` with actionable message:
  `"Set AGENTRAG_SYNC_KEY to a Fernet key. Generate one with: python -c
  'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"`
- Key is never logged, never stored in AgentRAG data files
- AgentRAG does not rotate keys — user is responsible for key management

**Dependency added:** `cryptography 42.x` to runtime deps.

---

## SyncBackend Protocol

```python
# src/agentrag/sync/base.py
class SyncBackend(Protocol):
    def push(self) -> SyncResult: ...
    def pull(self) -> SyncResult: ...
    def status(self) -> SyncStatus: ...
```

**Why Protocol (not ABC):** structural subtyping means future backends need
zero imports from `agentrag.sync`. Swap the backend by implementing three
methods — no inheritance required.

**New types in `types.py`:**

```python
@dataclass
class SyncResult:
    status: Literal["ok", "error"]
    message: str
    snapshot_id: str | None = None   # set on successful push

@dataclass
class SyncStatus:
    backend: str                      # "local" or "s3"
    last_push: str | None             # ISO 8601 or None
    last_pull: str | None
    snapshot_count: int
```

---

## LocalSyncBackend

Uses the Qdrant embedded snapshot API to create and restore full snapshots.

- `push()`: `QdrantStore.create_snapshot()` → copy file to
  `AGENTRAG_SYNC_LOCAL_DIR` (default: `~/.agentrag/backups/`).
  Filename: `snapshot_{ISO8601}.snapshot`
- `pull()`: find latest `.snapshot` file in dir → `QdrantStore.recover_snapshot()`
- `status()`: scan dir for `.snapshot` files, return timestamps and count

**Note:** `QdrantStore` must expose `create_snapshot()` and
`recover_snapshot()` methods. These are new methods on the existing
`store/qdrant.py` — the sole permitted importer of `qdrant_client`.

---

## S3SyncBackend

```
push():
  1. QdrantStore.create_snapshot() → tmp file
  2. Fernet(key).encrypt(file bytes)
  3. s3.put_object(Bucket=bucket, Key=key_prefix/snapshot_{ts}.enc, Body=ciphertext)
  4. delete tmp file
  5. return SyncResult(ok, snapshot_id=s3_key)

pull():
  1. s3.list_objects_v2(Bucket=bucket, Prefix=key_prefix)
  2. pick latest by LastModified
  3. s3.get_object → ciphertext
  4. Fernet(key).decrypt(ciphertext) → plaintext bytes
  5. write to tmp file
  6. QdrantStore.recover_snapshot(tmp_file)
  7. return SyncResult(ok)
```

**Error handling (Article XIII):**
- `ClientError` from boto3: return `SyncResult(error=<actionable message>)`. Never raise.
- `InvalidToken` from Fernet (wrong key): `SyncResult(error="Decryption failed. Verify AGENTRAG_SYNC_KEY matches the key used during push.")`
- No snapshots in bucket: `SyncResult(error="No snapshots found in s3://{bucket}/{prefix}. Run 'agentrag sync push' first.")`

---

## New Environment Variables

| Variable | Default | Description |
|---|---|---|
| `AGENTRAG_SYNC_BACKEND` | `local` | `local` or `s3`. Selects active sync backend. |
| `AGENTRAG_SYNC_ENDPOINT` | _(S3 bucket name)_ | For S3: bucket name. For S3-compatible: full endpoint URL. |
| `AGENTRAG_SYNC_KEY` | _(required for push/pull)_ | Fernet encryption key. Generate with `Fernet.generate_key()`. |
| `AGENTRAG_SYNC_LOCAL_DIR` | `~/.agentrag/backups` | Directory for local backend snapshots. |
| `AGENTRAG_SYNC_PREFIX` | `agentrag/` | S3 key prefix for all uploaded snapshots. |

All five variables added to `config.py` and to `specs/tech-stack.md`
simultaneously (Article IV.3).

---

## CLI Commands

Three subcommands added to the existing `typer` app under a `sync` group:

```
agentrag sync push    — create snapshot, encrypt, upload to backend
agentrag sync pull    — download latest snapshot, decrypt, restore
agentrag sync status  — print last push/pull times and snapshot count
```

Output is human-readable, one-line summary. Errors include the fix hint from
`SyncResult.message` verbatim.

---

## Dependency Direction

New additions comply with Article IV.4:

```
cli.py           →  sync/factory.py
sync/factory.py  →  sync/local.py, sync/cloud.py
sync/local.py    →  store/qdrant.py (snapshot methods only)
sync/cloud.py    →  store/qdrant.py (snapshot methods only)
sync/            →  (external: boto3, cryptography)
```

`sync/` imports from `store/` only — no imports from `ingestion/`,
`retrieval/`, or `server/`. Zero circular dependencies.

---

## Privacy Guarantee

- No sync happens without explicit `agentrag sync push` invocation
- All data is encrypted with user's key before leaving the machine
- AgentRAG never stores or transmits the encryption key
- `AGENTRAG_SYNC_KEY` is read from env — never from a file AgentRAG writes
- Metadata (snapshot timestamps, S3 key names) is not encrypted — these
  contain no document content
