from typing import Union
from uuid import UUID
from pydantic import BaseModel
from .base import WebSocketManagerBase


class ChannelWebSocketManager(WebSocketManagerBase):
    async def notify_channel(self, channel_id: Union[UUID, str], message: BaseModel | str) -> None:
        await self.notify(channel_id, message)