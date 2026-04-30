# Tech Stack

All library choices are locked unless a change is approved through the normal
file-operation protocol (Article IV of the constitution). Adding a new
dependency requires user approval before it appears in `pyproject.toml`.

---

## Runtime Stack

| Layer | Library / Tool | Version | Rationale |
|---|---|---|---|
| Language | Python | 3.12+ | Structural pattern matching, `tomllib`, typing improvements. Minimum enforced in `pyproject.toml`. |
| MCP server | `mcp` (official Python SDK) | ==1.27.0 (pinned exact) | stdio and HTTP transports. First-class tool registration. Pin the version — the MCP SDK changes frequently. **Phase 2 note:** FastMCP requires `@asynccontextmanager` lifespan hook for shared resource initialization (Settings, QdrantStore). This pattern is mandatory for all FastMCP apps. |
| HTTP server | FastAPI | 0.136.x | Async, minimal, schema-first. Powers HTTP transport for the MCP server. |
| ASGI server | Uvicorn | 0.46.x | Production-grade ASGI runner for FastAPI. |
| Vector store | `qdrant-client` | 1.17.x | Embedded mode: Qdrant runs in-process, no Docker required. Persistent to disk. |
| Embeddings | `sentence-transformers` | 3.x | Local embedding inference. Default model: `all-MiniLM-L6-v2` (fast, small, accurate). The chunker must tokenize using the same model's `AutoTokenizer` (bundled with `transformers`, already a transitive dependency of `sentence-transformers`) so chunk token counts exactly match what the embedder sees. Do not use character counts or `tiktoken` for chunk sizing. |
| LLM (cloud) | `google-genai` (Gemini API) | 1.x | Google Gemini 2.0 Flash via the official `google-genai` Python SDK. Free tier, generous quota, no local setup. Used for query decomposition and chunk evaluation in Phase 4. Do not add any Gemini calls until Phase 4 begins. |
| PDF parsing | `pymupdf` (fitz) | 1.24.x | Fastest Python PDF parser. Handles complex layouts, embedded images, multi-column text. |
| DOCX parsing | `python-docx` | 1.1.x | Phase 3. Iterate `doc.paragraphs`, filter blanks, join with `\n`. |
| HTML parsing | `beautifulsoup4` | 4.12.x | Phase 3. `html.parser` backend. Decompose boilerplate tags before `get_text()`. |
| Settings | `pydantic-settings` | 2.x | Typed settings from env vars and `.env` files. Powers `src/agentrag/config.py`. |
| CLI | `typer` | 0.12.x | Builds `agentrag serve` and `agentrag ingest` CLI commands from type-annotated functions. |

---

## Developer Tooling

| Tool | Version | Role |
|---|---|---|
| Black | 25.x | Code formatter. `line-length = 88`. 25.x introduces the 2026 stable style — use this series for all formatting. |
| Ruff | 0.15.x | Linter and import sorter. Extends Black config. 0.15.x adds significant new rules over 0.4.x — pin to `0.15.x` floor. |
| mypy | 1.10.x | Static type checker. `--strict` mode. Minimum 1.10; pin exact version in `pyproject.toml`. |
| pytest | 8.x | Test runner. Only test framework permitted. |
| pytest-asyncio | 1.3.x | Async test support for FastAPI endpoints. **Breaking change from 0.x:** version 1.x changed the default mode and deprecated several fixture patterns. Must be configured with `asyncio_mode = "auto"` in `pyproject.toml` under `[tool.pytest.ini_options]`. Do not use 0.x patterns (`@pytest.mark.asyncio` decorator, `event_loop` fixture) — they are removed in 1.x. **Phase 2 note:** Integration tests failed until this config was added. |
| pytest-cov | 5.x | Coverage reporting. |
| hatchling | latest | Build backend for PyPI packaging. |
| httpx | 0.27.x | Async HTTP test client. Required by `pytest-asyncio` integration tests against the FastAPI server. Must be listed as a dev dependency, not a runtime dependency. **Phase 2 note:** Used `httpx.ASGITransport` for testing FastAPI app without network calls. |

---

## Packaging

| Setting | Value |
|---|---|
| Build backend | `hatchling` |
| Package name | `agentrag` |
| Entry point | `agentrag = agentrag.cli:app` |
| Python requires | `>=3.12` |
| Distribution | PyPI (`pip install agentrag`) + `uvx agentrag serve` |

---

## Logging

All structured logging in this project uses Python's standard `logging` module.
No third-party logging library (structlog, loguru, etc.) is permitted without
explicit approval.

| Rule | Detail |
|------|--------|
| Logger per module | Each module calls `logging.getLogger(__name__)` at module level. |
| Level | `INFO` by default. `DEBUG` reserved for verbose tracing (embedding times, chunk counts). |
| No `print()` | All observable output goes through `logging`. `print()` is forbidden in production code paths. |
| Caller responsibility | The CLI (`cli.py`) is responsible for calling `logging.basicConfig()`. Library code never configures the root logger. |

---

## Explicitly Excluded Libraries

These libraries are **not permitted** in this codebase. Adding them requires
amending this spec with user approval.

| Library | Reason for exclusion |
|---|---|
| LangChain | Unnecessary abstraction for our narrow scope. Hides what RAG is actually doing. |
| LlamaIndex | Same reason as LangChain. We own the pipeline. |
| OpenAI SDK | All embeddings are local. No external API dependency in core path. |
| `unittest` | `pytest` only. `unittest` is not permitted. |

---

## Environment Variables

All configuration is loaded via `pydantic-settings` from environment or `.env`:

| Variable | Default | Description |
|---|---|---|
| `AGENTRAG_DATA_DIR` | `~/.agentrag` | Root directory for Qdrant data and config |
| `AGENTRAG_EMBED_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | sentence-transformers model name. Must use the full `{org}/{model}` HuggingFace path — the short name fails HuggingFace auth. |
| `AGENTRAG_VECTOR_DIM` | `384` | Output dimension of the embedding model. Must match the Qdrant collection `vector_size`. If the embed model is changed, this value must be updated and the Qdrant collection recreated. |
| `AGENTRAG_CHUNK_SIZE` | `512` | Token chunk size for splitting |
| `AGENTRAG_CHUNK_OVERLAP` | `64` | Token overlap between chunks |
| `AGENTRAG_PORT` | `8000` | HTTP port when using HTTP transport |
| `AGENTRAG_TRANSPORT` | `stdio` | `stdio` or `http` |
| `AGENTRAG_RERANK` | `false` | Set to `true` to activate cross-encoder re-ranking (Phase 5+). Identity reranker is used when `false`. |
| `AGENTRAG_GOOGLE_API_KEY` | _(required for Phase 4)_ | Google Gemini API key. Obtain free from https://aistudio.google.com/. Used by `query_planner.py` and `evaluator.py`. If missing or invalid, both modules degrade gracefully — retrieval is never blocked. |
| `AGENTRAG_GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model name for query decomposition and chunk evaluation. Any model available on the free tier is valid. |
| `AGENTRAG_QUERY_EXPAND` | `false` | Set to `true` to enable Gemini-backed query expansion in `plan_query`. When `false`, `plan_query` returns the original query unchanged without calling Gemini. |
