from .base import BaseAuthStrategy
from fastapi import WebSocketException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import uuid
from app.crud.channel import get_channel
from app.api.dependencies.auth import get_any_user


class ChannelAuthStrategy(BaseAuthStrategy):
    async def authorize(self, session: AsyncSession, entity_id: UUID, token_data: dict) -> dict:
        channel = await get_channel(session, entity_id)
        if channel is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Канал не найден")

        user = await get_any_user(session, token_data.sub)
        if user is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Пользователь не найден")

        if not channel.is_public and user not in channel.subscribers:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Нет доступа к каналу")

        connection_uuid = uuid.uuid4()
        return {"user": {"id": user.id, "connection_uuid": connection_uuid}, "entity": {"id": channel.id}}