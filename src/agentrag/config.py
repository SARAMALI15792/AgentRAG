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
    embed_model: str = "all-MiniLM-L6-v2"
    vector_dim: int = 384  # must match embed_model output dimension

    # Chunking
    chunk_size: int = 512  # tokens per chunk
    chunk_overlap: int = 64  # overlapping tokens between consecutive chunks

    # Server (used from Phase 2 onward)
    port: int = 8000
    transport: str = "stdio"

    # Phase 3+ features — defined here so Settings is complete across all phases
    rerank: bool = False
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    query_expand: bool = False

    def model_post_init(self, __context: Any) -> None:
        """Create data_dir on disk if it does not already exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
