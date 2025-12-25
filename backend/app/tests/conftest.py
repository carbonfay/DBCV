from typing import AsyncIterable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from app.config import settings
from app.models.base import BaseModel
from app.database import get_db_session
from app.main import app
from app.tests.utils import authentication_token_from_email, get_superuser_token_headers
from app.initial_data import init_db


@pytest.fixture(scope="session")
def anyio_backend():
    # Используем asyncio backend для совместимости anyio-маркировок
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def engine() -> AsyncIterable[AsyncEngine]:
    from sqlalchemy.pool import NullPool
    try:
        import testing.postgresql

        postgresql = testing.postgresql.Postgresql()
        try:
            _engine = create_async_engine(
                postgresql.url().replace("postgresql://", "postgresql+asyncpg://"),
                poolclass=NullPool,
            )
            async with _engine.begin() as conn:
                await conn.run_sync(BaseModel.metadata.create_all)
            yield _engine
        finally:
            try:
                await _engine.dispose()
            except Exception:
                pass
            try:
                postgresql.stop()
            except Exception:
                if postgresql.child_process and postgresql.child_process.poll() is None:
                    postgresql.child_process.kill()
                postgresql.child_process = None
                postgresql.cleanup()
        return
    except Exception:
        import pytest
        pytest.skip("PostgreSQL (initdb) недоступен, пропускаем тесты, зависящие от БД", allow_module_level=True)


@pytest.fixture(scope="function")
async def session(engine: AsyncEngine) -> AsyncIterable[AsyncSession]:
    """Create a new database session with a rollback at the end of the test.

    Inspired by https://dev.to/jbrocher/fastapi-testing-a-database-5ao5
    """
    connection: AsyncConnection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection)
    yield session
    await transaction.rollback()
    await connection.close()


@pytest.fixture(scope="function")
async def client(session: AsyncSession) -> AsyncIterable[AsyncClient]:
    """Create a test client that uses the override_get_db fixture to return
    a session.
    """
    app.dependency_overrides[get_db_session] = lambda: session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as test_client:
        yield test_client


@pytest.fixture(scope="function")
async def superuser_token_headers(
    client: AsyncClient, session: AsyncSession
) -> dict[str, str]:
    return await get_superuser_token_headers(client, session)


@pytest.fixture(scope="function")
async def normal_user_token_headers(
    client: AsyncClient, session: AsyncSession
) -> dict[str, str]:
    return await authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, session=session
    )
