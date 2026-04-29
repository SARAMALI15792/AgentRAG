from __future__ import annotations

from pathlib import Path

import pytest


def test_default_values_load(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for var in (
        "AGENTRAG_EMBED_MODEL",
        "AGENTRAG_VECTOR_DIM",
        "AGENTRAG_CHUNK_SIZE",
        "AGENTRAG_CHUNK_OVERLAP",
    ):
        monkeypatch.delenv(var, raising=False)

    from agentrag.config import Settings

    s = Settings(data_dir=tmp_path / "defaults")
    assert s.embed_model == "all-MiniLM-L6-v2"
    assert s.chunk_size == 512
    assert s.chunk_overlap == 64
    assert s.vector_dim == 384


def test_env_var_overrides_data_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    custom = tmp_path / "custom_data"
    monkeypatch.setenv("AGENTRAG_DATA_DIR", str(custom))

    from agentrag.config import Settings

    s = Settings()
    assert Path(s.data_dir) == custom


def test_data_dir_created_on_instantiation(tmp_path: Path) -> None:
    target = tmp_path / "should_be_created"
    assert not target.exists()

    from agentrag.config import Settings

    Settings(data_dir=target)
    assert target.is_dir()


def test_vector_dim_default(tmp_path: Path) -> None:
    from agentrag.config import Settings

    s = Settings(data_dir=tmp_path / "vdim")
    assert s.vector_dim == 384
