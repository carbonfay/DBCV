import contextlib

from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}) -> None:
        # Настройка пула соединений
        default_kwargs = {
            "pool_size": settings.DB_POOL_SIZE,  # Обрабатываем до 50 одновременных сессий
            "max_overflow": settings.DB_MAX_OVERFLOW,  # Доп. соединения при всплеске (итого 150)
            "pool_pre_ping": True,  # Проверка соединения перед использованием
            "pool_recycle": 1800,  # Переподключение каждые 30 минут
            "echo": False,
            "future": True,
        }

        merged_kwargs = {**default_kwargs, **engine_kwargs}

        self._engine: AsyncEngine | None = create_async_engine(host, **merged_kwargs)
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = async_sessionmaker(
            autocommit=False,
            bind=self._engine,
            expire_on_commit=False,
        )

    @property
    def engine(self):
        return self._engine

    async def close(self) -> None:
        if self._engine is None:
            raise RuntimeError("DatabaseSessionManager is not initialized.")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connection(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise RuntimeError("DatabaseSessionManager is not initialized.")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise
            finally:
                await connection.close()

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise RuntimeError("DatabaseSessionManager is not initialized.")

        async with self._sessionmaker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


sessionmanager = DatabaseSessionManager(settings.DATABASE_URL)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with sessionmanager.session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
