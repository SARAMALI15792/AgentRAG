# Changelog

All notable changes to this project are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) · Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [Unreleased]

No unreleased changes.

---

## [0.1.0] — 2026-05-06

Initial public release. Published to PyPI as `aicompatible-rag`.
Install: `pip install aicompatible-rag` · Zero-install: `uvx --from aicompatible-rag agentrag serve`

---

### Phase 7 — Cloud Sync

#### Added
- `SyncBackend` Protocol (structural typing) — swappable backend contract
- `SyncResult` and `SyncStatus` domain types
- `LocalSyncBackend` — tarfile directory snapshot with push/pull/status; Windows file-lock compatible (close + reopen Qdrant client)
- `S3SyncBackend` — Fernet AES-128-CBC + HMAC-SHA256 encryption before upload; boto3 `ClientError` handling; never raises
- Backend factory `get_sync_backend()` reading `AGENTRAG_SYNC_BACKEND` config
- `QdrantStore.create_snapshot()` and `recover_snapshot()` for filesystem-level backup
- `agentrag sync push` / `agentrag sync pull` / `agentrag sync status` CLI subcommands
- 5 new environment variables: `AGENTRAG_SYNC_BACKEND`, `AGENTRAG_SYNC_ENDPOINT`, `AGENTRAG_SYNC_KEY`, `AGENTRAG_SYNC_LOCAL_DIR`, `AGENTRAG_SYNC_PREFIX`
- `boto3` and `cryptography` optional dependency group (`agentrag[sync]`)
- 27 new tests (unit + integration) — 196 total passing
- `scripts/verify_phase7.sh` exit gate

---

### Phase 6 — Multi-Collection & Streaming Retrieval

#### Added
- `AGENTRAG_COLLECTION` environment variable (default: `documents`) for workspace isolation
- `store/qdrant.py` — replaced hardcoded `_COLLECTION` constant with `settings.collection`
- 3 new MCP tools: `list_collections`, `create_collection`, `switch_collection`
- `retrieval/streaming.py` — async generator yielding `SearchResult` as chunks score
- `search_stream` MCP tool with fallback to batch mode if MCP SDK does not support streaming
- Integration test: ingest into collection A, search collection B → empty; switch to A → results found
- `scripts/verify_phase6.sh` exit gate

---

### Phase 5 — Distribution

#### Added
- `pyproject.toml` finalized: MIT license, PyPI classifiers, `[project.urls]` with GitHub and issues links
- Version pinned at `0.1.0`; package name `aicompatible-rag` on PyPI
- `README.md` with 60-second quickstart, Claude Desktop config blocks (pip + uvx), full CLI/env/tools/file-types reference
- `CHANGELOG.md`
- `scripts/verify_phase5.sh` exit gate
- CI matrix expanded to Python 3.12 and 3.13
- GitHub Actions publish workflow — triggered on `v*` tag push (`uv build` → `uv publish` → PyPI)

---

### Phase 4 — Search Quality

#### Added
- Cross-encoder re-ranker: `cross-encoder/ms-marco-MiniLM-L-6-v2` loaded when `AGENTRAG_RERANK=true`; identity pass-through otherwise (zero overhead default)
- `AGENTRAG_RERANK` environment variable
- Metadata filter hardening: `search_documents` and `search_by_metadata` integration-tested with ≥3 distinct filter fields
- Concurrent upsert safety verified via `threading.Thread` integration test — stable `chunk_count` after 3 concurrent re-ingests
- `scripts/benchmark_retrieval.py` — ingests sample corpus, runs 10 queries, logs scores; not gated on threshold

#### Fixed
- Shared `QdrantClient` per data path to avoid `portalocker` conflicts on Linux under concurrent access

---

### Phase 3B — Extended Ingestion & Agentic Retrieval

