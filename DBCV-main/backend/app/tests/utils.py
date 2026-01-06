import random
import string

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crud import user as crud_user
from app.initial_data import init_db
from app.models.user import UserModel
from app.schemas.user import UserCreate


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


async def user_authentication_headers(
    client: AsyncClient, email: str, password: str
) -> dict[str, str]:
    data = {"username": email, "password": password}

    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


async def get_superuser_token_headers(
    client: AsyncClient, session: AsyncSession
) -> dict[str, str]:
    await init_db(session)
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


async def create_random_user(session: AsyncSession) -> UserModel:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        username=email, email=email, password=password, first_name="", last_name=""
    )
    user = await crud_user.create_user(session=session, user_in=user_in)
    await session.commit()
    await session.refresh(user)
    return user


async def authentication_token_from_email(
    client: AsyncClient, email: str, session: AsyncSession
) -> dict[str, str]:
    """Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    password = random_lower_string()
    user = await crud_user.get_user_by_email(session=session, email=email)
    if user:
        await crud_user.delete_user(session, user.id)
    user_in_create = UserCreate(
        username=email, email=email, password=password, first_name="", last_name=""
    )
    user = await crud_user.create_user(session=session, user_in=user_in_create)
    await session.commit()
    await session.refresh(user)
    return await user_authentication_headers(
        client=client, email=email, password=password
    )