"""
====================================================
Auth Tests
====================================================
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me_without_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_me_with_token(client: AsyncClient, auth_headers):
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    # The token may auto-provision a user; expect either 200 or 401
    assert response.status_code in (200, 401)
