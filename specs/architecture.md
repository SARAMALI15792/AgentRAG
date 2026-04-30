# Architecture

---

## Directory Layout

```
agentrag/
├── src/
│   └── agentrag/
│       ├── __init__.py
│       ├── cli.py                  # typer app: `agentrag serve`, `agentrag ingest`, `agentrag list`
│       ├── config.py               # pydantic-settings Settings dataclass
│       ├── types.py                # all domain dataclasses — single source of truth
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── reader.py           # file path → RawDocument
│       │   ├── chunker.py          # RawDocument → List[Chunk]
│       │   ├── embedder.py         # List[Chunk] → List[EmbeddedChunk]
│       │   └── pipeline.py         # orchestrates reader → chunker → embedder → store
│       ├── retrieval/
│       │   ├── __init__.py
│       │   ├── searcher.py         # query string → List[SearchResult]
│       │   ├── reranker.py         # List[SearchResult] → List[SearchResult] (re-ranked)
│       │   ├── query_planner.py    # str → QueryPlan (Gemini-backed, graceful degrade)
│       │   └── evaluator.py        # (query, results) → EvaluationReport (Gemini-backed)
│       ├── store/
│       │   ├── __init__.py
│       │   └── qdrant.py           # all Qdrant interactions — no other module imports qdrant_client
│       └── server/
│           ├── __init__.py
│           ├── app.py              # FastAPI app + MCP SDK registration
│           └── tools.py            # MCP tool handlers — delegation only, no business logic
├── tests/
│   ├── conftest.py                 # shared fixtures: mock store, mock embedder, Settings, sample chunks
│   ├── fixtures/
│   │   ├── sample.txt              # plain-text ingest fixture (≥ 600 words)
│   │   └── sample.pdf              # single-page PDF ingest fixture (committed binary)
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_store.py
│   │   ├── test_reader.py
│   │   ├── test_chunker.py
│   │   ├── test_embedder.py
│   │   ├── test_pipeline.py
│   │   ├── test_searcher.py
│   │   ├── test_tools.py
│   │   ├── test_query_planner.py
│   │   ├── test_evaluator.py
│   │   └── test_agentic_tools.py
│   └── integration/
│       ├── test_pipeline.py
│       ├── test_server.py
│       └── test_agentic_retrieval.py
├── scripts/
│   └── verify_phase1.sh            # runnable exit gate: pytest + mypy + CLI smoke test
├── .github/
│   └── workflows/
│       └── ci.yml                  # lint + typecheck + test on every push to main
├── specs/                          # Reference documents — no source code here
│   ├── mission.md
│   ├── tech-stack.md
│   ├── roadmap.md
│   └── architecture.md             # ← this file
├── pyproject.toml
├── .python-version                 # pins 3.12
└── CLAUDE.md                       # Project constitution
```

---

## Domain Types

```python
# All types live in src/agentrag/types.py (created in Phase 1)

@dataclass
class RawDocument:
    source_id: str          # stable hash of file path
    filename: str
    text: str
    metadata: dict[str, Any]

@dataclass
class Chunk:
    chunk_id: str           # f"{source_id}_{index}"
    source_id: str
    text: str
    start_char: int
    end_char: int
    index: int

@dataclass
class EmbeddedChunk:
    chunk_id: str
    source_id: str
    text: str
    vector: list[float]
    metadata: dict[str, Any]

@dataclass
class SearchResult:
    chunk_id: str
    source_id: str
    filename: str
    text: str
    score: float
    metadata: dict[str, Any]

@dataclass
class SourceInfo:
    source_id: str
    filename: str
    chunk_count: int
    metadata: dict[str, Any]
    ingested_at: str        # ISO 8601

@dataclass
class IngestResult:
    source_id: str
    filename: str
    chunk_count: int
    status: Literal["ok", "error"]
    error: str | None = None

@dataclass
class DeleteResult:
    source_id: str
    chunks_deleted: int
    status: Literal["ok", "not_found", "error"]

@dataclass
class DocumentContent:
    source_id: str
    filename: str
    full_text: str          # chunks joined in index order
    metadata: dict[str, Any]

# Phase 3 — Agentic Retrieval types

@dataclass
class QueryPlan:
    original_query: str
    sub_queries: list[str]  # 1–4 focused sub-questions; always includes original

@dataclass
class ChunkScore:
    chunk_id: str
    source_id: str
    score: float            # 0.0 (irrelevant) → 1.0 (directly answers query)
    reason: str             # one-sentence explanation

@dataclass
class EvaluationReport:
    query: str
    scored_chunks: list[ChunkScore]
    sufficient: bool        # True if any chunk scores ≥ 0.7
    suggested_queries: list[str]  # alternative queries when not sufficient
```

All domain types live exclusively in `src/agentrag/types.py`. No other module
defines dataclasses for cross-module data. Every import of these types must
come from `agentrag.types`.

---

## source_id Contract

`source_id` is a stable, collision-resistant identifier for a file. It is
computed once in `reader.py` and must be reproduced identically by any code
that needs to reference the same source.

