import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.initial_data import init_db


@pytest.mark.anyio
async def test_get_access_token(client: AsyncClient, session: AsyncSession) -> None:
    await init_db(session)
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]


@pytest.mark.anyio
async def test_get_access_token_incorrect_password(client: AsyncClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400