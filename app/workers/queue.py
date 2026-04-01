"""Job queue abstraction; database-backed dequeue for multi-process workers."""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.repositories.jobs import JobRepository


class JobQueue(Protocol):
    """Pluggable queue: swap for SQS/RabbitMQ later."""

    async def dequeue_job_id(self) -> str | None:
        """Return the next job id to process, or None if empty."""


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
