"""Unit tests for agentrag sync CLI commands (backend fully mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from agentrag.cli import app
from agentrag.types import SyncResult, SyncStatus

runner = CliRunner()


def _ok_push() -> SyncResult:
    return SyncResult(
        status="ok",
        message="Snapshot saved: /tmp/snap.snapshot",
        snapshot_id="snap.snapshot",
    )


def _ok_pull() -> SyncResult:
    return SyncResult(status="ok", message="Snapshot restored from /tmp/snap.snapshot")


def _ok_status() -> SyncStatus:
    return SyncStatus(
        backend="local", last_push="20260506T120000Z", last_pull=None, snapshot_count=2
    )


def _error_result(msg: str) -> SyncResult:
    return SyncResult(status="error", message=msg)


def test_sync_push_success() -> None:
    """agentrag sync push prints success message and exits 0."""
    mock_backend = MagicMock()
    mock_backend.push.return_value = _ok_push()
    with patch("agentrag.cli.get_sync_backend", return_value=mock_backend):
        with patch("agentrag.cli.QdrantStore"):
            result = runner.invoke(app, ["sync", "push"])
    assert result.exit_code == 0
    assert "Snapshot saved" in result.output


def test_sync_push_failure_exits_nonzero() -> None:
    """agentrag sync push exits 1 and prints error on failure."""
    mock_backend = MagicMock()
    mock_backend.push.return_value = _error_result("disk full")
    with patch("agentrag.cli.get_sync_backend", return_value=mock_backend):
        with patch("agentrag.cli.QdrantStore"):
            result = runner.invoke(app, ["sync", "push"])
    assert result.exit_code == 1
    assert "disk full" in result.output


def test_sync_pull_success() -> None:
    """agentrag sync pull prints success message and exits 0."""
    mock_backend = MagicMock()
    mock_backend.pull.return_value = _ok_pull()
    with patch("agentrag.cli.get_sync_backend", return_value=mock_backend):
        with patch("agentrag.cli.QdrantStore"):
            result = runner.invoke(app, ["sync", "pull"])
    assert result.exit_code == 0
    assert "restored" in result.output


def test_sync_pull_failure_exits_nonzero() -> None:
    """agentrag sync pull exits 1 on failure."""
    mock_backend = MagicMock()
    mock_backend.pull.return_value = _error_result("no snapshots found")
    with patch("agentrag.cli.get_sync_backend", return_value=mock_backend):
        with patch("agentrag.cli.QdrantStore"):
            result = runner.invoke(app, ["sync", "pull"])
    assert result.exit_code == 1
    assert "no snapshots" in result.output


def test_sync_status_success() -> None:
    """agentrag sync status prints backend, count and last-push time, exits 0."""
    mock_backend = MagicMock()
    mock_backend.status.return_value = _ok_status()
    with patch("agentrag.cli.get_sync_backend", return_value=mock_backend):
        with patch("agentrag.cli.QdrantStore"):
            result = runner.invoke(app, ["sync", "status"])
    assert result.exit_code == 0
    assert "local" in result.output
    assert "2" in result.output  # snapshot count
