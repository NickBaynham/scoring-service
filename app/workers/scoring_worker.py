"""Async worker loop that processes queued scoring jobs."""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.telemetry import init_telemetry
from app.db.models import JobStatus
from app.db.repositories.jobs import JobRepository
from app.db.session import get_session_factory, init_engine
from app.services.scoring_service import run_scoring_pipeline
from app.workers.queue import JobQueue, build_job_queue

logger = logging.getLogger(__name__)


async def process_once(
    factory: async_sessionmaker[AsyncSession],
    job_id: str,
) -> None:
    """Load job and run the scoring pipeline in a dedicated session."""
    async with factory() as session:
        repo = JobRepository(session)
        job = await repo.get_by_id(job_id)
        if job is None:
            logger.error("Job disappeared after dequeue: %s", job_id)
            return
        if job.status == JobStatus.QUEUED:
            await repo.mark_running(job)
            await session.flush()
        await run_scoring_pipeline(session, job)
        await session.commit()


async def worker_loop(stop: asyncio.Event) -> None:
    """Poll the database queue and execute scoring."""
    settings = get_settings()
    init_engine(settings)
    init_telemetry(settings)
    factory = get_session_factory()
    queue: JobQueue = build_job_queue(factory, settings)
    poll = settings.worker_poll_interval_seconds

    logger.info(
        "Scoring worker started",
        extra={"poll_interval_s": poll, "queue_backend": settings.job_queue_backend},
    )

    while not stop.is_set():
        try:
            job_id = await queue.dequeue_job_id()
            if job_id:
                logger.info("Processing job", extra={"job_id": job_id})
                try:
                    await process_once(factory, job_id)
                    await queue.acknowledge_last()
                except Exception:
                    logger.exception("Job processing failed", extra={"job_id": job_id})
            else:
                try:
                    await asyncio.wait_for(stop.wait(), timeout=poll)
                except TimeoutError:
                    continue
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Worker iteration failed")

    logger.info("Scoring worker shutting down")


async def _async_main() -> None:
    stop = asyncio.Event()

    def _handle_sig(*_: object) -> None:
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_sig)
        except NotImplementedError:
            signal.signal(sig, lambda *_: stop.set())

    await worker_loop(stop)


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level, json_logs=settings.app_env not in ("local", "test"))
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
