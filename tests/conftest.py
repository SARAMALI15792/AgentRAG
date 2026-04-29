from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import numpy as np
import pytest

if TYPE_CHECKING:
    from agentrag.config import Settings
    from agentrag.types import EmbeddedChunk


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    from agentrag.config import Settings

    return Settings(data_dir=tmp_path / "qdrant")


@pytest.fixture
def mock_sentence_transformer() -> MagicMock:
    mock = MagicMock()
    mock.encode.return_value = np.zeros((3, 384), dtype=np.float32)
    return mock


@pytest.fixture
def mock_qdrant_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def sample_chunks() -> list[EmbeddedChunk]:
    from agentrag.types import EmbeddedChunk

    return [
        EmbeddedChunk(
            chunk_id=f"abc_{i}",
            source_id="abc",
            text=f"Sample chunk text number {i}",
            vector=[0.0] * 384,
            metadata={},
        )
        for i in range(3)
    ]
