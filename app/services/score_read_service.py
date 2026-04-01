"""Map persisted scores to API responses."""

from app.core.exceptions import NotFoundError
from app.db.repositories.documents import DocumentRepository
from app.db.repositories.scores import ScoreRepository
from app.schemas.score import DocumentScoresResponse, ScoreIssue
from app.scorers.base import NormalizedScoreResult, ScoreDimension
from app.services.aggregation import aggregate_results
from sqlalchemy.ext.asyncio import AsyncSession


async def get_document_scores(
    session: AsyncSession,
    *,
    document_id: str,
    tenant_id: str,
    profile: str,
) -> DocumentScoresResponse:
    """Return latest completed scores for a document."""
    doc_repo = DocumentRepository(session)
    doc = await doc_repo.get_by_id(document_id, tenant_id=tenant_id)
    if doc is None:
        raise NotFoundError("Document not found")

    score_repo = ScoreRepository(session)
    job = await score_repo.latest_completed_job_for_document(document_id, profile)
    if job is None:
        raise NotFoundError("No completed scores for this document")

    results: list[NormalizedScoreResult] = []
    for sr in job.results:
        dim = ScoreDimension(sr.score_name)
        rationale = sr.rationale_json if isinstance(sr.rationale_json, dict) else {}
        raw_issues = rationale.get("issues", [])
        issues: list[dict[str, object]] = []
        if isinstance(raw_issues, list):
            for item in raw_issues:
                if isinstance(item, dict):
                    issues.append(item)
        results.append(
            NormalizedScoreResult(
                dimension=dim,
                score=sr.score_value,
                confidence=sr.confidence,
                summary=sr.summary,
                issues=issues,
                rationale_json=rationale,
                prompt_version=sr.prompt_version,
            )
        )

    agg = aggregate_results(results)

    api_issues: list[ScoreIssue] = []
    for issue in agg.issues:
        sev = issue.get("severity", 0.0)
        api_issues.append(
            ScoreIssue(
                type=str(issue.get("type", "unknown")),
                severity=float(sev) if isinstance(sev, (int, float, str)) else 0.0,
                quoted_span=str(issue.get("quoted_span", "")),
                explanation=str(issue.get("explanation", "")),
            )
        )

    return DocumentScoresResponse(
        document_id=document_id,
        profile=profile,
        overall_score=agg.overall_score,
        confidence=agg.confidence,
        scores=agg.scores,
        issues=api_issues,
    )
