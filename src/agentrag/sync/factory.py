"""Backend factory — returns the configured SyncBackend from Settings."""

from __future__ import annotations

from agentrag.config import Settings
from agentrag.store.qdrant import QdrantStore
from agentrag.sync.base import SyncBackend


def get_sync_backend(settings: Settings, store: QdrantStore) -> SyncBackend:
    """Instantiate and return the sync backend specified by settings.sync_backend."""
    backend = settings.sync_backend.lower()
    if backend == "local":
        from agentrag.sync.local import LocalSyncBackend

        return LocalSyncBackend(store=store, backup_dir=settings.sync_local_dir)
    if backend == "s3":
        if not settings.sync_key:
            raise ValueError(
                "AGENTRAG_SYNC_KEY is required for S3 sync. Generate one with: "
                "python -c 'from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())'"
            )
        import boto3

        s3 = boto3.client("s3")
        from agentrag.sync.cloud import S3SyncBackend

        return S3SyncBackend(
            store=store,
            s3_client=s3,
            bucket=settings.sync_endpoint,
            prefix=settings.sync_prefix,
            fernet_key=settings.sync_key.encode(),
        )
    raise ValueError(
        f"Unsupported sync backend: {settings.sync_backend!r}."
        " Supported: 'local', 's3'."
    )
