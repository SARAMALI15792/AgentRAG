"""S3SyncBackend — encrypts snapshots with Fernet before uploading to S3."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from agentrag.store.qdrant import QdrantStore
from agentrag.types import SyncResult, SyncStatus

logger = logging.getLogger(__name__)


class S3SyncBackend:
    """Pushes/pulls encrypted Qdrant snapshots to/from an S3-compatible bucket."""

    def __init__(
        self,
        store: QdrantStore,
        s3_client: Any,
        bucket: str,
        prefix: str,
        fernet_key: bytes,
        tmp_dir: Path | None = None,
    ) -> None:
        """Initialise with a QdrantStore, boto3 S3 client, and encryption key."""
        self._store = store
        self._s3 = s3_client
        self._bucket = bucket
        self._prefix = prefix.rstrip("/") + "/"
        self._fernet = Fernet(fernet_key)
        self._tmp_dir = tmp_dir or Path(tempfile.gettempdir())

    def push(self) -> SyncResult:
        """Snapshot → encrypt → upload to S3."""
        try:
            with tempfile.TemporaryDirectory(dir=self._tmp_dir) as td:
                snapshot_path: Path = self._store.create_snapshot(Path(td))
                plaintext = snapshot_path.read_bytes()
                ciphertext = self._fernet.encrypt(plaintext)
                s3_key = f"{self._prefix}{snapshot_path.name}.enc"
                self._s3.put_object(Bucket=self._bucket, Key=s3_key, Body=ciphertext)
                logger.info("Snapshot uploaded: s3://%s/%s", self._bucket, s3_key)
                return SyncResult(
                    status="ok",
                    message=f"Snapshot uploaded: s3://{self._bucket}/{s3_key}",
                    snapshot_id=s3_key,
                )
        except Exception as exc:
            return self._handle_error(exc)

    def pull(self) -> SyncResult:
        """Download latest snapshot from S3 → decrypt → restore."""
        try:
            response = self._s3.list_objects_v2(
                Bucket=self._bucket, Prefix=self._prefix
            )
            contents = response.get("Contents") or []
            if not contents:
                loc = f"s3://{self._bucket}/{self._prefix}"
                return SyncResult(
                    status="error",
                    message=(
                        f"No snapshots found in {loc}."
                        " Run 'agentrag sync push' first."
                    ),
                )
            latest = max(contents, key=lambda o: o["LastModified"])
            s3_key: str = latest["Key"]
            obj = self._s3.get_object(Bucket=self._bucket, Key=s3_key)
            ciphertext: bytes = obj["Body"].read()
            try:
                plaintext = self._fernet.decrypt(ciphertext)
            except InvalidToken:
                return SyncResult(
                    status="error",
                    message=(
                        "Decryption failed. Verify AGENTRAG_SYNC_KEY"
                        " matches the key used during push."
                    ),
                )
            tmp_snapshot = self._tmp_dir / Path(s3_key).name.removesuffix(".enc")
            tmp_snapshot.write_bytes(plaintext)
            self._store.recover_snapshot(tmp_snapshot)
            tmp_snapshot.unlink(missing_ok=True)
            logger.info("Snapshot restored from s3://%s/%s", self._bucket, s3_key)
            return SyncResult(
                status="ok",
                message=f"Snapshot restored from s3://{self._bucket}/{s3_key}",
            )
        except Exception as exc:
            return self._handle_error(exc)

    def status(self) -> SyncStatus:
        """Return S3 snapshot count and last push time."""
        try:
            response = self._s3.list_objects_v2(
                Bucket=self._bucket, Prefix=self._prefix
            )
            contents = response.get("Contents") or []
            last_push: str | None = None
            if contents:
                latest = max(contents, key=lambda o: o["LastModified"])
                last_push = str(latest["LastModified"])
            return SyncStatus(
                backend="s3",
                last_push=last_push,
                last_pull=None,
                snapshot_count=len(contents),
            )
        except Exception:
            return SyncStatus(
                backend="s3", last_push=None, last_pull=None, snapshot_count=0
            )

    def _handle_error(self, exc: Exception) -> SyncResult:
        """Convert exceptions to SyncResult(error) with actionable messages."""
        try:
            from botocore.exceptions import ClientError

            if isinstance(exc, ClientError):
                code = exc.response["Error"]["Code"]
                msg = exc.response["Error"]["Message"]
                if code in ("AccessDenied", "InvalidAccessKeyId"):
                    return SyncResult(
                        status="error",
                        message=(
                            f"AWS credentials error ({code}): {msg}."
                            " Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
                        ),
                    )
                return SyncResult(status="error", message=f"S3 error ({code}): {msg}")
        except ImportError:
            pass
        return SyncResult(status="error", message=str(exc))
