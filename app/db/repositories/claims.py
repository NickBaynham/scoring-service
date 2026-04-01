"""Claim persistence."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Claim


class ClaimRepository:
    """CRUD for extracted claims."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_document(self, document_id: str) -> list[Claim]:
        stmt = select(Claim).where(Claim.document_id == document_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_create(self, claims: list[Claim]) -> list[Claim]:
        self._session.add_all(claims)
        await self._session.flush()
        return claims
