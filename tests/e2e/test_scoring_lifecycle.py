"""End-to-end scoring lifecycle with mocked LLM HTTP."""

import pytest
import respx
from app.workers.scoring_worker import process_once
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def _llm_json(content: str) -> dict[str, object]:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                }
            }
        ]
    }


@pytest.mark.e2e
@respx.mock
async def test_submit_job_and_fetch_scores(
    client: AsyncClient,
    engine: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_BASE_URL", "https://llm.test/v1")
    from app.core.config import clear_settings_cache

    clear_settings_cache()

    call_count = {"n": 0}

    def chat_response(request: object) -> Response:
        call_count["n"] += 1
        body = '{"claims":[]}' if call_count["n"] == 1 else '{"score":0.8,"confidence":0.7,"issues":[],"summary":"ok"}'
        return Response(200, json=_llm_json(body))

    respx.post("https://llm.test/v1/chat/completions").mock(side_effect=chat_response)

    doc_resp = await client.post(
        "/v1/documents",
        json={
            "tenant_id": "tenant_1",
            "raw_text": "We grew 50% last year with strong fundamentals.",
            "profile": "credibility_v1",
        },
    )
    assert doc_resp.status_code == 201
    document_id = doc_resp.json()["id"]

    job_resp = await client.post(
        "/v1/score-jobs",
        json={
            "document_id": document_id,
            "tenant_id": "tenant_1",
            "profile": "credibility_v1",
        },
    )
    assert job_resp.status_code == 202
    job_id = job_resp.json()["job_id"]

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await process_once(factory, job_id)

    scores = await client.get(
        f"/v1/documents/{document_id}/scores",
        params={"tenant_id": "tenant_1", "profile": "credibility_v1"},
    )
    assert scores.status_code == 200
    data = scores.json()
    assert data["document_id"] == document_id
    assert "overall_score" in data
    assert len(data["scores"]) == 5
