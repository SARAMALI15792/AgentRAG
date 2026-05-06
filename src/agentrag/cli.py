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
from agentrag.sync.factory import get_sync_backend

app = typer.Typer(help="AgentRAG — Agentic RAG MCP Server")
sync_app = typer.Typer(help="Sync the vector store to/from a backup backend.")
app.add_typer(sync_app, name="sync")

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


@sync_app.command(name="push")
def sync_push_cmd() -> None:
    """Create a snapshot and upload it to the configured sync backend."""
    settings = Settings()
    store = QdrantStore(settings)
    backend = get_sync_backend(settings, store=store)
    result = backend.push()
    typer.echo(result.message)
    if result.status == "error":
        raise typer.Exit(code=1)


@sync_app.command(name="pull")
def sync_pull_cmd() -> None:
    """Download the latest snapshot and restore the vector store."""
    settings = Settings()
    store = QdrantStore(settings)
    backend = get_sync_backend(settings, store=store)
    result = backend.pull()
    typer.echo(result.message)
    if result.status == "error":
        raise typer.Exit(code=1)


@sync_app.command(name="status")
def sync_status_cmd() -> None:
    """Show last push/pull times and snapshot count for the sync backend."""
    settings = Settings()
    store = QdrantStore(settings)
    backend = get_sync_backend(settings, store=store)
    s = backend.status()
    typer.echo(f"Backend:        {s.backend}")
    typer.echo(f"Snapshots:      {s.snapshot_count}")
    typer.echo(f"Last push:      {s.last_push or 'never'}")
    typer.echo(f"Last pull:      {s.last_pull or 'never'}")


if __name__ == "__main__":
    app()
