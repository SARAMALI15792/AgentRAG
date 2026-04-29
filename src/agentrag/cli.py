"""CLI entry point for agentrag commands."""

from __future__ import annotations

import logging
from pathlib import Path

import typer

from agentrag.config import Settings
from agentrag.ingestion.pipeline import ingest
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
            f"✓ Ingested {result.filename}: {result.chunk_count} chunks "
            f"(source_id: {result.source_id})"
        )
    else:
        typer.echo(f"✗ Ingestion failed: {result.error}", err=True)
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


if __name__ == "__main__":
    app()
