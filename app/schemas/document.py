"""Document API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from app.db.models import DocumentStatus
from pydantic import BaseModel, Field, model_validator


class DocumentCreateRequest(BaseModel):
    """Register a document before scoring."""

    tenant_id: str = Field(..., min_length=1, max_length=128, examples=["tenant_1"])
    source_type: Literal["paste", "upload", "s3_ref", "unknown"] = "paste"
    text_uri: str | None = Field(None, max_length=2048, examples=["s3://bucket/key.txt"])
    raw_text: str | None = Field(None, examples=["Optional inline text."])
    profile: str = Field(default="credibility_v1", examples=["credibility_v1"])

    @model_validator(mode="after")
    def optional_content(self) -> DocumentCreateRequest:
        """Documents may be created empty and filled during scoring."""
        return self


class DocumentResponse(BaseModel):
    """Created or retrieved document."""

    id: str
    tenant_id: str
    source_type: str
    text_uri: str | None
    profile: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
