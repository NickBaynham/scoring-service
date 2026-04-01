"""Pydantic schemas for structured LLM outputs."""

from pydantic import BaseModel, Field, field_validator


class LLMIssue(BaseModel):
    """Issue item returned by dimension scorers."""

    type: str = Field(default="general", description="Issue category")
    severity: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str = ""
    quoted_span: str = ""


class DimensionScorePayload(BaseModel):
    """JSON object expected from each dimension prompt."""

    score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    issues: list[LLMIssue] = Field(default_factory=list)
    summary: str = ""

    @field_validator("issues", mode="before")
    @classmethod
    def default_issues(cls, v: object) -> object:
        if v is None:
            return []
        return v


class ClaimItem(BaseModel):
    """Single extracted claim."""

    claim_text: str
    claim_type: str = "factual"
    source_chunk: str | None = None
    normalized_form: str | None = None


class ClaimExtractionPayload(BaseModel):
    """Structured output for claim extraction."""

    claims: list[ClaimItem] = Field(default_factory=list)
