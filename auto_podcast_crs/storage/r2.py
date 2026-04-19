"""Cloudflare R2 implementation of StorageProvider.

R2 is S3-API-compatible. We use boto3 with the R2 endpoint override.

Two URLs per bucket:
  - write endpoint: https://<accountid>.r2.cloudflarestorage.com  (S3 API, requires keys)
  - public URL:     https://pub-<hash>.r2.dev                     (anonymous read)

Upload via the write endpoint, return the public URL for RSS feeds.
"""
from __future__ import annotations

import logging
import mimetypes
from pathlib import Path

from auto_podcast_crs.config import get_settings
from auto_podcast_crs.storage import StorageProvider

log = logging.getLogger(__name__)


class R2Storage(StorageProvider):
    def __init__(
        self,
        endpoint: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        public_url: str | None = None,
        bucket: str | None = None,
    ):
        s = get_settings()
        self.endpoint = endpoint or s.r2_endpoint
        self.access_key_id = access_key_id or s.r2_access_key_id
        self.secret_access_key = secret_access_key or s.r2_secret_access_key
        self.public_url = (public_url or s.r2_public_url).rstrip("/")
        self.bucket = bucket or s.r2_bucket

        missing = [
            name for name, val in [
                ("R2_ENDPOINT", self.endpoint),
                ("R2_ACCESS_KEY_ID", self.access_key_id),
                ("R2_SECRET_ACCESS_KEY", self.secret_access_key),
                ("R2_PUBLIC_URL", self.public_url),
            ] if not val
        ]
        if missing:
            raise RuntimeError(f"R2Storage missing env vars: {', '.join(missing)}")

        # Lazy import so boto3 stays in the `storage` extras group, not core
        try:
            import boto3
        except ImportError as e:
            raise RuntimeError(
                "boto3 not installed. Install with: pip install -e '.[storage]'"
            ) from e

        self._client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name="auto",  # R2 doesn't use regions
        )

    def upload(
        self,
        local_path: Path,
        object_key: str,
        *,
        content_type: str | None = None,
    ) -> str:
        if not local_path.exists():
            raise FileNotFoundError(f"Upload source not found: {local_path}")

        if content_type is None:
            # Guess from extension
            guessed, _ = mimetypes.guess_type(str(local_path))
            content_type = guessed or "application/octet-stream"

        size_mb = local_path.stat().st_size / (1024 * 1024)
        log.info(
            "Uploading %s (%.2f MB) → r2://%s/%s [%s]",
            local_path.name, size_mb, self.bucket, object_key, content_type,
        )

        self._client.upload_file(
            str(local_path),
            self.bucket,
            object_key,
            ExtraArgs={"ContentType": content_type},
        )

        public_url = f"{self.public_url}/{object_key}"
        log.info("Uploaded → %s", public_url)
        return public_url

    def exists(self, object_key: str) -> bool:
        # Lazy import for error class
        try:
            from botocore.exceptions import ClientError
        except ImportError as e:
            raise RuntimeError("botocore not available") from e

        try:
            self._client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise
