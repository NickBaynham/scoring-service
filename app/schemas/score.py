"""Aggregated score API schemas."""

from pydantic import BaseModel, Field


class ScoreIssue(BaseModel):
    """A concrete issue surfaced by a scorer."""

    type: str = Field(..., examples=["unsupported_claim"])
    severity: float = Field(..., ge=0.0, le=1.0)
    quoted_span: str = Field(default="", examples=["The platform is used by 80% of firms."])
    explanation: str = Field(
        default="",
        examples=["Specific quantitative claim lacks supporting evidence."],
    )


class DocumentScoresResponse(BaseModel):
    """Latest credibility profile for a document."""

    document_id: str
    profile: str
    overall_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    scores: dict[str, float]
    issues: list[ScoreIssue]
