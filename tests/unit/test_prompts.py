"""Unit tests for prompt builders."""

import pytest
from app.llm.prompts import claim_extraction_prompt, dimension_prompt
from app.scorers.base import ScoreDimension


@pytest.mark.unit
def test_dimension_prompt_contains_rules() -> None:
    text = "Hello world."
    p = dimension_prompt(ScoreDimension.LOGICAL_SOUNDNESS, text)
    assert "logical" in p.lower() or "structure" in p.lower()
    assert "only score the assigned dimension" in p.lower()
    assert text in p


@pytest.mark.unit
def test_claim_prompt_includes_document() -> None:
    text = "Claim A."
    p = claim_extraction_prompt(text)
    assert text in p
    assert "claims" in p.lower()
