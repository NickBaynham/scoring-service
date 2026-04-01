"""Integration tests for root URL and documentation entrypoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_root_redirects_to_swagger_ui(client: AsyncClient) -> None:
    r = await client.get("/", follow_redirects=False)
    assert r.status_code in (301, 302, 303, 307, 308)
    assert r.headers.get("location") == "/docs"


@pytest.mark.integration
async def test_openapi_json_available(client: AsyncClient) -> None:
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    data = r.json()
    assert data.get("openapi") is not None
    assert data.get("info", {}).get("title") == "VerifiedSignal Scoring Service"
