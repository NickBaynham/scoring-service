"""S3-compatible object storage for document text blobs."""

from __future__ import annotations

import logging

import aioboto3
from botocore.exceptions import ClientError

from app.core.config import Settings, get_settings
from app.core.exceptions import DomainValidationError, StorageError

logger = logging.getLogger(__name__)


class S3Storage:
    """Async get/put for text objects."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._session = aioboto3.Session()

    async def get_text(self, uri: str) -> str:
        """Fetch object body as UTF-8 text from s3://bucket/key."""
        if not uri.startswith("s3://"):
            raise DomainValidationError("text_uri must be an s3:// URI")
        rest = uri[5:]
        bucket, _, key = rest.partition("/")
        if not bucket or not key:
            raise DomainValidationError("Invalid S3 URI")
        if self._settings.s3_bucket and bucket != self._settings.s3_bucket:
            logger.warning("Bucket %s differs from configured S3_BUCKET", bucket)
        try:
            async with self._session.client(
                "s3",
                region_name=self._settings.aws_region,
                endpoint_url=self._settings.aws_endpoint_url or None,
            ) as client:
                resp = await client.get_object(Bucket=bucket, Key=key)
                body = await resp["Body"].read()
        except ClientError as e:
            raise StorageError(f"S3 get failed: {e}") from e
        text: str = body.decode("utf-8")
        return text
