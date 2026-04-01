"""Scoring job persistence."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import JobStatus, ScoreJob


class JobRepository:
    """CRUD and queue operations for score jobs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, job_id: str, tenant_id: str | None = None) -> ScoreJob | None:
        stmt = select(ScoreJob).where(ScoreJob.id == job_id)
        if tenant_id is not None:
            stmt = stmt.where(ScoreJob.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        document_id: str,
        tenant_id: str,
        profile_name: str,
        profile_version: str,
        status: JobStatus = JobStatus.QUEUED,
        job_id: str | None = None,
    ) -> ScoreJob:
        kwargs: dict[str, object] = {
            "document_id": document_id,
            "tenant_id": tenant_id,
            "profile_name": profile_name,
            "profile_version": profile_version,
            "status": status,
        }
        if job_id is not None:
            kwargs["id"] = job_id
        job = ScoreJob(**kwargs)
        self._session.add(job)
        await self._session.flush()
        return job

    async def mark_running(self, job: ScoreJob) -> ScoreJob:
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(tz=UTC)
        await self._session.flush()
        return job

    async def mark_completed(self, job: ScoreJob) -> ScoreJob:
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(tz=UTC)
        await self._session.flush()
        return job

    async def mark_failed(self, job: ScoreJob, message: str) -> ScoreJob:
        job.status = JobStatus.FAILED
        job.error_message = message[:8000]
        job.completed_at = datetime.now(tz=UTC)
        await self._session.flush()
        return job

    async def fetch_next_queued_for_update(self) -> ScoreJob | None:
        """Claim next queued job using SKIP LOCKED on Postgres; simple select on SQLite (tests)."""
        stmt = select(ScoreJob).where(ScoreJob.status == JobStatus.QUEUED).order_by(ScoreJob.created_at.asc()).limit(1)
        bind = self._session.get_bind()
        dialect = getattr(bind, "dialect", None)
        name = dialect.name if dialect is not None else "postgresql"
        if name == "sqlite":
            stmt = stmt.execution_options(synchronize_session=False)
        else:
            stmt = stmt.with_for_update(skip_locked=True)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def try_claim_next_queued(self) -> ScoreJob | None:
        """Select one queued job and mark running in one transaction."""
        job = await self.fetch_next_queued_for_update()
        if job is None:
            return None
        return await self.mark_running(job)
