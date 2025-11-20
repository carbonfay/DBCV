from typing import Union
from uuid import UUID
from pydantic import BaseModel
from .base import WebSocketManagerBase


class BotWebSocketManager(WebSocketManagerBase):
    async def notify_bot(self, bot_id: Union[UUID, str], message: BaseModel | str) -> None:
        await self.notify(bot_id, message)
