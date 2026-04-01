"""Base scorer interface."""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.llm.client import OpenAICompatibleClient


class ScoreDimension(enum.StrEnum):
    """Named scoring dimensions in the credibility profile."""

    LOGICAL_SOUNDNESS = "logical_soundness"
    CLAIM_VERIFIABILITY = "claim_verifiability"
    EVIDENCE_SUPPORT = "evidence_support"
    INTERNAL_CONSISTENCY = "internal_consistency"
    HALLUCINATION_RISK = "hallucination_risk"


@dataclass(frozen=True)
class NormalizedScoreResult:
    """Validated output from a single scorer run."""

    dimension: ScoreDimension
    score: float
    confidence: float
    summary: str
    issues: list[dict[str, object]]
    rationale_json: dict[str, object]
    prompt_version: str


class BaseScorer(ABC):
    """Shared interface for LLM-backed scorers."""

    prompt_version: str = "v1"

    def __init__(self, client: OpenAICompatibleClient) -> None:
        self._client = client

    @property
    @abstractmethod
    def dimension(self) -> ScoreDimension:
        """Which dimension this scorer evaluates."""

    @abstractmethod
    async def score(self, document_text: str, *, correlation_id: str | None = None) -> NormalizedScoreResult:
        """Run the scorer against document text."""
