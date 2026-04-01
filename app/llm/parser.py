"""Validate and parse model JSON responses."""

import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.core.exceptions import LLMError

T = TypeVar("T", bound=BaseModel)


def parse_json_content(raw: str) -> dict[str, object]:
    """Parse JSON from model output, tolerating fenced code blocks."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError(f"Invalid JSON from model: {e}") from e
    if not isinstance(data, dict):
        raise LLMError("Model JSON root must be an object")
    return data


def parse_model_payload(model_cls: type[T], raw: str) -> T:
    """Parse and validate `raw` JSON string into `model_cls`."""
    try:
        data = parse_json_content(raw)
        return model_cls.model_validate(data)
    except ValidationError as e:
        raise LLMError(f"Schema validation failed: {e}") from e
