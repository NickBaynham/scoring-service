"""Notify workers when a job is queued (e.g. SQS)."""

import json
import logging

import aioboto3
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


async def notify_job_enqueued(job_id: str, settings: Settings | None = None) -> None:
    """When using SQS backend, publish job id so workers do not rely on DB polling alone."""
    settings = settings or get_settings()
    if settings.job_queue_backend != "sqs":
        return
    if not settings.sqs_queue_url:
        logger.warning("SQS backend selected but SQS_QUEUE_URL is empty")
        return

    session = aioboto3.Session()
    async with session.client(
        "sqs",
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url or None,
    ) as client:
        await client.send_message(
            QueueUrl=settings.sqs_queue_url,
            MessageBody=json.dumps({"job_id": job_id}),
        )
    logger.debug("Published job to SQS", extra={"job_id": job_id})
