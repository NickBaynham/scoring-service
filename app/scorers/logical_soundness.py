"""Logical soundness dimension scorer."""

import logging

from app.llm.parser import parse_model_payload
from app.llm.prompts import dimension_prompt, system_prompt_for_json_only
from app.llm.schemas import DimensionScorePayload
from app.scorers.base import BaseScorer, NormalizedScoreResult, ScoreDimension

logger = logging.getLogger(__name__)


class LogicalSoundnessScorer(BaseScorer):
    """Evaluates argument structure and validity."""

    @property
    def dimension(self) -> ScoreDimension:
        return ScoreDimension.LOGICAL_SOUNDNESS

    async def score(self, document_text: str, *, correlation_id: str | None = None) -> NormalizedScoreResult:
        user = dimension_prompt(ScoreDimension.LOGICAL_SOUNDNESS, document_text)
        raw = await self._client.chat_completion_json(
            system=system_prompt_for_json_only(),
            user=user,
            correlation_id=correlation_id,
        )
        payload = parse_model_payload(DimensionScorePayload, raw)
        issues = [i.model_dump() for i in payload.issues]
        rationale = payload.model_dump()
        logger.info(
            "logical_soundness scored",
            extra={"correlation_id": correlation_id, "score": payload.score},
        )
        return NormalizedScoreResult(
            dimension=self.dimension,
            score=payload.score,
            confidence=payload.confidence,
            summary=payload.summary,
            issues=issues,
            rationale_json=rationale,
            prompt_version=self.prompt_version,
        )
