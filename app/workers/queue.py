"""Job queue abstraction; database-backed or SQS-backed dequeue."""

import json
import logging
from typing import Any, Protocol

import aioboto3
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.db.repositories.jobs import JobRepository

logger = logging.getLogger(__name__)


class JobQueue(Protocol):
    """Pluggable queue: database polling or SQS long poll."""

    async def dequeue_job_id(self) -> str | None:
        """Return the next job id to process, or None if empty / no message."""

    async def acknowledge_last(self) -> None:
        """Best-effort ack after successful processing (SQS delete); no-op for DB queue."""


class DatabaseJobQueue:
    """Postgres-backed queue using SKIP LOCKED."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def dequeue_job_id(self) -> str | None:
        async with self._session_factory() as session:
            repo = JobRepository(session)
            job = await repo.try_claim_next_queued()
            if job is None:
                await session.rollback()
                return None
            await session.commit()
            return job.id

    async def acknowledge_last(self) -> None:
        """Row already committed as running; nothing to ack."""


class SqsJobQueue:
    """SQS long-poll; delete message after successful scoring via acknowledge_last."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._receipt_handle: str | None = None

    async def dequeue_job_id(self) -> str | None:
        """Long-poll SQS; stash receipt handle for acknowledge_last."""
        self._receipt_handle = None
        if not self._settings.sqs_queue_url:
            logger.error("SQS_QUEUE_URL not configured")
            return None

        wait = min(20, max(1, int(self._settings.worker_poll_interval_seconds * 2)))
        vis = min(900, max(30, int(self._settings.sqs_visibility_timeout_seconds)))

        session = aioboto3.Session()
        async with session.client(
            "sqs",
            region_name=self._settings.aws_region,
            endpoint_url=self._settings.aws_endpoint_url or None,
        ) as client:
            resp = await client.receive_message(
                QueueUrl=self._settings.sqs_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=wait,
                VisibilityTimeout=vis,
            )
            messages = resp.get("Messages", [])
            if not messages:
                return None
            msg = messages[0]
            self._receipt_handle = msg.get("ReceiptHandle")
            body_raw = msg.get("Body", "{}")
            job_id = self._parse_job_id(body_raw)
            if not job_id:
                logger.error("SQS message missing job_id: %s", body_raw)
                await self._delete_message(client)
                return None
            return job_id

    def _parse_job_id(self, body_raw: str) -> str | None:
        try:
            data: dict[str, Any] = json.loads(body_raw)
            jid = data.get("job_id", "")
            return str(jid) if jid else None
        except json.JSONDecodeError:
            text = body_raw.strip()
            return text or None

    async def _delete_message(self, client: Any) -> None:
        if self._receipt_handle and self._settings.sqs_queue_url:
            await client.delete_message(
                QueueUrl=self._settings.sqs_queue_url,
                ReceiptHandle=self._receipt_handle,
            )
        self._receipt_handle = None

    async def acknowledge_last(self) -> None:
        """Delete the last received message after successful processing."""
        if not self._receipt_handle or not self._settings.sqs_queue_url:
            self._receipt_handle = None
            return
        session = aioboto3.Session()
        async with session.client(
            "sqs",
            region_name=self._settings.aws_region,
            endpoint_url=self._settings.aws_endpoint_url or None,
        ) as client:
            await client.delete_message(
                QueueUrl=self._settings.sqs_queue_url,
                ReceiptHandle=self._receipt_handle,
            )
        self._receipt_handle = None


def build_job_queue(
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings | None = None,
) -> DatabaseJobQueue | SqsJobQueue:
    """Factory for the configured backend."""
    settings = settings or get_settings()
    if settings.job_queue_backend == "sqs":
        return SqsJobQueue(settings)
    return DatabaseJobQueue(session_factory)
