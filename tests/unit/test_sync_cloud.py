"""Unit tests for S3SyncBackend (boto3 S3 client fully mocked)."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from cryptography.fernet import Fernet


@pytest.fixture()
def fernet_key() -> bytes:
    """A valid Fernet key for testing."""
    return Fernet.generate_key()


@pytest.fixture()
def snapshot_file(tmp_path: Path) -> Path:
    """A fake snapshot file."""
    f = tmp_path / "snapshot_20260506T000000Z.snapshot"
    f.write_bytes(b"plain-snapshot-data")
    return f


@pytest.fixture()
def mock_store(snapshot_file: Path) -> MagicMock:
    """Mock QdrantStore returning a known snapshot file."""
    store = MagicMock()
    store.create_snapshot.return_value = snapshot_file
    return store


@pytest.fixture()
def mock_s3() -> MagicMock:
    """Mock boto3 S3 client."""
    return MagicMock()


def _make_backend(
    store: MagicMock,
    mock_s3: MagicMock,
    key: bytes,
    bucket: str = "test-bucket",
    prefix: str = "agentrag/",
) -> object:
    from agentrag.sync.cloud import S3SyncBackend

    return S3SyncBackend(
        store=store,
        s3_client=mock_s3,
        bucket=bucket,
        prefix=prefix,
        fernet_key=key,
        tmp_dir=Path("."),
    )


def test_push_uploads_encrypted_bytes(
    mock_store: MagicMock, mock_s3: MagicMock, fernet_key: bytes, snapshot_file: Path
) -> None:
    """push() encrypts snapshot before uploading — ciphertext differs from plaintext."""
    backend = _make_backend(mock_store, mock_s3, fernet_key)
    result = backend.push()  # type: ignore[union-attr]

    assert result.status == "ok"
    assert result.snapshot_id is not None
    mock_s3.put_object.assert_called_once()
    call_kwargs = mock_s3.put_object.call_args.kwargs
    uploaded_body: bytes = call_kwargs["Body"]
    assert uploaded_body != b"plain-snapshot-data"  # encrypted != plaintext
    # Verify it decrypts back to original
    assert Fernet(fernet_key).decrypt(uploaded_body) == b"plain-snapshot-data"


def test_push_returns_error_on_client_error(
    mock_store: MagicMock, mock_s3: MagicMock, fernet_key: bytes
) -> None:
    """push() returns SyncResult(error) on boto3 ClientError — never raises."""
    from botocore.exceptions import ClientError

    mock_s3.put_object.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "PutObject"
    )
    backend = _make_backend(mock_store, mock_s3, fernet_key)
    result = backend.push()  # type: ignore[union-attr]
    assert result.status == "error"
    assert "Access" in result.message or "access" in result.message.lower()


def test_pull_downloads_and_decrypts(
    mock_store: MagicMock, mock_s3: MagicMock, fernet_key: bytes, tmp_path: Path
) -> None:
    """pull() downloads ciphertext, decrypts, and calls store.recover_snapshot."""
    plaintext = b"real-snapshot-content"
    ciphertext = Fernet(fernet_key).encrypt(plaintext)
    mock_s3.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "agentrag/snapshot_001.enc", "LastModified": "2026-05-06T12:00:00"},
        ]
    }
    mock_s3.get_object.return_value = {"Body": io.BytesIO(ciphertext)}
    # Capture file bytes inside recover_snapshot before the temp file is deleted
    captured: list[bytes] = []

    def _capture_bytes(path: Path) -> None:
        captured.append(path.read_bytes())

    mock_store.recover_snapshot.side_effect = _capture_bytes
    from agentrag.sync.cloud import S3SyncBackend

    b = S3SyncBackend(
        store=mock_store,
        s3_client=mock_s3,
        bucket="test-bucket",
        prefix="agentrag/",
        fernet_key=fernet_key,
        tmp_dir=tmp_path,
    )
    result = b.pull()
    assert result.status == "ok"
    mock_store.recover_snapshot.assert_called_once()
    assert captured[0] == plaintext


def test_pull_no_snapshots_returns_error(
    mock_store: MagicMock, mock_s3: MagicMock, fernet_key: bytes
) -> None:
    """pull() returns SyncResult(error) when bucket has no snapshots."""
    mock_s3.list_objects_v2.return_value = {"Contents": []}
    backend = _make_backend(mock_store, mock_s3, fernet_key)
    result = backend.pull()  # type: ignore[union-attr]
    assert result.status == "error"
    assert "no snapshots" in result.message.lower()


def test_pull_wrong_key_returns_error(
    mock_store: MagicMock, mock_s3: MagicMock, fernet_key: bytes
) -> None:
    """pull() returns SyncResult(error) when decryption fails (wrong key)."""
    wrong_key = Fernet.generate_key()
    ciphertext = Fernet(wrong_key).encrypt(b"data")
    mock_s3.list_objects_v2.return_value = {
        "Contents": [{"Key": "agentrag/s.enc", "LastModified": "2026-05-06T12:00:00"}]
    }
    mock_s3.get_object.return_value = {"Body": io.BytesIO(ciphertext)}
    backend = _make_backend(mock_store, mock_s3, fernet_key)
    result = backend.pull()  # type: ignore[union-attr]
    assert result.status == "error"
    assert "AGENTRAG_SYNC_KEY" in result.message or "decrypt" in result.message.lower()


def test_pull_client_error_returns_error(
    mock_store: MagicMock, mock_s3: MagicMock, fernet_key: bytes
) -> None:
    """pull() returns SyncResult(error) on boto3 ClientError — never raises."""
    from botocore.exceptions import ClientError

    mock_s3.list_objects_v2.side_effect = ClientError(
        {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}},
        "ListObjectsV2",
    )
    backend = _make_backend(mock_store, mock_s3, fernet_key)
    result = backend.pull()  # type: ignore[union-attr]
    assert result.status == "error"
