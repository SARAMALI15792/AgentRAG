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
│       │   ├── reader.py           # file path → RawDocument (dispatches to reader registry)
│       │   ├── reader_registry.py  # Phase 3B: extension → reader callable mapping
│       │   ├── readers/            # Phase 3B+: per-format reader modules
│       │   │   ├── __init__.py
│       │   │   ├── office.py       # .xlsx, .pptx, .csv readers
│       │   │   ├── ebooks.py       # .epub, .mobi readers
│       │   │   ├── structured.py   # .json, .yaml, .xml, .toml readers
│       │   │   ├── media.py        # .srt, .vtt subtitle readers
│       │   │   ├── email.py        # .eml, .mbox readers
│       │   │   └── web.py          # URL fetcher → HTML → text
│       │   ├── chunker.py          # RawDocument → List[Chunk]
│       │   ├── embedder.py         # List[Chunk] → List[EmbeddedChunk]
│       │   └── pipeline.py         # orchestrates reader → chunker → embedder → store
│       ├── retrieval/
│       │   ├── __init__.py
│       │   ├── searcher.py         # query string → List[SearchResult]
│       │   ├── reranker.py         # List[SearchResult] → List[SearchResult] (re-ranked)
│       │   ├── streaming.py        # Phase 7: async generator yielding SearchResult
│       │   ├── query_planner.py    # str → QueryPlan (Gemini-backed, graceful degrade)
│       │   └── evaluator.py        # (query, results) → EvaluationReport (Gemini-backed)
│       ├── store/
│       │   ├── __init__.py
│       │   └── qdrant.py           # all Qdrant interactions — no other module imports qdrant_client
│       ├── sync/                   # Phase 8: cloud sync (optional)
│       │   ├── __init__.py
│       │   ├── base.py             # SyncBackend protocol
│       │   ├── local.py            # local directory backup
│       │   └── cloud.py            # cloud provider implementation
│       └── server/
│           ├── __init__.py
│           ├── app.py              # FastAPI app + MCP SDK registration
│           └── tools.py            # MCP tool handlers — delegation only, no business logic
├── tests/
│   ├── conftest.py                 # shared fixtures: mock store, mock embedder, Settings, sample chunks
│   ├── fixtures/
│   │   ├── sample.txt              # plain-text ingest fixture (≥ 600 words)
│   │   ├── sample.pdf              # single-page PDF ingest fixture (committed binary)
│   │   ├── sample.docx             # Word document fixture
│   │   ├── sample.html             # HTML page fixture
│   │   ├── sample.py               # Python source fixture
│   │   ├── sample.ipynb            # Jupyter notebook fixture
│   │   ├── sample.md               # Markdown fixture
│   │   ├── sample.xlsx             # Phase 3B: Excel spreadsheet fixture
│   │   ├── sample.pptx             # Phase 3B: PowerPoint fixture
│   │   ├── sample.csv              # Phase 3B: CSV fixture
│   │   ├── sample.epub             # Phase 3B: EPUB fixture
│   │   ├── sample.json             # Phase 3B: JSON fixture
│   │   ├── sample.yaml             # Phase 3B: YAML fixture
│   │   ├── sample.xml              # Phase 3B: XML fixture
│   │   ├── sample.toml             # Phase 3B: TOML fixture
│   │   ├── sample.srt              # Phase 3C: SRT subtitle fixture
│   │   └── sample.eml              # Phase 3C: Email fixture
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_store.py
│   │   ├── test_reader.py
│   │   ├── test_reader_registry.py # Phase 3B: plugin registry tests
│   │   ├── test_chunker.py
│   │   ├── test_embedder.py
│   │   ├── test_pipeline.py
│   │   ├── test_searcher.py
│   │   ├── test_tools.py
│   │   ├── test_query_planner.py
│   │   ├── test_evaluator.py
│   │   ├── test_agentic_tools.py
│   │   ├── test_streaming.py       # Phase 7: streaming retrieval tests
│   │   └── test_url_reader.py      # Phase 3C: URL reader tests
│   └── integration/
│       ├── test_pipeline.py
│       ├── test_server.py
│       ├── test_agentic_retrieval.py
│       ├── test_extended_ingestion_3b.py  # Phase 3B: office/ebook/structured tests
│       ├── test_search_filters.py         # Phase 5: metadata filter tests
│       └── test_concurrent_upsert.py      # Phase 5: concurrency tests
├── scripts/
│   ├── verify_phase1.sh            # runnable exit gate: pytest + mypy + CLI smoke test
│   ├── verify_phase3b.sh           # Phase 3B exit gate
│   ├── verify_phase3c.sh           # Phase 3C exit gate
│   ├── verify_phase4.sh            # Phase 4 exit gate
│   ├── verify_phase5.sh            # Phase 5 exit gate
│   ├── verify_phase6.sh            # Phase 6 exit gate
│   ├── verify_phase7.sh            # Phase 7 exit gate
│   ├── verify_phase8.sh            # Phase 8 exit gate
│   └── benchmark_retrieval.py      # Phase 5: retrieval quality benchmark
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

