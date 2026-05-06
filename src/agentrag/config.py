from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_prefix="AGENTRAG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core paths and model
    data_dir: Path = Path.home() / ".agentrag"
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_dim: int = 384  # must match embed_model output dimension

    # Chunking
    chunk_size: int = 512  # tokens per chunk
    chunk_overlap: int = 64  # overlapping tokens between consecutive chunks

    # Server (used from Phase 2 onward)
    port: int = 8000
    transport: str = "stdio"

    # Phase 4+ features — defined here so Settings is complete across all phases
    rerank: bool = False
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    query_expand: bool = False
    collection: str = "documents"
    ingest_timeout: int = 300
    max_file_size_mb: int = 100

    # Phase 7 — cloud sync
    sync_backend: str = "local"  # "local" or "s3"
    sync_endpoint: str = ""  # S3 bucket name or S3-compatible endpoint URL
    sync_key: str = ""  # Fernet encryption key (base64)
    sync_local_dir: Path = Path.home() / ".agentrag" / "backups"
    sync_prefix: str = "agentrag/"  # S3 key prefix for uploaded snapshots

    def model_post_init(self, __context: Any) -> None:
        """Create data_dir on disk if it does not already exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
