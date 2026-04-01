"""Prompt builders for claim extraction and dimension scorers."""

from app.scorers.base import ScoreDimension

_BASE_RULES = """
Rules:
- Only score the assigned dimension. Do not comment on other dimensions.
- Use ONLY the provided document text. Do not invent facts or external knowledge.
- If uncertain, lower the confidence score (the separate "confidence" field).
- Quote exact spans from the text where possible in "quoted_span".
- Respond with a single JSON object only, no markdown, no prose outside JSON.
- Score must be between 0 and 1 inclusive. Confidence must be between 0 and 1 inclusive.
"""


def claim_extraction_prompt(document_text: str) -> str:
    """Prompt for extracting atomic claims."""
    return f"""You extract factual and interpretive claims from a document for downstream review.
Return JSON with this exact shape:
{{"claims": [{{"claim_text": "...", "claim_type": "factual|interpretive|opinion",
  "source_chunk": "...", "normalized_form": "..."}}]}}
Rules:
- Use ONLY the provided text.
- Do not invent content.
- Keep claims short and self-contained.
Document:
---
{document_text}
---
"""


def dimension_prompt(dimension: ScoreDimension, document_text: str) -> str:
    """Build a scorer-specific user prompt."""
    dim_instructions: dict[ScoreDimension, str] = {
        ScoreDimension.LOGICAL_SOUNDNESS: (
            "Evaluate logical structure: premises, conclusions, and whether conclusions follow."
        ),
        ScoreDimension.CLAIM_VERIFIABILITY: (
            "Evaluate whether stated claims could be checked against evidence or sources."
        ),
        ScoreDimension.EVIDENCE_SUPPORT: (
            "Evaluate how well key assertions are supported by reasoning or citations in the text."
        ),
        ScoreDimension.INTERNAL_CONSISTENCY: (
            "Evaluate whether the text contradicts itself or uses inconsistent terms for the same idea."
        ),
        ScoreDimension.HALLUCINATION_RISK: (
            "Estimate risk of fabricated or ungrounded specifics (higher score = higher risk)."
        ),
    }
    instruction = dim_instructions[dimension]
    return f"""{instruction}
Return JSON with this exact shape:
{{"score": 0.0, "confidence": 0.0, "issues": [
  {{"type": "...", "severity": 0.0, "explanation": "", "quoted_span": ""}}], "summary": ""}}
{_BASE_RULES}
Document:
---
{document_text}
---
"""


def system_prompt_for_json_only() -> str:
    """Short system message reinforcing JSON-only output."""
    return (
        "You are an expert document analyst for VerifiedSignal. "
        "Always respond with valid JSON only as specified in the user message."
    )
