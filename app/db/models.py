"""SQLAlchemy ORM models for documents, jobs, scores, and claims."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid_str() -> str:
    return str(uuid4())


class SourceType(enum.StrEnum):
    """How document text was provided."""

    PASTE = "paste"
    UPLOAD = "upload"
    S3_REF = "s3_ref"
    UNKNOWN = "unknown"


class DocumentStatus(enum.StrEnum):
    """Lifecycle state of a document record."""

    DRAFT = "draft"
    READY = "ready"
    SCORED = "scored"
    ERROR = "error"


class JobStatus(enum.StrEnum):
    """Scoring job state."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    """A logical document belonging to a tenant."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type_enum", native_enum=False, length=32),
        default=SourceType.UNKNOWN,
    )
    text_uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile: Mapped[str] = mapped_column(String(64), default="credibility_v1")
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status_enum", native_enum=False, length=32),
        default=DocumentStatus.DRAFT,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    jobs: Mapped[list[ScoreJob]] = relationship(back_populates="document", cascade="all, delete-orphan")
    claims: Mapped[list[Claim]] = relationship(back_populates="document", cascade="all, delete-orphan")


class ScoreJob(Base):
    """An asynchronous scoring run for a document."""

    __tablename__ = "score_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    profile_name: Mapped[str] = mapped_column(String(64))
    profile_version: Mapped[str] = mapped_column(String(32), default="1")
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum", native_enum=False, length=32),
        default=JobStatus.QUEUED,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="jobs")
    results: Mapped[list[ScoreResult]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )


class ScoreResult(Base):
    """One dimension score produced by a scorer for a job."""

    __tablename__ = "score_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("score_jobs.id", ondelete="CASCADE"),
        index=True,
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    score_name: Mapped[str] = mapped_column(String(64), index=True)
    score_value: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    summary: Mapped[str] = mapped_column(Text, default="")
    rationale_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    model_name: Mapped[str] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped[ScoreJob] = relationship(back_populates="results")
    spans: Mapped[list[ScoreSpan]] = relationship(
        back_populates="score_result",
        cascade="all, delete-orphan",
    )


class ScoreSpan(Base):
    """Issue or evidence span attached to a score result."""

    __tablename__ = "score_spans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    score_result_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("score_results.id", ondelete="CASCADE"),
        index=True,
    )
    quoted_span: Mapped[str] = mapped_column(Text, default="")
    issue_type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text, default="")
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    score_result: Mapped[ScoreResult] = relationship(back_populates="spans")


class Claim(Base):
    """Extracted claim for traceability (optional enrichment)."""

    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    claim_text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str] = mapped_column(String(64), default="factual")
    source_chunk: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_form: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="claims")
