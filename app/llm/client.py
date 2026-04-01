"""Async OpenAI-compatible HTTP client with retries and structured JSON."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
import orjson

from app.core.config import Settings, get_settings
from app.core.exceptions import LLMError

logger = logging.getLogger(__name__)


class OpenAICompatibleClient:
    """Minimal chat-completions client for OpenAI-compatible servers."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = httpx.AsyncClient(
            base_url=self._settings.openai_base_url.rstrip("/"),
            timeout=httpx.Timeout(self._settings.llm_timeout_seconds),
            headers={"Authorization": f"Bearer {self._settings.openai_api_key}"},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def chat_completion_json(
        self,
        *,
        system: str,
        user: str,
        correlation_id: str | None = None,
    ) -> str:
        """Return assistant message content as string (expected JSON)."""
        payload: dict[str, Any] = {
            "model": self._settings.model_name,
            "temperature": self._settings.llm_temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
        }
        extra: dict[str, str] = {}
        if correlation_id:
            extra["X-Correlation-ID"] = correlation_id
        last_exc: Exception | None = None
        for attempt in range(1, self._settings.llm_max_retries + 1):
            try:
                resp = await self._client.post(
                    "/chat/completions",
                    content=orjson.dumps(payload),
                    headers={"Content-Type": "application/json", **extra},
                )
                resp.raise_for_status()
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not isinstance(content, str) or not content.strip():
                    raise LLMError("Empty completion content")
                logger.debug(
                    "LLM completion ok",
                    extra={"correlation_id": correlation_id, "attempt": attempt},
                )
                return content
            except (httpx.HTTPError, LLMError) as e:
                last_exc = e
                logger.warning(
                    "LLM request failed attempt %s: %s",
                    attempt,
                    e,
                    extra={"correlation_id": correlation_id},
                )
                if attempt < self._settings.llm_max_retries:
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
        assert last_exc is not None
        raise LLMError(f"LLM request failed after retries: {last_exc}") from last_exc
