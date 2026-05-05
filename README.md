# AgentRAG

Agentic RAG MCP Server — persistent, semantically-indexed memory over private data for Claude and any MCP-compatible agent. Runs locally. No data leaves your machine.

[![CI](https://github.com/SARAMALI15792/AgentRAG/actions/workflows/ci.yml/badge.svg)](https://github.com/SARAMALI15792/AgentRAG/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 60-Second Quickstart

```bash
pip install agentrag
export AGENTRAG_GOOGLE_API_KEY=your_key_here   # optional — enables agentic retrieval
agentrag serve
```

Claude Desktop picks it up immediately. No restart needed after adding the config below.

---

## Claude Desktop Integration

Add to your Claude Desktop config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

### Option A — pip install (recommended)

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

### Option B — zero-install via uvx (no pip required)

```json
{
  "mcpServers": {
    "agentrag": {
      "command": "uvx",
      "args": ["agentrag", "serve", "--data-dir", "~/.agentrag"]
    }
  }
}
```

---

## CLI Reference

```
agentrag serve    Start the MCP server
agentrag ingest   Ingest a file or directory into the vector store
agentrag list     List all ingested sources
```

### `agentrag serve` flags

| Flag | Default | Description |
|------|---------|-------------|
| `--data-dir` | `~/.agentrag` | Root directory for Qdrant data |
| `--transport` | `stdio` | `stdio` (Claude Desktop) or `http` |
| `--port` | `8000` | HTTP port (ignored for stdio transport) |
| `--embed-model` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model name |
| `--collection` | `documents` | Active Qdrant collection name |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENTRAG_DATA_DIR` | `~/.agentrag` | Root directory for Qdrant data and config |
| `AGENTRAG_EMBED_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model name |
| `AGENTRAG_VECTOR_DIM` | `384` | Output dimension of the embedding model |
| `AGENTRAG_CHUNK_SIZE` | `512` | Token chunk size for splitting |
| `AGENTRAG_CHUNK_OVERLAP` | `64` | Token overlap between chunks |
| `AGENTRAG_PORT` | `8000` | HTTP port for HTTP transport |
| `AGENTRAG_TRANSPORT` | `stdio` | `stdio` or `http` |
| `AGENTRAG_RERANK` | `false` | Set `true` to activate cross-encoder re-ranking |
| `AGENTRAG_GOOGLE_API_KEY` | _(none)_ | Google Gemini API key — enables agentic retrieval |
| `AGENTRAG_GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model for query planning and evaluation |
| `AGENTRAG_QUERY_EXPAND` | `false` | Set `true` to enable Gemini-backed query expansion |
| `AGENTRAG_COLLECTION` | `documents` | Active Qdrant collection name |
| `AGENTRAG_INGEST_TIMEOUT` | `300` | Max seconds per file ingestion |
| `AGENTRAG_MAX_FILE_SIZE_MB` | `100` | Max file size in MB (reject with actionable error above this) |

---

## MCP Tools

All tools are available natively in Claude — no special prompting required.

| Tool | Description |
|------|-------------|
| `ingest_file` | Ingest a single local file into the vector store |
| `ingest_directory` | Bulk ingest all supported files in a directory |
| `ingest_url` | Fetch a web page and ingest its text content |
| `search_documents` | Semantic search over all ingested documents |
| `search_by_metadata` | Filter sources by metadata without a semantic query |
| `search_multi` | Search with multiple queries and deduplicate results |
| `list_sources` | List all ingested sources with metadata summary |
| `get_document` | Retrieve the full reconstructed text of a source |
| `delete_source` | Remove a source and all its vector chunks |
| `plan_query` | Decompose a complex query into focused sub-queries |
| `evaluate_chunks` | Score each chunk's relevance to the original query |

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
| `.xlsx` | Spreadsheet | `pip install agentrag[office]` |
| `.pptx` | Presentation | `pip install agentrag[office]` |
| `.epub` | eBook | `pip install agentrag[ebooks]` |
| `.mobi` | eBook | `pip install agentrag[ebooks]` |
| `.srt`, `.vtt` | Subtitles | `pip install agentrag[web]` |
| URL | Web page | `pip install agentrag[web]` |

Install all optional types at once:

```bash
pip install agentrag[all]
```

---

## Development Setup

```bash
git clone https://github.com/SARAMALI15792/AgentRAG
cd AgentRAG
uv pip install -e ".[dev,office,ebooks,web]"
uv run pytest --tb=short
```

A pre-commit hook runs `black`, `ruff`, and `mypy` automatically on every commit.
