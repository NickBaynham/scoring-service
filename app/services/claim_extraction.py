"""Extract claims from document text using the LLM."""

import logging
import uuid

from app.core.exceptions import LLMError
from app.db.models import Claim
from app.llm.client import OpenAICompatibleClient
from app.llm.parser import parse_model_payload
from app.llm.prompts import claim_extraction_prompt, system_prompt_for_json_only
from app.llm.schemas import ClaimExtractionPayload

logger = logging.getLogger(__name__)


async def extract_claims_to_models(
    *,
    document_id: str,
    document_text: str,
    client: OpenAICompatibleClient,
    correlation_id: str | None = None,
) -> list[Claim]:
    """Return ORM Claim rows from extracted claims."""
    raw = await client.chat_completion_json(
        system=system_prompt_for_json_only(),
        user=claim_extraction_prompt(document_text),
        correlation_id=correlation_id,
    )
    try:
        payload = parse_model_payload(ClaimExtractionPayload, raw)
    except LLMError:
        logger.exception("claim extraction parse failed")
        return []
    claims: list[Claim] = []
    for item in payload.claims:
        claims.append(
            Claim(
                id=str(uuid.uuid4()),
                document_id=document_id,
                claim_text=item.claim_text,
                claim_type=item.claim_type,
                source_chunk=item.source_chunk,
                normalized_form=item.normalized_form,
            )
        )
    return claims