## Reader Plugin Registry

Phase 3B introduces a reader plugin registry that replaces the `if/elif`
chain in `reader.py`. This is the sole exception to the "no premature
abstraction" rule (Article IV.5) — justified by the roadmap committing to
15+ file types.

### Registry Design

```python
# src/agentrag/ingestion/reader_registry.py

ReaderFn = Callable[[Path], str]
_registry: dict[str, ReaderFn] = {}

def register(extensions: list[str], reader: ReaderFn) -> None:
    """Register a reader function for one or more file extensions."""
    for ext in extensions:
        _registry[ext.lower()] = reader

def get_reader(extension: str) -> ReaderFn:
    """Look up the reader for an extension. Raises ValueError if unsupported."""
    reader = _registry.get(extension.lower())
    if reader is None:
        raise ValueError(f"Unsupported file type: {extension}")
    return reader

def supported_extensions() -> set[str]:
    """Return all registered extensions."""
    return set(_registry.keys())
```

### Rules

- Every reader function has signature `(Path) -> str` — returns extracted text.
- `reader.py` calls `get_reader(suffix)` then wraps result in `RawDocument`.
- New file type support = new reader module + `register()` call. No changes
  to `reader.py`, `pipeline.py`, or `tools.py`.
- Reader modules in `readers/` are auto-imported by `reader_registry.py` on
  first use (lazy import to avoid loading unused dependencies).
- Optional dependency readers (office, ebook) must catch `ImportError` and
  raise a clear message: `"Install agentrag[office] for .xlsx support"`.

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

# Phase 4 — Agentic Retrieval types

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
- **URL sources:** For URL ingestion (Phase 3C), `source_id` is computed from
  the normalized URL string (lowercase scheme + host, stripped trailing slash)
  instead of a file path. The `make_source_id` contract still applies — the
  input is just a URL string instead of a `Path.resolve()` string.

---

## Data Flow

### Ingestion Path

```
User file (PDF / DOCX / XLSX / EPUB / JSON / URL / ...)
  │
  ▼
reader_registry.py → dispatches to registered reader
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
                     Collection name from settings.collection (default: "documents")
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
  3. reranker.rerank(results)  [identity in Phase 2, cross-encoder in Phase 5]
  │
  ▼
List[SearchResult]  → returned to Claude
```

### Agentic Retrieval Path (Phase 4)

```
Claude calls plan_query(query)
  │
  ▼
query_planner.py → QueryPlan(original, sub_queries)
  │
  ▼
Claude calls search_multi(sub_queries, top_k)
  │
  ▼
searcher.py × N queries → deduplicate by chunk_id → merged results
  │
  ▼
Claude calls evaluate_chunks(query, results)
  │
  ▼
evaluator.py → EvaluationReport(scored_chunks, sufficient, suggested_queries)
  │
  ▼
If not sufficient: Claude calls search_multi(suggested_queries) → loop
```

### Streaming Retrieval Path (Phase 7)

```
Claude calls search_stream(query, top_k)
  │
  ▼
retrieval/streaming.py
  async generator: yield SearchResult as each chunk scores
  │
  ▼
Results stream to Claude as they arrive (if MCP SDK supports streaming)
Fallback: batch mode identical to search_documents
```

---

## MCP Tool Contracts

All tools are registered on the MCP server. Claude calls them natively.

### Phase 1-3A Tools (Shipped)

---

#### `ingest_file`

```
Purpose : Ingest a single local file into the vector store.
Input   : path (str), metadata (dict, optional)
Output  : IngestResult
Errors  : FileNotFoundError if path does not exist
          ValueError if file type is unsupported
```

---

#### `ingest_directory`

```
Purpose : Bulk ingest all supported files in a directory.
Input   : path (str)
          recursive (bool, default True)
          file_types (list[str], default: all registered extensions)
          metadata (dict, optional)
Output  : list[IngestResult]  — one per file attempted
Notes   : Skips unsupported file types silently (logged).
          Re-ingesting an existing source updates its chunks.
          Phase 3B+: uses reader_registry.supported_extensions() for glob list.
```

