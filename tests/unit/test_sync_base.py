"""Tests for SyncBackend protocol structural typing."""

from __future__ import annotations

from agentrag.sync.base import SyncBackend
from agentrag.types import SyncResult, SyncStatus


class _GoodBackend:
    """Concrete class that satisfies SyncBackend without inheriting."""

    def push(self) -> SyncResult:
        """Push snapshot."""
        return SyncResult(status="ok", message="pushed")

    def pull(self) -> SyncResult:
        """Pull snapshot."""
        return SyncResult(status="ok", message="pulled")

    def status(self) -> SyncStatus:
        """Return status."""
        return SyncStatus(
            backend="test", last_push=None, last_pull=None, snapshot_count=0
        )


class _MissingPull:
    """Incomplete class — missing pull method."""

    def push(self) -> SyncResult:
        """Push snapshot."""
        return SyncResult(status="ok", message="")

    def status(self) -> SyncStatus:
        """Return status."""
        return SyncStatus(
            backend="test", last_push=None, last_pull=None, snapshot_count=0
        )


def test_good_backend_satisfies_protocol() -> None:
    """Class with all three methods satisfies SyncBackend structurally."""
    backend: SyncBackend = _GoodBackend()  # type: ignore[assignment]
    result = backend.push()
    assert result.status == "ok"


def test_sync_result_fields() -> None:
    """SyncResult has required fields with correct types."""
    r = SyncResult(status="ok", message="done", snapshot_id="snap_001")
    assert r.status == "ok"
    assert r.message == "done"
    assert r.snapshot_id == "snap_001"


def test_sync_result_snapshot_id_optional() -> None:
    """SyncResult snapshot_id defaults to None."""
    r = SyncResult(status="error", message="failed")
    assert r.snapshot_id is None


def test_sync_status_fields() -> None:
    """SyncStatus has required fields with correct types."""
    s = SyncStatus(
        backend="local",
        last_push="2026-05-06T10:00:00+00:00",
        last_pull=None,
        snapshot_count=3,
    )
    assert s.backend == "local"
    assert s.last_push is not None
    assert s.last_pull is None
    assert s.snapshot_count == 3
