"""Document persistence."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, DocumentStatus, SourceType


class DocumentRepository:
    """CRUD for documents."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, document_id: str, tenant_id: str | None = None) -> Document | None:
        stmt = select(Document).where(Document.id == document_id)
        if tenant_id is not None:
            stmt = stmt.where(Document.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        tenant_id: str,
        source_type: SourceType,
        profile: str,
        text_uri: str | None = None,
        raw_text: str | None = None,
        status: DocumentStatus = DocumentStatus.DRAFT,
        document_id: str | None = None,
    ) -> Document:
        kwargs: dict[str, object] = {
            "tenant_id": tenant_id,
            "source_type": source_type,
            "text_uri": text_uri,
            "raw_text": raw_text,
            "profile": profile,
            "status": status,
        }
        if document_id is not None:
            kwargs["id"] = document_id
        doc = Document(**kwargs)
        self._session.add(doc)
        await self._session.flush()
        return doc

    async def update_text(
        self,
        document: Document,
        *,
        raw_text: str | None = None,
        text_uri: str | None = None,
        status: DocumentStatus | None = None,
    ) -> Document:
        if raw_text is not None:
            document.raw_text = raw_text
        if text_uri is not None:
            document.text_uri = text_uri
        if status is not None:
            document.status = status
        await self._session.flush()
        return document