```python
import hashlib
from pathlib import Path

def make_source_id(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]
```

Rules:
- Always use the **resolved absolute path** (symlinks expanded, `..` collapsed).
- Truncate to the first 16 hex characters (64-bit collision resistance —
  sufficient for a single-user local store).
- Never use the filename alone — two files with the same name in different
  directories must produce different `source_id` values.
- `store/qdrant.py` uses `source_id` as the partition key for deduplication.
  Any change to this function invalidates all stored data.

---

## Data Flow

### Ingestion Path

```
User file (PDF / MD / TXT)
  │
  ▼
reader.py
  RawDocument(source_id, filename, text, metadata)
  │
  ▼
chunker.py
  List[Chunk]  — sliding window, 512 tokens, 64 overlap
  │
  ▼
embedder.py
  List[EmbeddedChunk]  — sentence-transformers local inference
  │
  ▼
store/qdrant.py
  upsert(chunks)  — Qdrant embedded, persisted to ~/.agentrag/qdrant/
```

### Retrieval Path

```
Claude calls search_documents(query, top_k, filters)
  │
  ▼
server/tools.py   (thin handler — no logic)
  │
  ▼
retrieval/searcher.py
  1. embed query via embedder.py
  2. qdrant.query(vector, top_k, filters)
  3. reranker.rerank(results)  [identity in Phase 2, cross-encoder in Phase 4]
  │
  ▼
List[SearchResult]  → returned to Claude
```

---

## MCP Tool Contracts

All tools are registered on the MCP server. Claude calls them natively.

---

### `ingest_file`

```
Purpose : Ingest a single local file into the vector store.
Input   : path (str), metadata (dict, optional)
Output  : IngestResult
Errors  : FileNotFoundError if path does not exist
          ValueError if file type is unsupported
```

---

### `ingest_directory`

```
Purpose : Bulk ingest all supported files in a directory.
Input   : path (str)
          recursive (bool, default True)
          file_types (list[str], default [".pdf", ".md", ".txt"])
          metadata (dict, optional)
Output  : list[IngestResult]  — one per file attempted
Notes   : Skips unsupported file types silently (logged).
          Re-ingesting an existing source updates its chunks.
```

---

### `search_documents`

```
Purpose : Semantic search over all ingested documents.
Input   : query (str)
          top_k (int, default 5)
          filters (dict, optional)  — metadata key/value pairs
Output  : list[SearchResult]  — ranked by score descending
Notes   : Returns empty list (not error) if no results found.
```

---

### `search_by_metadata`

```
Purpose : Filter sources by metadata without a semantic query.
Input   : filters (dict)  — at least one key required
Output  : list[SourceInfo]
Errors  : ValueError if filters is empty
```

---

### `list_sources`

```
Purpose : List all ingested sources with metadata summary.
Input   : (none)
Output  : list[SourceInfo]
Notes   : Returns empty list if no sources have been ingested.
```

---

### `get_document`

```
Purpose : Retrieve the full reconstructed text of an ingested source.
Input   : source_id (str)
Output  : DocumentContent(source_id, filename, full_text, metadata)
Errors  : ValueError if source_id not found
Notes   : Reconstructs text by joining all chunks in order.
          May differ slightly from original due to chunking boundaries.
```

---

### `delete_source`

```
Purpose : Remove a source and all its vector chunks from the store.
Input   : source_id (str)
Output  : DeleteResult
Errors  : Returns status="not_found" (not exception) if source_id unknown
Notes   : This operation is irreversible. The MCP tool handler must
          surface the DeleteResult to Claude so the user is informed.
```

---

## Runtime Configuration

```
agentrag serve --data-dir ~/.agentrag --transport stdio
```

| Flag | Default | Description |
|---|---|---|
| `--data-dir` | `~/.agentrag` | Root for Qdrant data and settings |
| `--transport` | `stdio` | `stdio` (Claude Desktop) or `http` |
| `--port` | `8000` | HTTP port (ignored for stdio) |
| `--embed-model` | `all-MiniLM-L6-v2` | sentence-transformers model name |

---

## Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or the equivalent path on Windows/Linux:

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

For zero-install (`uvx`):

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

## Dependency Direction

```
cli.py
  └─▶ ingestion/pipeline.py   ─▶ reader, chunker, embedder, store
  └─▶ server/app.py

server/tools.py
  └─▶ ingestion/pipeline.py
  └─▶ retrieval/searcher.py   ─▶ embedder, store
  └─▶ store/qdrant.py

retrieval/searcher.py      ──▶ store/, ingestion/embedder.py (query embed only)
retrieval/query_planner.py ──▶ (external: google-genai SDK only)
retrieval/evaluator.py     ──▶ (external: google-genai SDK only)
ingestion/                 ──▶ store/

store/ ──▶ (nothing internal — only qdrant_client)
```

**Rule:** Dependencies only flow downward. Nothing in `store/` or `retrieval/`
imports from `ingestion/` or `server/`. Nothing in `ingestion/` imports from
`retrieval/` or `server/`.
