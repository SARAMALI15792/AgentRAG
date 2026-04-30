# AgentRAG Architecture

AgentRAG is an Agentic RAG MCP Server designed to give Claude persistent, private memory over local documents.

## Core Components

### Ingestion Pipeline

The ingestion pipeline follows a strict sequence: read, chunk, embed, persist.

- **reader.py** converts local files into `RawDocument` objects.
- **chunker.py** splits text using sliding-window tokenization (512 tokens, 64 overlap).
- **embedder.py** generates sentence-transformer embeddings in batches.
- **pipeline.py** orchestrates the full sequence and reports an `IngestResult`.

### Vector Store

All interactions with Qdrant are mediated exclusively through `store/qdrant.py`.
This is the only file permitted to import `qdrant_client`. The store runs embedded
(in-process) so no Docker installation is required.

### MCP Server

The MCP server exposes seven tools callable from Claude Desktop via stdio or HTTP.
Tool handlers in `server/tools.py` are thin delegates — they contain no business logic.

## Design Principles

- Local first: everything works offline without external API calls.
- Separation of concerns: ingestion and retrieval logic are in separate packages.
- Zero vendor lock-in: the embedding model and vector store are swappable via config.
