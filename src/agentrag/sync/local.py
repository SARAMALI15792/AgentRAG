"""LocalSyncBackend — filesystem snapshot backup using Qdrant data directory."""

from __future__ import annotations

import logging
from pathlib import Path

from agentrag.store.qdrant import QdrantStore
from agentrag.types import SyncResult, SyncStatus

logger = logging.getLogger(__name__)


class LocalSyncBackend:
    """Backs up and restores the Qdrant data directory as .snapshot archives."""

    def __init__(self, store: QdrantStore, backup_dir: Path) -> None:
        """Initialise with a QdrantStore instance and the backup directory."""
        self._store = store
        self._backup_dir = backup_dir

    def push(self) -> SyncResult:
        """Create snapshot archive in backup_dir."""
        try:
            self._backup_dir.mkdir(parents=True, exist_ok=True)
            snapshot_path: Path = self._store.create_snapshot(self._backup_dir)
            logger.info("Snapshot created: %s", snapshot_path)
            return SyncResult(
                status="ok",
                message=f"Snapshot saved: {snapshot_path}",
                snapshot_id=snapshot_path.name,
            )
        except Exception as exc:
            return SyncResult(status="error", message=str(exc))

    def pull(self) -> SyncResult:
        """Find latest .snapshot file and restore the vector store."""
        snapshots = sorted(self._backup_dir.glob("*.snapshot"))
        if not snapshots:
            return SyncResult(
                status="error",
                message=(
                    f"No snapshots found in {self._backup_dir}."
                    " Run 'agentrag sync push' first."
                ),
            )
        latest = snapshots[-1]
        try:
            self._store.recover_snapshot(latest)
            logger.info("Snapshot restored: %s", latest)
            return SyncResult(status="ok", message=f"Snapshot restored from {latest}")
        except Exception as exc:
            return SyncResult(status="error", message=str(exc))

    def status(self) -> SyncStatus:
        """Scan backup_dir for snapshots and return counts and timestamps."""
        snapshots = sorted(self._backup_dir.glob("*.snapshot"))
        last_push: str | None = None
        if snapshots:
            # Extract timestamp from filename: snapshot_{ts}.snapshot
            name = snapshots[-1].stem  # e.g. "snapshot_20260506T120000Z"
            last_push = name.replace("snapshot_", "", 1) if "_" in name else name
        return SyncStatus(
            backend="local",
            last_push=last_push,
            last_pull=None,
            snapshot_count=len(snapshots),
        )
