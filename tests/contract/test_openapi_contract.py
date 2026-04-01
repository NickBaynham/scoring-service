"""Contract tests for OpenAPI schema and documented paths."""

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.contract
async def test_openapi_includes_core_paths() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    paths = schema.get("paths", {})
    assert "/health" in paths
    assert "/v1/score-jobs" in paths
    assert "/v1/documents/{document_id}/scores" in paths


@pytest.mark.contract
async def test_error_schema_present() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/openapi.json")
    schema = r.json()
    assert "components" in schema
    schemas = schema["components"].get("schemas", {})
    assert any("Error" in k for k in schemas)
