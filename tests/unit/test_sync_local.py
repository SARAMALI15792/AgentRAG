"""Unit tests for LocalSyncBackend (QdrantStore mocked)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agentrag.types import SyncStatus


@pytest.fixture()
def backup_dir(tmp_path: Path) -> Path:
    """Temporary backup directory."""
    d = tmp_path / "backups"
    d.mkdir()
    return d


@pytest.fixture()
def mock_store(tmp_path: Path) -> MagicMock:
    """Mock QdrantStore with snapshot helpers."""
    store = MagicMock()
    snapshot_file = tmp_path / "snapshot_20260506T000000Z.snapshot"
    snapshot_file.write_bytes(b"fake-snapshot-data")
    store.create_snapshot.return_value = snapshot_file
    return store


@pytest.fixture()
def backend(backup_dir: Path, mock_store: MagicMock) -> object:
    """LocalSyncBackend with mocked store and backup dir."""
    from agentrag.sync.local import LocalSyncBackend

    return LocalSyncBackend(store=mock_store, backup_dir=backup_dir)


def test_push_creates_snapshot(
    backend: object, mock_store: MagicMock, backup_dir: Path
) -> None:
    """push() calls store.create_snapshot with backup_dir."""
    from agentrag.sync.local import LocalSyncBackend

    assert isinstance(backend, LocalSyncBackend)
    result = backend.push()
    mock_store.create_snapshot.assert_called_once_with(backup_dir)
    assert result.status == "ok"
    assert result.snapshot_id is not None


def test_push_returns_error_on_store_failure(backup_dir: Path) -> None:
    """push() returns SyncResult(error) when store raises — never re-raises."""
    from agentrag.sync.local import LocalSyncBackend

    store = MagicMock()
    store.create_snapshot.side_effect = OSError("disk full")
    backend = LocalSyncBackend(store=store, backup_dir=backup_dir)
    result = backend.push()
    assert result.status == "error"
    assert "disk full" in result.message


def test_pull_calls_recover_on_latest(
    backend: object, mock_store: MagicMock, backup_dir: Path, tmp_path: Path
) -> None:
    """pull() finds the latest .snapshot file and calls store.recover_snapshot."""
    from agentrag.sync.local import LocalSyncBackend

    assert isinstance(backend, LocalSyncBackend)
    snap = backup_dir / "snapshot_20260506T120000Z.snapshot"
    snap.write_bytes(b"snap-data")
    result = backend.pull()
    mock_store.recover_snapshot.assert_called_once_with(snap)
    assert result.status == "ok"


def test_pull_no_snapshots_returns_error(
    backup_dir: Path, mock_store: MagicMock
) -> None:
    """pull() returns SyncResult(error) when backup_dir has no .snapshot files."""
    from agentrag.sync.local import LocalSyncBackend

    backend = LocalSyncBackend(store=mock_store, backup_dir=backup_dir)
    result = backend.pull()
    assert result.status == "error"
    assert "no snapshots" in result.message.lower()


def test_pull_returns_error_on_restore_failure(backup_dir: Path) -> None:
    """pull() returns SyncResult(error) when store.recover_snapshot raises."""
    from agentrag.sync.local import LocalSyncBackend

    snap = backup_dir / "snapshot_20260506T120000Z.snapshot"
    snap.write_bytes(b"snap-data")
    store = MagicMock()
    store.recover_snapshot.side_effect = OSError("corrupt archive")
    backend = LocalSyncBackend(store=store, backup_dir=backup_dir)
    result = backend.pull()
    assert result.status == "error"
    assert "corrupt archive" in result.message


def test_status_no_snapshots(backup_dir: Path, mock_store: MagicMock) -> None:
    """status() returns 0 snapshot_count when no snapshots exist."""
    from agentrag.sync.local import LocalSyncBackend

    backend = LocalSyncBackend(store=mock_store, backup_dir=backup_dir)
    s = backend.status()
    assert isinstance(s, SyncStatus)
    assert s.backend == "local"
    assert s.snapshot_count == 0
    assert s.last_push is None


def test_status_with_snapshots(backup_dir: Path, mock_store: MagicMock) -> None:
    """status() reports correct count and latest push time."""
    from agentrag.sync.local import LocalSyncBackend

    (backup_dir / "snapshot_20260506T100000Z.snapshot").write_bytes(b"a")
    (backup_dir / "snapshot_20260506T110000Z.snapshot").write_bytes(b"b")
    backend = LocalSyncBackend(store=mock_store, backup_dir=backup_dir)
    s = backend.status()
    assert s.snapshot_count == 2
    assert s.last_push is not None
