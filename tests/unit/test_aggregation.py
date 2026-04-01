"""Unit tests for credibility aggregation."""

import pytest
from app.scorers.base import NormalizedScoreResult, ScoreDimension
from app.services.aggregation import WEIGHTS, aggregate_results


@pytest.mark.unit
def test_aggregate_formula() -> None:
    results = [
        NormalizedScoreResult(
            dimension=ScoreDimension.LOGICAL_SOUNDNESS,
            score=1.0,
            confidence=0.8,
            summary="",
            issues=[],
            rationale_json={},
            prompt_version="v1",
        ),
        NormalizedScoreResult(
            dimension=ScoreDimension.CLAIM_VERIFIABILITY,
            score=1.0,
            confidence=0.8,
            summary="",
            issues=[],
            rationale_json={},
            prompt_version="v1",
        ),
        NormalizedScoreResult(
            dimension=ScoreDimension.EVIDENCE_SUPPORT,
            score=1.0,
            confidence=0.8,
            summary="",
            issues=[],
            rationale_json={},
            prompt_version="v1",
        ),
        NormalizedScoreResult(
            dimension=ScoreDimension.INTERNAL_CONSISTENCY,
            score=1.0,
            confidence=0.8,
            summary="",
            issues=[],
            rationale_json={},
            prompt_version="v1",
        ),
        NormalizedScoreResult(
            dimension=ScoreDimension.HALLUCINATION_RISK,
            score=0.0,
            confidence=0.8,
            summary="",
            issues=[],
            rationale_json={},
            prompt_version="v1",
        ),
    ]
    agg = aggregate_results(results)
    expected = (
        WEIGHTS[ScoreDimension.LOGICAL_SOUNDNESS]
        + WEIGHTS[ScoreDimension.CLAIM_VERIFIABILITY]
        + WEIGHTS[ScoreDimension.EVIDENCE_SUPPORT]
        + WEIGHTS[ScoreDimension.INTERNAL_CONSISTENCY]
        + WEIGHTS[ScoreDimension.HALLUCINATION_RISK] * 1.0
    )
    assert abs(agg.overall_score - expected) < 1e-9
    assert agg.confidence == pytest.approx(0.8)


@pytest.mark.unit
def test_hallucination_inverted_weight() -> None:
    """High hallucination risk should lower overall when other dimensions are fixed."""
    base = 0.7
    low_risk = [
        _dim(ScoreDimension.LOGICAL_SOUNDNESS, base),
        _dim(ScoreDimension.CLAIM_VERIFIABILITY, base),
        _dim(ScoreDimension.EVIDENCE_SUPPORT, base),
        _dim(ScoreDimension.INTERNAL_CONSISTENCY, base),
        _dim(ScoreDimension.HALLUCINATION_RISK, 0.1),
    ]
    high_risk = [
        _dim(ScoreDimension.LOGICAL_SOUNDNESS, base),
        _dim(ScoreDimension.CLAIM_VERIFIABILITY, base),
        _dim(ScoreDimension.EVIDENCE_SUPPORT, base),
        _dim(ScoreDimension.INTERNAL_CONSISTENCY, base),
        _dim(ScoreDimension.HALLUCINATION_RISK, 0.9),
    ]
    assert aggregate_results(low_risk).overall_score > aggregate_results(high_risk).overall_score


def _dim(dimension: ScoreDimension, score: float) -> NormalizedScoreResult:
    return NormalizedScoreResult(
        dimension=dimension,
        score=score,
        confidence=0.5,
        summary="",
        issues=[],
        rationale_json={},
        prompt_version="v1",
    )
