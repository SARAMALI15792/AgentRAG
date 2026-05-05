# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added

**Phase 1 — Core Ingestion Pipeline**
- Project skeleton with `pyproject.toml`, pre-commit hook, and CI workflow
- Domain types: `RawDocument`, `Chunk`, `EmbeddedChunk`, `SearchResult`, `SourceInfo`, `IngestResult`, `DeleteResult`, `DocumentContent`
- `config.py` — pydantic-settings `Settings` with 14 environment variables
- `store/qdrant.py` — embedded Qdrant store (sole importer of `qdrant_client`)
- `ingestion/reader.py` — `.txt`, `.md`, `.pdf` via PyMuPDF
- `ingestion/chunker.py` — sliding-window tokenizer chunking (512 tokens, 64 overlap)
- `ingestion/embedder.py` — local sentence-transformers batch embedding
- `ingestion/pipeline.py` — orchestrates reader → chunker → embedder → store; never raises
- `cli.py` — `agentrag ingest` and `agentrag list` CLI commands
- Unit and integration test suite with real Qdrant embedded instance

**Phase 2 — MCP Server**
- `retrieval/searcher.py` — query embedding + Qdrant vector search
- `retrieval/reranker.py` — cross-encoder re-ranker (activated via `AGENTRAG_RERANK=true`)
- `server/tools.py` — 7 MCP tool handlers: `ingest_file`, `ingest_directory`, `search_documents`, `search_by_metadata`, `list_sources`, `get_document`, `delete_source`
- `server/app.py` — FastAPI + FastMCP with lifespan hook, stdio and HTTP transports
- `agentrag serve` CLI command with `--transport` flag
- Integration tests via `httpx.ASGITransport`

**Phase 3A — Extended File Support**
- `.docx` reader via `python-docx`
- `.html` reader via BeautifulSoup4
- `.py` reader (plaintext)
- `.ipynb` reader via stdlib JSON
- `ingest_directory` extended to all 7 supported types with recursive glob

**Phase 3B — Extended Ingestion and Agentic Retrieval**
- Reader plugin registry (`reader_registry.py`) replacing `if/elif` dispatch chain
- Office readers: `.xlsx` (openpyxl), `.pptx` (python-pptx), `.csv` (stdlib)
- eBook readers: `.epub` (ebooklib), `.mobi` (mobi)
- Structured data readers: `.json`, `.yaml` (PyYAML), `.xml` (stdlib), `.toml` (stdlib tomllib)
- Web reader: URL ingestion via httpx + BeautifulSoup4
- Subtitle readers: `.srt` (pysrt), `.vtt` (webvtt-py)
- Email readers: `.eml`, `.mbox` (stdlib email/mailbox)
- `ingest_url` MCP tool
- Agentic retrieval types: `QueryPlan`, `ChunkScore`, `EvaluationReport`
- `retrieval/query_planner.py` — Gemini-backed query decomposition with graceful degradation
- `retrieval/evaluator.py` — Gemini-backed chunk relevance scoring with graceful degradation
- New MCP tools: `plan_query`, `search_multi`, `evaluate_chunks`

**Phase 4 — Search Quality**
- Cross-encoder re-ranker: `cross-encoder/ms-marco-MiniLM-L-6-v2` activated via `AGENTRAG_RERANK=true`
- Metadata filter hardening: `search_documents` and `search_by_metadata` tested with ≥3 filter fields
- Concurrent upsert safety verified via threading integration test
- `scripts/benchmark_retrieval.py` for retrieval quality measurement

**Phase 5 — Distribution**
- `pyproject.toml` finalized: MIT license, PyPI classifiers, `[project.urls]`
- `README.md` with 60-second quickstart, Claude Desktop config, full CLI/env/tools/file-types reference
- `CHANGELOG.md` (this file)
- `scripts/verify_phase5.sh` exit gate
- CI matrix expanded to Python 3.12 and 3.13
- GitHub Actions publish workflow defined — triggered on `v*` tag push; publication deferred to post-Phase 7