---

#### `search_documents`

```
Purpose : Semantic search over all ingested documents.
Input   : query (str)
          top_k (int, default 5)
          filters (dict, optional)  — metadata key/value pairs
Output  : list[SearchResult]  — ranked by score descending
Notes   : Returns empty list (not error) if no results found.
```

---

#### `search_by_metadata`

```
Purpose : Filter sources by metadata without a semantic query.
Input   : filters (dict)  — at least one key required
Output  : list[SourceInfo]
Errors  : ValueError if filters is empty
```

---

#### `list_sources`

```
Purpose : List all ingested sources with metadata summary.
Input   : (none)
Output  : list[SourceInfo]
Notes   : Returns empty list if no sources have been ingested.
```

---

#### `get_document`

```
Purpose : Retrieve the full reconstructed text of an ingested source.
Input   : source_id (str)
Output  : DocumentContent(source_id, filename, full_text, metadata)
Errors  : ValueError if source_id not found
Notes   : Reconstructs text by joining all chunks in order.
          May differ slightly from original due to chunking boundaries.
```

---

#### `delete_source`

```
Purpose : Remove a source and all its vector chunks from the store.
Input   : source_id (str)
Output  : DeleteResult
Errors  : Returns status="not_found" (not exception) if source_id unknown
Notes   : This operation is irreversible. The MCP tool handler must
          surface the DeleteResult to Claude so the user is informed.
```

---

### Phase 3C Tools (Planned)

#### `ingest_url`

```
Purpose : Fetch a web page and ingest its text content.
Input   : url (str), metadata (dict, optional)
Output  : IngestResult
Errors  : ValueError if URL is malformed
          ConnectionError if fetch fails (timeout, DNS, HTTP error)
Notes   : Requires agentrag[web] optional dependency.
          Uses httpx for fetching, BeautifulSoup for text extraction.
```

---

### Phase 4 Tools (Planned)

#### `plan_query`

```
Purpose : Decompose a complex query into focused sub-queries.
Input   : query (str)
Output  : QueryPlan(original_query, sub_queries)
Notes   : Requires AGENTRAG_GOOGLE_API_KEY. Degrades gracefully to
          single-query plan if key missing or API unreachable.
```

#### `search_multi`

```
Purpose : Search with multiple queries, deduplicate results.
Input   : queries (list[str]), top_k (int, default 5)
Output  : list[SearchResult] — deduplicated by chunk_id, highest score kept
Errors  : ValueError if queries list is empty
```

#### `evaluate_chunks`

```
Purpose : Score each chunk's relevance to the original query.
Input   : query (str), results (list[SearchResult])
Output  : EvaluationReport(scored_chunks, sufficient, suggested_queries)
Notes   : Degrades gracefully — scores 0.5, sufficient=True if API unavailable.
```

---

### Phase 7 Tools (Planned)

#### `list_collections`

```
Purpose : List all named Qdrant collections.
Input   : (none)
Output  : list[str]
```

#### `switch_collection`

```
Purpose : Set the active collection for subsequent operations.
Input   : name (str)
Output  : str — confirmation message
Errors  : ValueError if collection does not exist
```

#### `create_collection`

```
Purpose : Create a new named collection for workspace isolation.
Input   : name (str)
Output  : str — confirmation message
Errors  : ValueError if collection already exists
```

#### `search_stream`

```
Purpose : Streaming semantic search — results arrive as they score.
Input   : query (str), top_k (int, default 5)
Output  : AsyncIterator[SearchResult]
Notes   : Falls back to batch mode if MCP SDK does not support streaming.
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
| `--collection` | `documents` | Phase 7: active Qdrant collection name |

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
retrieval/streaming.py     ──▶ retrieval/searcher.py
ingestion/reader.py        ──▶ ingestion/reader_registry.py
ingestion/reader_registry.py ──▶ ingestion/readers/* (lazy import)
ingestion/                 ──▶ store/
sync/                      ──▶ store/ (snapshot access only)

store/ ──▶ (nothing internal — only qdrant_client)
```

**Rule:** Dependencies only flow downward. Nothing in `store/` or `retrieval/`
imports from `ingestion/` or `server/`. Nothing in `ingestion/` imports from
`retrieval/` or `server/`.

**New rule (Phase 3B):** Reader modules in `ingestion/readers/` must not
import from any other `agentrag` module except `agentrag.types`. They are
leaf modules — pure functions that take a `Path` and return a `str`.
