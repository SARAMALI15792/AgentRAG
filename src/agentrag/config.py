from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGENTRAG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Path.home() / ".agentrag"
    embed_model: str = "all-MiniLM-L6-v2"
    vector_dim: int = 384
    chunk_size: int = 512
    chunk_overlap: int = 64
    port: int = 8000
    transport: str = "stdio"
    rerank: bool = False
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    query_expand: bool = False

    def model_post_init(self, __context: Any) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
