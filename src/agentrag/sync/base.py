"""SyncBackend protocol — structural interface for all sync backends."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from agentrag.types import SyncResult, SyncStatus


@runtime_checkable
class SyncBackend(Protocol):
    """Structural protocol: implement push/pull/status to satisfy without inheriting."""

    def push(self) -> SyncResult:
        """Create and upload a snapshot of the vector store."""
        ...

    def pull(self) -> SyncResult:
        """Download the latest snapshot and restore the vector store."""
        ...

    def status(self) -> SyncStatus:
        """Return last push/pull times and snapshot count."""
        ...
