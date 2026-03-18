from __future__ import annotations

import io
import uuid
from typing import Optional

from minio import Minio


class StorageService:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self.bucket = bucket
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload(
        self, data: bytes, filename: str, user_id: str
    ) -> str:
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "pdf"
        object_name = f"uploads/{user_id}/{uuid.uuid4().hex}.{ext}"
        self.client.put_object(
            self.bucket,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type="application/pdf",
        )
        return object_name

    def download(self, object_name: str) -> bytes:
        response = self.client.get_object(self.bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, object_name: str) -> None:
        self.client.remove_object(self.bucket, object_name)

    def get_presigned_url(
        self, object_name: str, expires_hours: int = 1
    ) -> str:
        from datetime import timedelta

        return self.client.presigned_get_object(
            self.bucket,
            object_name,
            expires=timedelta(hours=expires_hours),
        )
