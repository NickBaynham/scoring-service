"""Health check endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.common import SERVICE_NAME

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Liveness and basic dependency readiness",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Critical dependency unavailable"},
    },
)
async def health(
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """Return service health and basic dependency readiness."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "degraded", "service": SERVICE_NAME, "database": "unavailable"},
        ) from None

    return {"status": "ok", "service": SERVICE_NAME}
