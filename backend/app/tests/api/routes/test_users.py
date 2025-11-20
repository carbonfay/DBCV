import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.tests.utils import create_random_user


@pytest.mark.anyio
async def test_get_existing_user(
    client: AsyncClient, superuser_token_headers: dict[str, str], session: AsyncSession
) -> None:
    user = await create_random_user(session)
    user_id = user.id
    r = await client.get(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
    )
    assert 200 <= r.status_code < 300
    response_user = r.json()
    assert user.email == response_user["email"]


@pytest.mark.anyio
async def test_get_existing_user_permissions_error(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = await client.get(
        f"{settings.API_V1_STR}/users/999999",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "The user doesn't have enough privileges."}


@pytest.mark.anyio
async def test_get_user_not_found(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    r = await client.get(
        f"{settings.API_V1_STR}/users/999999",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404
    assert r.json() == {"detail": "User not found."}


@pytest.mark.anyio
async def test_get_users(
    client: AsyncClient, superuser_token_headers: dict[str, str], session: AsyncSession
) -> None:
    users = [await create_random_user(session) for _ in range(5)]
    r = await client.get(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
    )
    assert 200 <= r.status_code < 300
    assert len(users) + 1 == len(r.json())


@pytest.mark.anyio
async def test_create_user(
    client: AsyncClient, superuser_token_headers: dict[str, str], session: AsyncSession
) -> None:
    data = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "password123",
    }
    r = await client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data
    )
    assert 200 <= r.status_code < 300
    response_user = r.json()
    assert response_user["email"] == data["email"]
    assert response_user["username"] == data["username"]
    assert "id" in response_user
    assert "password" not in response_user


@pytest.mark.anyio
async def test_create_user_duplicate_email(
    client: AsyncClient, superuser_token_headers: dict[str, str], session: AsyncSession
) -> None:
    user = await create_random_user(session)
    data = {"email": user.email, "username": "newuser", "password": "password123"}
    r = await client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data
    )
    assert r.status_code == 400
    assert r.json() == {
        "detail": "The user with the given email or username already exists."
    }


@pytest.mark.anyio
async def test_create_user_duplicate_username(
    client: AsyncClient, superuser_token_headers: dict[str, str], session: AsyncSession
) -> None:
    user = await create_random_user(session)
    data = {"email": "email", "username": user.username, "password": "password123"}
    r = await client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data
    )
    assert r.status_code == 400
    assert r.json() == {
        "detail": "The user with the given email or username already exists."
    }


@pytest.mark.anyio
async def test_update_user_me(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    data = {"username": "updatedusername"}
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers, json=data
    )
    assert 200 <= r.status_code < 300
    response_user = r.json()
    assert response_user["username"] == data["username"]


@pytest.mark.anyio
async def test_update_user_me_duplicate_username(
    client: AsyncClient,
    normal_user_token_headers: dict[str, str],
    session: AsyncSession,
) -> None:
    another_user = await create_random_user(session)
    data = {"username": another_user.username}
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers, json=data
    )
    assert r.status_code == 400
    assert r.json() == {
        "detail": "The user with the given email or username already exists."
    }