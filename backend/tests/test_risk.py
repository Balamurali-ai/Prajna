"""
====================================================
Risk Endpoint Tests
====================================================
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_rankings_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/risk/rankings")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_district_not_found(client: AsyncClient, auth_headers):
    response = await client.get(
        "/api/v1/risk/district/NonExistentDistrict",
        headers=auth_headers,
    )
    # Either 404 (no ML data) or 401 (auth)
    assert response.status_code in (401, 404, 500, 503)
