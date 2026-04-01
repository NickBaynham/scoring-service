"""End-to-end scoring pipeline: text → claims → scorers → persistence."""

from __future__ import annotations

import asyncio
import logging
import uuid

from app.core.config import Settings, get_settings
from app.core.exceptions import DomainValidationError, LLMError
from app.db.models import (
    DocumentStatus,
    ScoreJob,
    ScoreResult,
    ScoreSpan,
)
from app.db.repositories.claims import ClaimRepository
from app.db.repositories.documents import DocumentRepository
from app.db.repositories.jobs import JobRepository
from app.db.repositories.scores import ScoreRepository
from app.llm.client import OpenAICompatibleClient
from app.scorers.base import BaseScorer, NormalizedScoreResult
from app.scorers.claim_verifiability import ClaimVerifiabilityScorer
from app.scorers.evidence_support import EvidenceSupportScorer
from app.scorers.hallucination_risk import HallucinationRiskScorer
from app.scorers.internal_consistency import InternalConsistencyScorer
from app.scorers.logical_soundness import LogicalSoundnessScorer
from app.services.aggregation import aggregate_results
from app.services.claim_extraction import extract_claims_to_models
from app.services.document_service import resolve_document_text
from app.storage.s3_client import S3Storage
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def build_scorers(client: OpenAICompatibleClient) -> list[BaseScorer]:
    """Return all scorers for the credibility profile."""
    return [
        LogicalSoundnessScorer(client),
        ClaimVerifiabilityScorer(client),
        EvidenceSupportScorer(client),
        InternalConsistencyScorer(client),
        HallucinationRiskScorer(client),
    ]


async def persist_dimension_results(
    session: AsyncSession,
    *,
    job_id: str,
    document_id: str,
    results: list[NormalizedScoreResult],
    settings: Settings,
) -> None:
    """Write per-dimension rows and issue spans."""
    score_repo = ScoreRepository(session)
    for r in results:
        sr = ScoreResult(
            id=str(uuid.uuid4()),
            job_id=job_id,
            document_id=document_id,
            score_name=r.dimension.value,
            score_value=r.score,
            confidence=r.confidence,
            summary=r.summary,
            rationale_json=r.rationale_json,
            model_name=settings.model_name,
            prompt_version=r.prompt_version,
        )
        await score_repo.add_result(sr)
        for issue in r.issues:
            sev = issue.get("severity", 0.0)
            sev_f = float(sev) if isinstance(sev, (int, float, str)) else 0.0
            span = ScoreSpan(
                id=str(uuid.uuid4()),
                score_result_id=sr.id,
                quoted_span=str(issue.get("quoted_span", "")),
                issue_type=str(issue.get("type", "unknown")),
                severity=sev_f,
                explanation=str(issue.get("explanation", "")),
                start_offset=None,
                end_offset=None,
            )
            await score_repo.add_span(span)


async def run_scoring_pipeline(
    session: AsyncSession,
    job: ScoreJob,
    *,
    settings: Settings | None = None,
    llm_client: OpenAICompatibleClient | None = None,
    s3: S3Storage | None = None,
) -> None:
    """Execute scoring for a queued job."""
    settings = settings or get_settings()
    client = llm_client or OpenAICompatibleClient(settings)
    job_repo = JobRepository(session)
    doc_repo = DocumentRepository(session)
    claim_repo = ClaimRepository(session)

    try:
        doc = await doc_repo.get_by_id(job.document_id)
        if doc is None:
            await job_repo.mark_failed(job, "Document missing")
            return

        correlation_id = job.id

        try:
            text = await resolve_document_text(doc, s3=s3)
        except DomainValidationError as e:
            await job_repo.mark_failed(job, str(e))
            return

        try:
            claims = await extract_claims_to_models(
                document_id=doc.id,
                document_text=text,
                client=client,
                correlation_id=correlation_id,
            )
            if claims:
                await claim_repo.bulk_create(claims)

            scorers = build_scorers(client)
            tasks = [s.score(text, correlation_id=correlation_id) for s in scorers]
            normalized: list[NormalizedScoreResult] = list(
                await asyncio.gather(*tasks),
            )

            _ = aggregate_results(normalized)
            await persist_dimension_results(
                session,
                job_id=job.id,
                document_id=doc.id,
                results=normalized,
                settings=settings,
            )
            doc.status = DocumentStatus.SCORED
            await job_repo.mark_completed(job)
        except LLMError as e:
            logger.exception("LLM failure during scoring", extra={"job_id": job.id})
            await job_repo.mark_failed(job, str(e))
        except Exception as e:  # noqa: BLE001
            logger.exception("Unexpected scoring failure", extra={"job_id": job.id})
            await job_repo.mark_failed(job, str(e))
    finally:
        if llm_client is None:
            await client.aclose()
