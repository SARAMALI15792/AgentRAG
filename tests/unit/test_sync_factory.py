"""Unit tests for get_sync_backend factory function."""

from __future__ import annotations

import pytest

from agentrag.config import Settings


def _make_settings(**kwargs: object) -> Settings:
    """Create Settings with sync vars overridden."""
    return Settings(
        sync_backend=str(kwargs.get("backend", "local")),
        sync_local_dir=str(kwargs.get("local_dir", "~/.agentrag/backups")),
        sync_endpoint=str(kwargs.get("endpoint", "")),
        sync_key=str(kwargs.get("key", "")),
        sync_prefix=str(kwargs.get("prefix", "agentrag/")),
    )  # type: ignore[call-arg]


def test_local_backend_returned_for_local(tmp_path: object) -> None:
    """AGENTRAG_SYNC_BACKEND=local returns LocalSyncBackend."""
    from agentrag.sync.factory import get_sync_backend
    from agentrag.sync.local import LocalSyncBackend

    settings = _make_settings(backend="local", local_dir=str(tmp_path))
    from unittest.mock import MagicMock

    from agentrag.store.qdrant import QdrantStore

    backend = get_sync_backend(settings, store=MagicMock(spec=QdrantStore))
    assert isinstance(backend, LocalSyncBackend)


def test_s3_backend_returned_for_s3() -> None:
    """AGENTRAG_SYNC_BACKEND=s3 returns S3SyncBackend."""
    from unittest.mock import MagicMock

    from cryptography.fernet import Fernet

    from agentrag.store.qdrant import QdrantStore
    from agentrag.sync.cloud import S3SyncBackend
    from agentrag.sync.factory import get_sync_backend

    key = Fernet.generate_key().decode()
    settings = _make_settings(backend="s3", key=key, endpoint="my-bucket")
    backend = get_sync_backend(settings, store=MagicMock(spec=QdrantStore))
    assert isinstance(backend, S3SyncBackend)


def test_unknown_backend_raises_value_error() -> None:
    """Unknown AGENTRAG_SYNC_BACKEND value raises ValueError with helpful message."""
    from unittest.mock import MagicMock

    from agentrag.store.qdrant import QdrantStore
    from agentrag.sync.factory import get_sync_backend

    settings = _make_settings(backend="gcs")
    with pytest.raises(ValueError, match="Unsupported sync backend"):
        get_sync_backend(settings, store=MagicMock(spec=QdrantStore))


def test_s3_missing_key_raises_value_error() -> None:
    """S3 backend with empty AGENTRAG_SYNC_KEY raises ValueError."""
    from unittest.mock import MagicMock

    from agentrag.store.qdrant import QdrantStore
    from agentrag.sync.factory import get_sync_backend

    settings = _make_settings(backend="s3", key="", endpoint="my-bucket")
    with pytest.raises(ValueError, match="AGENTRAG_SYNC_KEY"):
        get_sync_backend(settings, store=MagicMock(spec=QdrantStore))
