"""Score results and spans persistence."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import JobStatus, ScoreJob, ScoreResult, ScoreSpan


class ScoreRepository:
    """Persist and read score dimensions and issues."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_result(
        self,
        result: ScoreResult,
    ) -> ScoreResult:
        self._session.add(result)
        await self._session.flush()
        return result

    async def add_span(self, span: ScoreSpan) -> ScoreSpan:
        self._session.add(span)
        await self._session.flush()
        return span

    async def list_for_document(
        self,
        document_id: str,
        *,
        profile_name: str | None = None,
    ) -> list[ScoreResult]:
        stmt = (
            select(ScoreResult)
            .where(ScoreResult.document_id == document_id)
            .options(selectinload(ScoreResult.spans))
            .order_by(ScoreResult.created_at.desc())
        )
        if profile_name:
            stmt = stmt.join(ScoreJob, ScoreResult.job_id == ScoreJob.id).where(ScoreJob.profile_name == profile_name)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def latest_completed_job_for_document(
        self,
        document_id: str,
        profile_name: str,
    ) -> ScoreJob | None:
        stmt = (
            select(ScoreJob)
            .where(
                ScoreJob.document_id == document_id,
                ScoreJob.profile_name == profile_name,
                ScoreJob.status == JobStatus.COMPLETED,
            )
            .order_by(ScoreJob.completed_at.desc().nullslast())
            .limit(1)
            .options(selectinload(ScoreJob.results).selectinload(ScoreResult.spans))
        )
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()
