"""Scoring job HTTP API."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_api_key
from app.db.repositories.jobs import JobRepository
from app.db.session import get_db_session
from app.schemas.api_errors import ErrorDetail, ErrorResponse
from app.schemas.job import ScoreJobCreateRequest, ScoreJobCreateResponse, ScoreJobStatusResponse
from app.services.job_notification import notify_job_enqueued
from app.services.job_service import create_score_job

router = APIRouter(
    prefix="/v1/score-jobs",
    tags=["Scoring jobs"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "",
    response_model=ScoreJobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a scoring job",
    description=(
        "Queues an asynchronous scoring run for the given document. "
        "Provide inline `text` or `text_uri`, or ensure the document already has text."
    ),
    responses={
        202: {"description": "Job accepted and queued"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        422: {"description": "Validation error"},
    },
)
async def create_job(
    body: ScoreJobCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ScoreJobCreateResponse:
    job = await create_score_job(session, body)
    await session.commit()
    await notify_job_enqueued(job.id)
    return ScoreJobCreateResponse(job_id=job.id, status="queued")


@router.get(
    "/{job_id}",
    response_model=ScoreJobStatusResponse,
    summary="Get scoring job status",
    responses={
        200: {"description": "Job found"},
        404: {"model": ErrorResponse, "description": "Unknown job id"},
    },
)
async def get_job(
    job_id: str,
    tenant_id: str = Query(..., description="Tenant scope", examples=["tenant_1"]),
    session: AsyncSession = Depends(get_db_session),
) -> ScoreJobStatusResponse:
    repo = JobRepository(session)
    job = await repo.get_by_id(job_id, tenant_id=tenant_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(code="not_found", message="Job not found").model_dump(),
        )
    return ScoreJobStatusResponse.model_validate(job)
