from unittest.mock import MagicMock, patch

from app.services.storage import StorageService


@patch("app.services.storage.Minio")
def test_upload_file(mock_minio_cls):
    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = True
    mock_minio_cls.return_value = mock_client

    svc = StorageService("localhost:9000", "key", "secret", "bucket")
    path = svc.upload(b"content", "test.pdf", "user-123")
    assert "user-123" in path
    assert path.endswith(".pdf")
    mock_client.put_object.assert_called_once()


@patch("app.services.storage.Minio")
def test_download_file(mock_minio_cls):
    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = True
    mock_response = MagicMock()
    mock_response.read.return_value = b"pdf-content"
    mock_client.get_object.return_value = mock_response
    mock_minio_cls.return_value = mock_client

    svc = StorageService("localhost:9000", "key", "secret", "bucket")
    data = svc.download("uploads/user-123/test.pdf")
    assert data == b"pdf-content"


@patch("app.services.storage.Minio")
def test_delete_file(mock_minio_cls):
    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = True
    mock_minio_cls.return_value = mock_client

    svc = StorageService("localhost:9000", "key", "secret", "bucket")
    svc.delete("uploads/user-123/test.pdf")
    mock_client.remove_object.assert_called_once_with("bucket", "uploads/user-123/test.pdf")


@patch("app.services.storage.Minio")
def test_creates_bucket_if_not_exists(mock_minio_cls):
    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = False
    mock_minio_cls.return_value = mock_client

    StorageService("localhost:9000", "key", "secret", "mybucket")
    mock_client.make_bucket.assert_called_once_with("mybucket")
