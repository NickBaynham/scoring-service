"""Aggregate dimension scores into an overall credibility profile."""

from dataclasses import dataclass

from app.scorers.base import NormalizedScoreResult, ScoreDimension


@dataclass(frozen=True)
class AggregatedProfile:
    """Combined view after weighting and issue merge."""

    overall_score: float
    confidence: float
    scores: dict[str, float]
    issues: list[dict[str, object]]


WEIGHTS: dict[ScoreDimension, float] = {
    ScoreDimension.LOGICAL_SOUNDNESS: 0.25,
    ScoreDimension.CLAIM_VERIFIABILITY: 0.20,
    ScoreDimension.EVIDENCE_SUPPORT: 0.20,
    ScoreDimension.INTERNAL_CONSISTENCY: 0.20,
    ScoreDimension.HALLUCINATION_RISK: 0.15,
}


def aggregate_results(results: list[NormalizedScoreResult]) -> AggregatedProfile:
    """Combine per-dimension outputs using the credibility_v1 formula."""
    by_dim = {r.dimension: r for r in results}
    if set(by_dim.keys()) != set(WEIGHTS.keys()):
        missing = set(WEIGHTS.keys()) - set(by_dim.keys())
        raise ValueError(f"Missing dimensions: {missing}")

    ls = by_dim[ScoreDimension.LOGICAL_SOUNDNESS].score
    cv = by_dim[ScoreDimension.CLAIM_VERIFIABILITY].score
    es = by_dim[ScoreDimension.EVIDENCE_SUPPORT].score
    ic = by_dim[ScoreDimension.INTERNAL_CONSISTENCY].score
    hr = by_dim[ScoreDimension.HALLUCINATION_RISK].score

    overall = (
        WEIGHTS[ScoreDimension.LOGICAL_SOUNDNESS] * ls
        + WEIGHTS[ScoreDimension.CLAIM_VERIFIABILITY] * cv
        + WEIGHTS[ScoreDimension.EVIDENCE_SUPPORT] * es
        + WEIGHTS[ScoreDimension.INTERNAL_CONSISTENCY] * ic
        + WEIGHTS[ScoreDimension.HALLUCINATION_RISK] * (1.0 - hr)
    )

    confidences = [r.confidence for r in results]
    confidence = sum(confidences) / len(confidences) if confidences else 0.0

    scores_map = {r.dimension.value: r.score for r in results}

    issues: list[dict[str, object]] = []
    for r in results:
        for issue in r.issues:
            issues.append(
                {
                    **issue,
                    "dimension": r.dimension.value,
                }
            )

    return AggregatedProfile(
        overall_score=max(0.0, min(1.0, overall)),
        confidence=max(0.0, min(1.0, confidence)),
        scores=scores_map,
        issues=issues,
    )
