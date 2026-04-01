"""Integration tests for health endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_health_ok(client: AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "scoring-service"