#### Added
- **Reader plugin registry** (`ingestion/reader_registry.py`) — replaces `if/elif` dispatch chain; new file types register without modifying core pipeline
- **Office readers** (`ingestion/readers/office.py`): `.xlsx` via `openpyxl`, `.pptx` via `python-pptx`, `.csv` via stdlib
- **eBook readers** (`ingestion/readers/ebooks.py`): `.epub` via `ebooklib`, `.mobi` via `mobi`
- **Structured data readers** (`ingestion/readers/structured.py`): `.json`, `.yaml` (PyYAML), `.xml` (stdlib), `.toml` (stdlib `tomllib`)
- **Web reader** (`ingestion/readers/web.py`): URL ingestion via `httpx` + BeautifulSoup4
- **Subtitle readers** (`ingestion/readers/media.py`): `.srt` via `pysrt`, `.vtt` via `webvtt-py`
- **Email readers** (`ingestion/readers/email.py`): `.eml` and `.mbox` via stdlib `email`/`mailbox`
- `ingest_url` MCP tool — fetch, extract, and ingest any web page
- Optional dependency groups: `agentrag[office]`, `agentrag[ebooks]`, `agentrag[web]`, `agentrag[all]`
- Agentic retrieval domain types: `QueryPlan`, `ChunkScore`, `EvaluationReport`
- `retrieval/query_planner.py` — Gemini 2.0 Flash query decomposition; degrades gracefully to single-query plan when API key missing
- `retrieval/evaluator.py` — Gemini 2.0 Flash chunk relevance scoring (0.0–1.0); passes through at 0.5 when API unavailable
- `AGENTRAG_GOOGLE_API_KEY`, `AGENTRAG_GEMINI_MODEL`, `AGENTRAG_QUERY_EXPAND` environment variables
- 3 new MCP tools: `plan_query`, `search_multi`, `evaluate_chunks`
- `google-genai` runtime dependency (Gemini 2.0 Flash)

---

### Phase 3A — Extended File Support

#### Added
- `.docx` reader via `python-docx`
- `.html` reader via BeautifulSoup4 (`html.parser` backend, boilerplate tag removal)
- `.py` reader (plaintext — raw source ingestion)
- `.ipynb` reader via stdlib JSON — extracts `source` from code and markdown cells
- `ingest_directory` extended to all 7 types with recursive glob
- `python-docx` and `beautifulsoup4` runtime dependencies

---

### Phase 2 — MCP Server

#### Added
- `retrieval/searcher.py` — query embedding + Qdrant vector search + reranker pass-through
- `retrieval/reranker.py` — identity stub (activated in Phase 4)
- `server/tools.py` — 7 MCP tool handlers, each ≤15 lines of business logic: `ingest_file`, `ingest_directory`, `search_documents`, `search_by_metadata`, `list_sources`, `get_document`, `delete_source`
- `server/app.py` — FastAPI + FastMCP with `@asynccontextmanager` lifespan hook; stdio and HTTP transports
- `agentrag serve` CLI command with `--transport` flag
- `QdrantStore.get_full_document()` method
- Integration tests via `httpx.ASGITransport` (no network required)
- `pytest-asyncio 1.x` with `asyncio_mode = "auto"` (replaces deprecated `@pytest.mark.asyncio` pattern)

---

### Phase 1 — Core Ingestion Pipeline

#### Added
- Project skeleton: `pyproject.toml`, pre-commit hook (Black + Ruff + mypy), CI workflow
- Domain types in `src/agentrag/types.py`: `RawDocument`, `Chunk`, `EmbeddedChunk`, `SearchResult`, `SourceInfo`, `IngestResult`, `DeleteResult`, `DocumentContent`
- `config.py` — `pydantic-settings` `Settings` dataclass; all runtime config in one place
- `store/qdrant.py` — embedded Qdrant (sole importer of `qdrant_client`); persistent to `~/.agentrag/qdrant/`
- `ingestion/reader.py` — `.txt`, `.md`, `.pdf` via PyMuPDF
- `ingestion/chunker.py` — sliding-window tokenizer chunking (512 tokens / 64 overlap) using the embed model's `AutoTokenizer`
- `ingestion/embedder.py` — local `sentence-transformers` batch embedding (`all-MiniLM-L6-v2`, 384-dim)
- `ingestion/pipeline.py` — orchestrates reader → chunker → embedder → store; never raises; returns `IngestResult`
- `cli.py` — `agentrag ingest` and `agentrag list` CLI commands via Typer
- Unit tests (6 modules) + integration tests against a real embedded Qdrant instance
- `scripts/verify_phase1.sh` exit gate
- `TYPE_CHECKING` guard pattern in `tests/conftest.py` to prevent import-time circular dependency errors

---

[Unreleased]: https://github.com/SARAMALI15792/AgentRAG/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/SARAMALI15792/AgentRAG/releases/tag/v0.1.0
