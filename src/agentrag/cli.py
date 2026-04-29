"""CLI entry point for agentrag commands."""

from __future__ import annotations

import logging
from pathlib import Path

import typer
import uvicorn

from agentrag.config import Settings
from agentrag.ingestion.pipeline import ingest
from agentrag.server.app import create_app
from agentrag.store.qdrant import QdrantStore

app = typer.Typer(help="AgentRAG — Agentic RAG MCP Server")

# Configure logging once at module level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@app.command(name="ingest")
def ingest_cmd(file: Path) -> None:
    """Ingest a local file into the vector store."""
    settings = Settings()
    result = ingest(file, settings)

    if result.status == "ok":
        typer.echo(
            f"[OK] Ingested {result.filename}: {result.chunk_count} chunks "
            f"(source_id: {result.source_id})"
        )
    else:
        typer.echo(f"[ERROR] Ingestion failed: {result.error}", err=True)
        raise typer.Exit(code=1)


@app.command(name="list")
def list_cmd() -> None:
    """List all ingested sources."""
    settings = Settings()
    store = QdrantStore(settings)
    sources = store.list_sources()

    if not sources:
        typer.echo("No sources ingested yet.")
        return

    typer.echo(f"Found {len(sources)} source(s):\n")
    for source in sources:
        typer.echo(
            f"  {source.filename} ({source.chunk_count} chunks) — {source.source_id}"
        )
        typer.echo(f"    Ingested: {source.ingested_at}")


@app.command(name="serve")
def serve_cmd(
    transport: str = typer.Option("stdio", help="Transport mode: stdio or http"),
    port: int = typer.Option(8000, help="HTTP port (ignored for stdio)"),
    host: str = typer.Option("127.0.0.1", help="HTTP host (ignored for stdio)"),
) -> None:
    """Start the MCP server."""
    fastapi_app, mcp = create_app()

    if transport == "stdio":
        typer.echo("Starting MCP server in stdio mode...")
        mcp.run(transport="stdio")
    elif transport == "http":
        typer.echo(f"Starting MCP server on http://{host}:{port}")
        uvicorn.run(fastapi_app, host=host, port=port)
    else:
        typer.echo(f"[ERROR] Unknown transport: {transport}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
