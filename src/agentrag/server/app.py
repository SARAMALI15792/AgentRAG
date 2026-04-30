"""FastAPI app with MCP SDK tool registration."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from agentrag.config import Settings
from agentrag.server import tools
from agentrag.store.qdrant import QdrantStore


@dataclass
class AppContext:
    """Application context with shared resources."""

    settings: Settings
    store: QdrantStore


@asynccontextmanager
async def app_lifespan(mcp: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle — initialize resources at startup."""
    settings = Settings()
    store = QdrantStore(settings)

    try:
        yield AppContext(settings=settings, store=store)
    finally:
        # Cleanup if needed (Qdrant embedded client closes automatically)
        pass


def create_app() -> tuple[FastAPI, FastMCP]:
    """Create FastAPI app with MCP server mounted."""
    # Create MCP server with lifespan
    mcp = FastMCP("AgentRAG", lifespan=app_lifespan)

    # Register all 7 MCP tools
    @mcp.tool()
    def ingest_file(file_path: str) -> dict[str, Any]:
        """Ingest a single file into the vector store."""
        result = tools.ingest_file(file_path)
        return {
            "source_id": result.source_id,
            "filename": result.filename,
            "chunk_count": result.chunk_count,
            "status": result.status,
            "error": result.error,
        }

    @mcp.tool()
    def ingest_directory(directory_path: str) -> list[dict[str, Any]]:
        """Ingest all supported files in a directory recursively."""
        results = tools.ingest_directory(directory_path)
        return [
            {
                "source_id": r.source_id,
                "filename": r.filename,
                "chunk_count": r.chunk_count,
                "status": r.status,
                "error": r.error,
            }
            for r in results
        ]

    @mcp.tool()
    def search_documents(query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search documents by semantic similarity."""
        results = tools.search_documents(query, top_k)
        return [
            {
                "chunk_id": r.chunk_id,
                "source_id": r.source_id,
                "filename": r.filename,
                "text": r.text,
                "score": r.score,
                "metadata": r.metadata,
            }
            for r in results
        ]

    @mcp.tool()
    def search_by_metadata(filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Search sources by metadata filters."""
        results = tools.search_by_metadata(filters)
        return [
            {
                "source_id": s.source_id,
                "filename": s.filename,
                "chunk_count": s.chunk_count,
                "metadata": s.metadata,
                "ingested_at": s.ingested_at,
            }
            for s in results
        ]

    @mcp.tool()
    def list_sources() -> list[dict[str, Any]]:
        """List all ingested sources."""
        results = tools.list_sources()
        return [
            {
                "source_id": s.source_id,
                "filename": s.filename,
                "chunk_count": s.chunk_count,
                "metadata": s.metadata,
                "ingested_at": s.ingested_at,
            }
            for s in results
        ]

    @mcp.tool()
    def get_document(source_id: str) -> dict[str, Any]:
        """Retrieve full document text by source_id."""
        result = tools.get_document(source_id)
        return {
            "source_id": result.source_id,
            "filename": result.filename,
            "full_text": result.full_text,
            "metadata": result.metadata,
        }

    @mcp.tool()
    def delete_source(source_id: str) -> dict[str, Any]:
        """Delete all chunks for a source."""
        result = tools.delete_source(source_id)
        return {
            "source_id": result.source_id,
            "chunks_deleted": result.chunks_deleted,
            "status": result.status,
        }

    @mcp.tool()
    def ingest_url(url: str) -> dict[str, Any]:
        """Fetch a web page and ingest its text content."""
        result = tools.ingest_url(url)
        return {
            "source_id": result.source_id,
            "filename": result.filename,
            "chunk_count": result.chunk_count,
            "status": result.status,
            "error": result.error,
        }

    # Create FastAPI app and mount MCP SSE transport
    app = FastAPI(title="AgentRAG MCP Server")

    @app.get("/health")
    def health() -> dict[str, str]:
        """Health check endpoint for integration tests."""
        return {"status": "ok"}

    # Mount MCP SSE app at /sse
    app.mount("/sse", mcp.sse_app())

    return app, mcp
