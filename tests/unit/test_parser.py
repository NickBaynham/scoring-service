"""Unit tests for LLM JSON parsing."""

import pytest
from app.core.exceptions import LLMError
from app.llm.parser import parse_json_content, parse_model_payload
from app.llm.schemas import DimensionScorePayload


@pytest.mark.unit
def test_parse_json_strips_fence() -> None:
    raw = '```json\n{"score": 0.5, "confidence": 0.6, "issues": [], "summary": "x"}\n```'
    data = parse_json_content(raw)
    assert data["score"] == 0.5


@pytest.mark.unit
def test_parse_model_payload_ok() -> None:
    raw = '{"score": 0.5, "confidence": 0.6, "issues": [], "summary": "ok"}'
    p = parse_model_payload(DimensionScorePayload, raw)
    assert p.score == 0.5


@pytest.mark.unit
def test_parse_model_invalid() -> None:
    with pytest.raises(LLMError):
        parse_model_payload(DimensionScorePayload, "not json")
