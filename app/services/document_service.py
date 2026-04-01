"""Resolve document text from inline storage or S3."""

import logging

from app.core.exceptions import DomainValidationError
from app.db.models import Document, DocumentStatus, SourceType
from app.db.repositories.documents import DocumentRepository
from app.storage.s3_client import S3Storage

logger = logging.getLogger(__name__)


async def resolve_document_text(
    doc: Document,
    *,
    override_text: str | None = None,
    override_uri: str | None = None,
    s3: S3Storage | None = None,
) -> str:
    """Return UTF-8 text used for scoring."""
    if override_text:
        return override_text.strip()
    if doc.raw_text:
        return doc.raw_text.strip()
    uri = override_uri or doc.text_uri
    if uri:
        storage = s3 or S3Storage()
        text = await storage.get_text(uri)
        return text.strip()
    raise DomainValidationError("No text available: provide text, raw_text on document, or text_uri")


def map_source_type(s: str) -> SourceType:
    try:
        return SourceType(s)
    except ValueError:
        return SourceType.UNKNOWN


async def ensure_document_ready(
    repo: DocumentRepository,
    doc: Document,
    *,
    text: str | None,
    text_uri: str | None,
) -> Document:
    """Apply inline updates and mark ready when text exists."""
    if text is not None:
        doc = await repo.update_text(doc, raw_text=text, status=DocumentStatus.READY)
    elif text_uri is not None:
        doc = await repo.update_text(doc, text_uri=text_uri, status=DocumentStatus.READY)
    elif doc.raw_text or doc.text_uri:
        doc = await repo.update_text(doc, status=DocumentStatus.READY)
    return doc
