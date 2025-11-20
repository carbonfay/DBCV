from .base import BaseAuthStrategy
from fastapi import WebSocketException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import uuid
from app.crud.bot import get_bot
from app.api.dependencies.auth import get_any_user
from app.api.dependencies.auth import BotAccessChecker, AccessType


class BotAuthStrategy(BaseAuthStrategy):
    async def authorize(self, session: AsyncSession, entity_id: UUID, token_data: dict) -> dict:
        bot = await get_bot(session, entity_id)
        if bot is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Бот не найден")

        user = await get_any_user(session, token_data.sub)
        if user is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Пользователь не найден")

        try:
            await BotAccessChecker._has_access_or_higher(session, bot.id, user, AccessType.VIEWER)
        except Exception:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Нет доступа к боту")

        connection_uuid = uuid.uuid4()
        return {"user": {"id": user.id, "connection_uuid": connection_uuid}, "entity": {"id": bot.id}}