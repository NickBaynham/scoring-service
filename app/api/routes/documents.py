"""Document registration and score retrieval."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.security import verify_api_key
from app.db.repositories.documents import DocumentRepository
from app.db.session import get_db_session
from app.schemas.api_errors import ErrorDetail, ErrorResponse
from app.schemas.document import DocumentCreateRequest, DocumentResponse
from app.schemas.score import DocumentScoresResponse
from app.services.document_service import map_source_type
from app.services.score_read_service import get_document_scores

router = APIRouter(
    prefix="/v1/documents",
    tags=["Documents"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a document",
    responses={
        201: {"description": "Document created"},
        422: {"description": "Invalid body"},
    },
)
async def create_document(
    body: DocumentCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> DocumentResponse:
    repo = DocumentRepository(session)
    doc = await repo.create(
        tenant_id=body.tenant_id,
        source_type=map_source_type(body.source_type),
        profile=body.profile,
        text_uri=body.text_uri,
        raw_text=body.raw_text,
    )
    return DocumentResponse.model_validate(doc)


@router.get(
    "/{document_id}/scores",
    response_model=DocumentScoresResponse,
    summary="Get latest credibility scores for a document",
    responses={
        200: {"description": "Scores found"},
        404: {"model": ErrorResponse, "description": "Document or scores missing"},
    },
)
async def get_scores(
    document_id: str,
    tenant_id: str = Query(..., examples=["tenant_1"]),
    profile: str = Query("credibility_v1", examples=["credibility_v1"]),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentScoresResponse:
    try:
        return await get_document_scores(
            session,
            document_id=document_id,
            tenant_id=tenant_id,
            profile=profile,
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(code="not_found", message=e.message).model_dump(),
        ) from e
