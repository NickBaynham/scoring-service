"""Scoring job API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from app.db.models import JobStatus
from pydantic import BaseModel, Field, model_validator


class ScoreJobCreateRequest(BaseModel):
    """Submit a scoring job."""

    document_id: str = Field(..., examples=["doc_123"])
    tenant_id: str = Field(..., examples=["tenant_1"])
    text: str | None = Field(
        None,
        description="Optional raw text; used if document has no text yet.",
        examples=["The company grew 50% year over year."],
    )
    text_uri: str | None = Field(
        None,
        description="Optional S3 URI for normalized text blob.",
        examples=["s3://my-bucket/docs/a.txt"],
    )
    profile: str = Field(default="credibility_v1", examples=["credibility_v1"])

    @model_validator(mode="after")
    def text_or_uri_or_document(self) -> ScoreJobCreateRequest:
        """Allow submission when document will supply text; at least one path in pipeline."""
        return self


class ScoreJobCreateResponse(BaseModel):
    """Queued job acknowledgement."""

    job_id: str = Field(..., examples=["job_456"])
    status: Literal["queued"] = "queued"


class ScoreJobStatusResponse(BaseModel):
    """Job metadata and lifecycle state."""

    job_id: str
    document_id: str
    tenant_id: str
    profile_name: str
    profile_version: str
    status: JobStatus
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
