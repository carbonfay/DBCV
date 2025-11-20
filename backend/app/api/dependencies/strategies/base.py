from sqlalchemy.ext.asyncio import AsyncSession
from abc import ABC, abstractmethod
from uuid import UUID


class BaseAuthStrategy(ABC):
    @abstractmethod
    async def authorize(self, session: AsyncSession, entity_id: UUID, token_data: dict) -> dict:
        pass
