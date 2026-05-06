# AgentRAG

> Persistent, semantically-indexed memory over private data — for Claude and any MCP-compatible agent.
> Runs fully local. No data leaves your machine.

[![CI](https://github.com/SARAMALI15792/AgentRAG/actions/workflows/ci.yml/badge.svg)](https://github.com/SARAMALI15792/AgentRAG/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/aicompatible-rag)](https://pypi.org/project/aicompatible-rag/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![mypy: strict](https://img.shields.io/badge/mypy-strict-brightgreen)](https://mypy.readthedocs.io/)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## What It Does

AI models are powerful reasoners — but they are blind to your private data. Every session starts from zero.

AgentRAG closes that gap. It is a locally-running MCP server that gives Claude a persistent, semantically-indexed memory over any documents you bring in. Claude calls `search_documents`, `plan_query`, and `evaluate_chunks` the same way it calls any other tool — and gets back the most relevant chunk from the right document, ranked by meaning rather than keyword match.

**Key properties:**

- **Fully local by default** — Qdrant vector store runs in-process, embeddings generated locally via `sentence-transformers`. No API keys required for core retrieval.
- **Universal ingestion** — 20+ file types: PDF, DOCX, XLSX, EPUB, JSON, YAML, Markdown, Python, Jupyter notebooks, subtitles, emails, and web pages.
- **Agentic retrieval** — Claude decomposes complex queries into sub-questions, searches multiple angles, scores relevance, and re-searches if needed — all through native MCP tool calls.
- **Workspace isolation** — maintain separate knowledge bases per project via named Qdrant collections.
- **Cloud sync (opt-in)** — encrypted snapshot push/pull to S3-compatible storage. Never syncs without explicit `agentrag sync push`.
- **Privacy by design** — no telemetry, no analytics, no network calls unless you explicitly configure one.

---

## 60-Second Quickstart

```bash
# Install
pip install aicompatible-rag

# (Optional) Enable agentic retrieval — free key from https://aistudio.google.com/
export AGENTRAG_GOOGLE_API_KEY=your_key_here

# Start the MCP server
agentrag serve
```

Then add the config block below to Claude Desktop and start chatting over your documents.

---

## Integrations

AgentRAG works with any MCP-compatible client. Pick the integration that matches your workflow.

---

### Claude Desktop

Add to your Claude Desktop config file:

| Platform | Path |
|----------|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

**Option A — pip install (recommended)**

```json
{
  "mcpServers": {
    "agentrag": {
      "command": "agentrag",
      "args": ["serve", "--data-dir", "~/.agentrag"]
    }
  }
}
```

**Option B — zero-install via uvx (no pip required)**

```json
{
  "mcpServers": {
    "agentrag": {
      "command": "uvx",
      "args": ["--from", "aicompatible-rag", "agentrag", "serve", "--data-dir", "~/.agentrag"]
    }
  }
}
```

---

### Claude Code (CLI)

[Claude Code](https://claude.ai/code) supports MCP servers via project-level or global config.

**Add to project** (`.claude/mcp_servers.json` in your repo):

```json
{
  "agentrag": {
    "command": "agentrag",
    "args": ["serve", "--data-dir", "~/.agentrag"],
    "env": {
      "AGENTRAG_GOOGLE_API_KEY": "your_key_here"
    }
  }
}
```

Or register globally via the Claude Code CLI:

```bash
claude mcp add agentrag agentrag serve --data-dir ~/.agentrag
```

Once registered, Claude Code can call all AgentRAG tools (`ingest_file`, `search_documents`, etc.) directly from any coding session — giving it semantic memory over your private docs, codebases, and notes.

---

### VS Code (GitHub Copilot / MCP extension)

Any VS Code extension that supports MCP servers (e.g. GitHub Copilot with MCP, or the official MCP extension) can connect to AgentRAG over HTTP transport.

**Step 1 — start AgentRAG in HTTP mode:**

```bash
AGENTRAG_TRANSPORT=http AGENTRAG_PORT=8000 agentrag serve
```

**Step 2 — add to VS Code `settings.json`:**

```json
{
  "mcp.servers": {
    "agentrag": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---

### JetBrains IDEs (IntelliJ, PyCharm, WebStorm, etc.)

JetBrains AI Assistant supports MCP servers via HTTP transport.

**Step 1 — start AgentRAG in HTTP mode:**

```bash
AGENTRAG_TRANSPORT=http AGENTRAG_PORT=8000 agentrag serve
```

**Step 2 — add in** `Settings → Tools → AI Assistant → MCP Servers`:

```
Name:    agentrag
URL:     http://localhost:8000/mcp
```

---

### Any MCP-compatible client

AgentRAG speaks the [Model Context Protocol](https://modelcontextprotocol.io/) over both `stdio` and HTTP. Any client that supports MCP can connect:

| Transport | Use case | How to start |
|-----------|----------|--------------|
| `stdio` | Claude Desktop, Claude Code, local tools | `agentrag serve` (default) |
| `http` | VS Code, JetBrains, remote agents, custom clients | `AGENTRAG_TRANSPORT=http agentrag serve` |

---

## CLI Reference

```
agentrag serve      Start the MCP server
agentrag ingest     Ingest a file or directory into the vector store
agentrag list       List all ingested sources
agentrag sync       Cloud sync subcommands (push / pull / status)
```

### `agentrag serve`

| Flag | Default | Description |
|------|---------|-------------|
| `--data-dir` | `~/.agentrag` | Root directory for Qdrant data |
| `--transport` | `stdio` | `stdio` (Claude Desktop) or `http` |
| `--port` | `8000` | HTTP port (ignored for stdio) |
| `--embed-model` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `--collection` | `documents` | Active Qdrant collection name |

### `agentrag ingest`

```bash
agentrag ingest /path/to/file.pdf
agentrag ingest /path/to/directory --recursive
```

### `agentrag sync`

```bash
agentrag sync push      # snapshot current store and upload
agentrag sync pull      # download latest snapshot and restore
agentrag sync status    # show last push/pull timestamps
```

Requires `AGENTRAG_SYNC_BACKEND`, `AGENTRAG_SYNC_ENDPOINT`, and `AGENTRAG_SYNC_KEY`.
See [Cloud Sync](#cloud-sync) for setup.

---

## Environment Variables

All variables are loaded from environment or `.env` file via `pydantic-settings`.

### Core

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENTRAG_DATA_DIR` | `~/.agentrag` | Root directory for Qdrant data and config |
| `AGENTRAG_EMBED_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model name (full `{org}/{model}` HuggingFace path) |
| `AGENTRAG_VECTOR_DIM` | `384` | Output dimension of the embedding model — must match the Qdrant collection |
| `AGENTRAG_CHUNK_SIZE` | `512` | Token chunk size for sliding-window splitting |
| `AGENTRAG_CHUNK_OVERLAP` | `64` | Token overlap between consecutive chunks |
| `AGENTRAG_PORT` | `8000` | HTTP port for HTTP transport mode |
| `AGENTRAG_TRANSPORT` | `stdio` | `stdio` or `http` |
| `AGENTRAG_COLLECTION` | `documents` | Active Qdrant collection name |
| `AGENTRAG_INGEST_TIMEOUT` | `300` | Max seconds per file ingestion before timeout |
| `AGENTRAG_MAX_FILE_SIZE_MB` | `100` | Max file size in MB — files above this are rejected with an actionable error |

### Agentic Retrieval (Gemini)

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENTRAG_GOOGLE_API_KEY` | _(none)_ | Google Gemini API key. Free key at [aistudio.google.com](https://aistudio.google.com/). Graceful degrade if missing. |
| `AGENTRAG_GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model for query decomposition and chunk evaluation |
| `AGENTRAG_QUERY_EXPAND` | `false` | Set `true` to enable Gemini-backed query expansion in `plan_query` |
| `AGENTRAG_RERANK` | `false` | Set `true` to activate cross-encoder re-ranking (`ms-marco-MiniLM-L-6-v2`) |

### Cloud Sync

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENTRAG_SYNC_BACKEND` | `local` | `local` or `s3` |
| `AGENTRAG_SYNC_ENDPOINT` | _(none)_ | S3: bucket name. S3-compatible: full endpoint URL |
| `AGENTRAG_SYNC_KEY` | _(none)_ | Fernet encryption key (base64). Generate: `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'` |
| `AGENTRAG_SYNC_LOCAL_DIR` | `~/.agentrag/backups` | Directory for local backend snapshot archives |
| `AGENTRAG_SYNC_PREFIX` | `agentrag/` | S3 key prefix for all uploaded snapshots |

---

## MCP Tools

All tools are available natively in Claude — no special prompting required.

### Ingestion

| Tool | Input | Description |
|------|-------|-------------|
| `ingest_file` | `path, metadata?` | Ingest a single local file into the vector store |
| `ingest_directory` | `path, recursive?, file_types?, metadata?` | Bulk ingest all supported files in a directory |
| `ingest_url` | `url, metadata?` | Fetch a web page and ingest its text content |

### Retrieval

| Tool | Input | Description |
|------|-------|-------------|
| `search_documents` | `query, top_k?, filters?` | Semantic search — returns chunks ranked by relevance |
| `search_by_metadata` | `filters` | Filter sources by metadata without a semantic query |
| `search_multi` | `queries, top_k?` | Search with multiple queries; deduplicates by `chunk_id` |
| `search_stream` | `query, top_k?` | Streaming search — results arrive as they score |

### Agentic Loop

| Tool | Input | Description |
|------|-------|-------------|
| `plan_query` | `query` | Decompose a complex query into focused sub-queries (Gemini-backed) |
| `evaluate_chunks` | `query, results` | Score each chunk's relevance; returns `EvaluationReport` with re-search suggestions |

### Document Management

| Tool | Input | Description |
|------|-------|-------------|
| `list_sources` | _(none)_ | List all ingested sources with metadata summary |
| `get_document` | `source_id` | Retrieve the full reconstructed text of a source |
| `delete_source` | `source_id` | Remove a source and all its vector chunks |

### Workspace (Collections)

| Tool | Input | Description |
|------|-------|-------------|
| `list_collections` | _(none)_ | List all named Qdrant collections |
| `create_collection` | `name` | Create a new named collection for workspace isolation |
| `switch_collection` | `name` | Set active collection for subsequent operations |

---

## Agentic Retrieval Loop

When `AGENTRAG_GOOGLE_API_KEY` is set, Claude can run a full agentic retrieval loop:

```
plan_query("compare treatment A and treatment B for condition X")
  → QueryPlan(sub_queries=["what is treatment A?", "what is treatment B?", "comparison studies"])

search_multi(sub_queries, top_k=5)
  → deduplicated SearchResult list

evaluate_chunks(original_query, results)
  → EvaluationReport(sufficient=False, suggested_queries=["side effects comparison", ...])

search_multi(suggested_queries)  ← re-search if not sufficient
```

All three tools degrade gracefully when the API is unavailable — retrieval is never blocked.

---

## Supported File Types

| Extension | Category | Install |
|-----------|----------|---------|
| `.txt`, `.md` | Plaintext | _(included)_ |
| `.pdf` | Document | _(included)_ |
| `.docx` | Document | _(included)_ |
| `.html` | Web | _(included)_ |
| `.py` | Code | _(included)_ |
| `.ipynb` | Notebook | _(included)_ |
| `.json`, `.yaml`, `.xml`, `.toml` | Structured data | _(included)_ |
| `.csv` | Tabular | _(included)_ |
| `.eml`, `.mbox` | Email | _(included)_ |
| `.xlsx` | Spreadsheet | `pip install aicompatible-rag[office]` |
| `.pptx` | Presentation | `pip install aicompatible-rag[office]` |
| `.epub` | eBook | `pip install aicompatible-rag[ebooks]` |
| `.mobi` | eBook | `pip install aicompatible-rag[ebooks]` |
| `.srt`, `.vtt` | Subtitles | `pip install aicompatible-rag[web]` |
| URL | Web page | `pip install aicompatible-rag[web]` |

Install all optional types at once:

```bash
pip install aicompatible-rag[all]
```

---

## Cloud Sync

AgentRAG can back up and restore your Qdrant vector store to any S3-compatible storage. All snapshots are encrypted client-side before upload — your encryption key never leaves your machine.

### Local backup (no cloud required)

```bash
# .env
AGENTRAG_SYNC_BACKEND=local
AGENTRAG_SYNC_LOCAL_DIR=~/agentrag-backups
AGENTRAG_SYNC_KEY=<your-fernet-key>
```

### S3 sync

```bash
# .env
AGENTRAG_SYNC_BACKEND=s3
AGENTRAG_SYNC_ENDPOINT=my-bucket-name
AGENTRAG_SYNC_KEY=<your-fernet-key>
```

Generate a key:
```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Then push and pull:
```bash
agentrag sync push    # snapshot + encrypt + upload
agentrag sync pull    # download + decrypt + restore
agentrag sync status  # timestamps of last push/pull
```

> **Privacy guarantee:** Snapshots are encrypted with Fernet (AES-128-CBC + HMAC-SHA256) before upload. The server never sees plaintext data.

---

## Workspace Isolation

Maintain separate knowledge bases per project using named Qdrant collections.

```bash
# via env var
AGENTRAG_COLLECTION=project-alpha agentrag serve

# via MCP tool (from Claude)
create_collection("project-alpha")
switch_collection("project-alpha")
ingest_file("/path/to/docs")
search_documents("query")   # scoped to project-alpha only
```

Data in one collection is never visible from another.

---

## Architecture

```
Ingestion path:
  File / URL
    → reader_registry (dispatches to format reader)
    → reader.py          RawDocument
    → chunker.py         List[Chunk]  (512 tokens / 64 overlap)
    → embedder.py        List[EmbeddedChunk]  (local sentence-transformers)
    → store/qdrant.py    upsert  (embedded Qdrant, persisted to ~/.agentrag)

Retrieval path:
  Claude → search_documents
    → searcher.py        embed query + qdrant.query + rerank
    → List[SearchResult]

Agentic path:
  Claude → plan_query → search_multi → evaluate_chunks → (re-search if needed)
```

**Dependency direction is strict** — `store/` never imports from `ingestion/` or `retrieval/`. `ingestion/` never imports from `retrieval/`. Reader modules in `ingestion/readers/` are pure leaf functions: `(Path) -> str`.

---

## Development Setup

```bash
git clone https://github.com/SARAMALI15792/AgentRAG
cd AgentRAG
uv pip install -e ".[dev,office,ebooks,web]"
uv run pytest --tb=short
```

### Toolchain

| Tool | Command |
|------|---------|
| Format | `uv run black .` |
| Lint | `uv run ruff check .` |
| Type check | `uv run mypy --strict src/` |
| Test | `uv run pytest --tb=short` |
| All checks | `uv run black . && uv run ruff check . && uv run mypy --strict src/` |

A pre-commit hook runs all three checks automatically before every commit.

### Project Layout

```
src/agentrag/
  cli.py              CLI entry point (typer)
  config.py           All runtime configuration (pydantic-settings)
  types.py            Domain dataclasses — single source of truth
  ingestion/          reader → chunker → embedder → pipeline
  retrieval/          searcher, reranker, query_planner, evaluator, streaming
  store/              qdrant.py — sole importer of qdrant_client
  sync/               cloud sync backends (local + S3)
  server/             MCP server, tool handlers
tests/
  unit/               isolated, all external deps mocked
  integration/        real Qdrant embedded, real files
scripts/
  verify_phase*.sh    deterministic phase exit gates
```

---

## Roadmap

| Phase | Status | Deliverable |
|-------|--------|-------------|
| 1 — Core Pipeline | ✅ Complete | read → chunk → embed → store |
| 2 — MCP Server | ✅ Complete | 7 MCP tools, stdio + HTTP transport |
| 3A — Extended Files | ✅ Complete | DOCX, HTML, Python, Jupyter |
| 3B — Agentic Retrieval | ✅ Complete | 20+ file types, `plan_query`, `search_multi`, `evaluate_chunks` |
| 4 — Search Quality | ✅ Complete | Cross-encoder reranker, metadata filter hardening |
| 5 — Distribution | ✅ Complete | PyPI package (`aicompatible-rag`), `uvx` entry point |
| 6 — Multi-Collection | ✅ Complete | Named collections, streaming retrieval |
| 7 — Cloud Sync | ✅ Complete | Encrypted push/pull to S3-compatible backends |

---

## License

MIT — see [LICENSE](LICENSE).
