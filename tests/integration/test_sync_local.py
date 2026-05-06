"""Integration tests for LocalSyncBackend with real Qdrant embedded store."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentrag.config import Settings
from agentrag.ingestion.pipeline import ingest
from agentrag.store.qdrant import QdrantStore, _close_all_clients
from agentrag.sync.local import LocalSyncBackend


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    """Isolated settings pointing at a temp data directory."""
    return Settings(data_dir=tmp_path / "agentrag")  # type: ignore[call-arg]


@pytest.fixture()
def store(settings: Settings) -> QdrantStore:
    """Real QdrantStore backed by embedded Qdrant."""
    return QdrantStore(settings)


@pytest.fixture()
def backup_dir(tmp_path: Path) -> Path:
    """Dedicated backup directory."""
    d = tmp_path / "backups"
    d.mkdir()
    return d


@pytest.fixture(autouse=True)
def _cleanup_clients() -> None:
    """Close all cached Qdrant clients after each test."""
    yield
    _close_all_clients()


FIXTURE = Path(__file__).parent.parent / "fixtures" / "sample.txt"


def test_push_creates_snapshot_file(
    store: QdrantStore, backup_dir: Path, settings: Settings
) -> None:
    """push() creates a .snapshot file in backup_dir."""
    ingest(FIXTURE, settings)
    backend = LocalSyncBackend(store=store, backup_dir=backup_dir)
    result = backend.push()
    assert result.status == "ok", result.message
    snapshots = list(backup_dir.glob("*.snapshot"))
    assert len(snapshots) == 1


def test_push_pull_restores_data(
    store: QdrantStore, backup_dir: Path, settings: Settings
) -> None:
    """push → delete source → pull → search returns results again."""
    ingest_result = ingest(FIXTURE, settings)
    source_id = ingest_result.source_id
    backend = LocalSyncBackend(store=store, backup_dir=backup_dir)

    push_result = backend.push()
    assert push_result.status == "ok", push_result.message

    # Wipe the data so pull has something to prove
    store.delete(source_id)
    assert store.list_sources() == []

    pull_result = backend.pull()
    assert pull_result.status == "ok", pull_result.message

    sources = store.list_sources()
    assert any(s.source_id == source_id for s in sources)


def test_status_after_push(
    store: QdrantStore, backup_dir: Path, settings: Settings
) -> None:
    """status() reports snapshot_count=1 and a non-None last_push after push."""
    ingest(FIXTURE, settings)
    backend = LocalSyncBackend(store=store, backup_dir=backup_dir)
    backend.push()
    s = backend.status()
    assert s.snapshot_count == 1
    assert s.last_push is not None
    assert s.backend == "local"


def test_pull_no_snapshots_returns_error(store: QdrantStore, backup_dir: Path) -> None:
    """pull() returns SyncResult(error) when no .snapshot files exist."""
    backend = LocalSyncBackend(store=store, backup_dir=backup_dir)
    result = backend.pull()
    assert result.status == "error"
    assert "no snapshots" in result.message.lower()


def test_push_pull_idempotent(
    store: QdrantStore, backup_dir: Path, settings: Settings
) -> None:
    """Two push+pull cycles produce the same data."""
    ingest_result = ingest(FIXTURE, settings)
    source_id = ingest_result.source_id
    backend = LocalSyncBackend(store=store, backup_dir=backup_dir)

    backend.push()
    store.delete(source_id)
    backend.pull()
    after_first = store.list_sources()

    backend.push()
    store.delete(source_id)
    backend.pull()
    after_second = store.list_sources()

    assert len(after_first) == len(after_second)
