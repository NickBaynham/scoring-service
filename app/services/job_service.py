"""Application service for job orchestration from the API layer."""

from uuid import uuid4

from app.core.config import Settings, get_settings
from app.core.exceptions import DomainValidationError, NotFoundError
from app.db.models import ScoreJob
from app.db.repositories.documents import DocumentRepository
from app.db.repositories.jobs import JobRepository
from app.schemas.job import ScoreJobCreateRequest
from sqlalchemy.ext.asyncio import AsyncSession


async def create_score_job(
    session: AsyncSession,
    body: ScoreJobCreateRequest,
    settings: Settings | None = None,
) -> ScoreJob:
    """Enqueue a job for an existing document."""
    settings = settings or get_settings()
    doc_repo = DocumentRepository(session)
    job_repo = JobRepository(session)

    doc = await doc_repo.get_by_id(body.document_id, tenant_id=body.tenant_id)
    if doc is None:
        raise NotFoundError("Document not found")

    from app.services.document_service import ensure_document_ready

    doc = await ensure_document_ready(
        doc_repo,
        doc,
        text=body.text,
        text_uri=body.text_uri,
    )

    if not doc.raw_text and not doc.text_uri:
        raise DomainValidationError(
            "No text source for scoring: provide text or text_uri, or register document content first.",
        )

    job_id = str(uuid4())
    job = await job_repo.create(
        document_id=doc.id,
        tenant_id=body.tenant_id,
        profile_name=body.profile,
        profile_version=settings.score_profile_version,
        job_id=job_id,
    )
    return job
